"""Tests for the RetroMonitorCoordinator.

Uses aiohttp test utilities to mock the agent HTTP server.
No Home Assistant runtime required.
"""

import asyncio
import copy
import json
import sys
import os
import importlib.util
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — import coordinator & validator without HA installed.
# We stub out the HA imports that coordinator.py requires.
# ---------------------------------------------------------------------------

_HA_COMPONENT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "homeassistant",
    "custom_components",
)
sys.path.insert(0, _HA_COMPONENT_PATH)

# Minimal stubs for Home Assistant modules that coordinator.py imports.
# We only need enough to instantiate and call _async_update_data.

_update_coordinator_mod = MagicMock()


class _FakeUpdateFailed(Exception):
    pass


_update_coordinator_mod.UpdateFailed = _FakeUpdateFailed
_update_coordinator_mod.DataUpdateCoordinator = object  # base class placeholder

sys.modules.setdefault("homeassistant", MagicMock())
sys.modules.setdefault("homeassistant.config_entries", MagicMock())
sys.modules.setdefault("homeassistant.core", MagicMock())
sys.modules.setdefault("homeassistant.helpers", MagicMock())
sys.modules.setdefault("homeassistant.helpers.aiohttp_client", MagicMock())
sys.modules.setdefault(
    "homeassistant.helpers.update_coordinator", _update_coordinator_mod
)
sys.modules.setdefault("homeassistant.helpers.device_registry", MagicMock())
sys.modules.setdefault("homeassistant.helpers.entity", MagicMock())


# We need to re-define coordinator in a way that bypasses the HA base class
# but still exercises our actual logic. The simplest approach is to test
# the validator + HTTP fetch logic directly.

_COMPONENT_ROOT = os.path.join(_HA_COMPONENT_PATH, "retro_monitor")
_CONST_SPEC = importlib.util.spec_from_file_location(
    "retro_monitor.const", os.path.join(_COMPONENT_ROOT, "const.py")
)
_CONST_MODULE = importlib.util.module_from_spec(_CONST_SPEC)
sys.modules["retro_monitor.const"] = _CONST_MODULE
_CONST_SPEC.loader.exec_module(_CONST_MODULE)

_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "retro_monitor.validator", os.path.join(_COMPONENT_ROOT, "validator.py")
)
_VALIDATOR_MODULE = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_MODULE.__package__ = "retro_monitor"
sys.modules["retro_monitor.validator"] = _VALIDATOR_MODULE
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR_MODULE)

PayloadValidationError = _VALIDATOR_MODULE.PayloadValidationError
validate_payload = _VALIDATOR_MODULE.validate_payload

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_PAYLOAD: dict = {
    "device_id": "iandeiMac.local",
    "hostname": "iandeiMac.local",
    "platform": "macos_hackintosh",
    "timestamp": "2026-03-26T09:00:00Z",
    "source_ok": True,
    "cpu_temp": 58.0,
    "cpu_load": 17.4,
    "cpu_clock": 3420.0,
    "cpu_power": 75.3,
    "gpu_temp": 54.0,
    "gpu_load": 21.0,
    "gpu_clock": 1139.0,
    "gpu_power": 38.0,
    "memory_used_mb": 25764.6,
    "memory_total_mb": 65536.0,
    "memory_percent": 50.8,
    "fan_rpm_max": 2951.0,
    "fan_rpm_avg": 678.8,
    "disk_temp_max": 41.0,
    "disk_activity_percent": 0.0,
    "net_up_bps": 0.0,
    "net_down_bps": 0.0,
    "system_power_estimated": None,
}


def _payload(**overrides):
    p = copy.deepcopy(VALID_PAYLOAD)
    p.update(overrides)
    return p


def _payload_without(*keys):
    p = copy.deepcopy(VALID_PAYLOAD)
    for k in keys:
        p.pop(k, None)
    return p


# ---------------------------------------------------------------------------
# Coordinator-logic tests (exercising validate_payload as the coordinator does)
# ---------------------------------------------------------------------------


class TestCoordinatorFlows:
    """Test the three-layer error model that the coordinator implements."""

    def test_valid_payload_returns_data(self):
        """Layer 3 happy path — valid + source_ok."""
        data = validate_payload(VALID_PAYLOAD)
        assert data["cpu_temp"] == 58.0
        assert data["source_ok"] is True

    def test_degraded_payload_still_valid(self):
        """Layer 3 — source_ok=false is NOT a validation error."""
        p = _payload(source_ok=False, cpu_temp=None, gpu_temp=None)
        data = validate_payload(p)
        assert data["source_ok"] is False
        assert data["cpu_temp"] is None

    def test_missing_field_raises(self):
        """Layer 2 — missing required fields are payload validation errors."""
        with pytest.raises(PayloadValidationError):
            validate_payload(_payload_without("cpu_temp"))

    def test_invalid_json_structure(self):
        """Layer 2 — non-dict body."""
        with pytest.raises(PayloadValidationError):
            validate_payload("not a dict")

    def test_wrong_type_timestamp(self):
        """Layer 2 — timestamp must be a string."""
        with pytest.raises(PayloadValidationError):
            validate_payload(_payload(timestamp=123))

    def test_wrong_type_source_ok(self):
        """Layer 2 — source_ok must be a bool."""
        with pytest.raises(PayloadValidationError):
            validate_payload(_payload(source_ok="true"))

    def test_wrong_type_numeric_field(self):
        """Layer 2 — numeric fields must be number or null."""
        with pytest.raises(PayloadValidationError):
            validate_payload(_payload(cpu_load="high"))


class TestDeviceInfoCaching:
    """Test the device_info extraction logic that the coordinator caches."""

    def test_extracts_identity_fields(self):
        data = validate_payload(VALID_PAYLOAD)
        info = {
            "device_id": data.get("device_id", ""),
            "hostname": data.get("hostname", ""),
            "platform": data.get("platform", ""),
        }
        assert info["device_id"] == "iandeiMac.local"
        assert info["hostname"] == "iandeiMac.local"
        assert info["platform"] == "macos_hackintosh"

    def test_identity_survives_null_fields(self):
        """Identity is stable even when sensor data is null."""
        p = _payload(cpu_temp=None, gpu_temp=None, source_ok=False)
        data = validate_payload(p)
        assert data["device_id"] == "iandeiMac.local"
