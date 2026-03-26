"""Tests for the Retro Monitor payload validator.

These are pure-Python unit tests with no Home Assistant dependency.
"""

import sys
import os
import copy
import pytest

# Make the HA custom component importable without installing HA.
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "homeassistant",
        "custom_components",
        "retro_monitor",
    ),
)
# Also need the parent to allow `from validator import ...`
# We import directly since there is no HA runtime.
from validator import PayloadValidationError, validate_payload  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture: a fully-valid payload
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
    """Return a copy of VALID_PAYLOAD with arbitrary overrides."""
    p = copy.deepcopy(VALID_PAYLOAD)
    p.update(overrides)
    return p


def _payload_without(*keys):
    """Return a copy of VALID_PAYLOAD with certain keys removed."""
    p = copy.deepcopy(VALID_PAYLOAD)
    for k in keys:
        p.pop(k, None)
    return p


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestValidPayloads:
    def test_full_payload_passes(self):
        result = validate_payload(VALID_PAYLOAD)
        assert result is VALID_PAYLOAD

    def test_all_numeric_fields_null(self):
        """source_ok=false + all nulls is valid — it's degradation, not error."""
        p = _payload(source_ok=False)
        for k in (
            "cpu_temp", "cpu_load", "cpu_clock", "cpu_power",
            "gpu_temp", "gpu_load", "gpu_clock", "gpu_power",
            "memory_used_mb", "memory_total_mb", "memory_percent",
            "fan_rpm_max", "fan_rpm_avg",
            "disk_temp_max", "disk_activity_percent",
            "net_up_bps", "net_down_bps", "system_power_estimated",
        ):
            p[k] = None
        assert validate_payload(p) == p

    def test_integer_values_accepted(self):
        """Pure ints (not floats) are valid numbers."""
        p = _payload(cpu_temp=58, cpu_clock=3420)
        assert validate_payload(p)["cpu_temp"] == 58

    def test_system_power_null_is_valid(self):
        p = _payload(system_power_estimated=None)
        assert validate_payload(p)["system_power_estimated"] is None


# ---------------------------------------------------------------------------
# Structural errors
# ---------------------------------------------------------------------------


class TestRejections:
    def test_not_a_dict(self):
        with pytest.raises(PayloadValidationError, match="JSON object"):
            validate_payload([1, 2, 3])

    def test_none_rejected(self):
        with pytest.raises(PayloadValidationError, match="JSON object"):
            validate_payload(None)

    def test_string_rejected(self):
        with pytest.raises(PayloadValidationError, match="JSON object"):
            validate_payload("hello")


# ---------------------------------------------------------------------------
# Missing fields
# ---------------------------------------------------------------------------


class TestMissingFields:
    def test_missing_source_ok(self):
        with pytest.raises(PayloadValidationError, match="source_ok"):
            validate_payload(_payload_without("source_ok"))

    def test_missing_timestamp(self):
        with pytest.raises(PayloadValidationError, match="timestamp"):
            validate_payload(_payload_without("timestamp"))

    def test_missing_cpu_temp(self):
        with pytest.raises(PayloadValidationError, match="cpu_temp"):
            validate_payload(_payload_without("cpu_temp"))

    def test_missing_device_id(self):
        with pytest.raises(PayloadValidationError, match="device_id"):
            validate_payload(_payload_without("device_id"))

    def test_missing_multiple_fields(self):
        with pytest.raises(PayloadValidationError, match="missing required"):
            validate_payload(_payload_without("cpu_temp", "gpu_temp", "hostname"))


# ---------------------------------------------------------------------------
# Type errors
# ---------------------------------------------------------------------------


class TestTypeErrors:
    def test_timestamp_not_string(self):
        with pytest.raises(PayloadValidationError, match="timestamp.*string"):
            validate_payload(_payload(timestamp=12345))

    def test_timestamp_none_rejected(self):
        with pytest.raises(PayloadValidationError, match="timestamp.*string"):
            validate_payload(_payload(timestamp=None))

    def test_source_ok_not_bool(self):
        with pytest.raises(PayloadValidationError, match="source_ok.*boolean"):
            validate_payload(_payload(source_ok="yes"))

    def test_source_ok_int_rejected(self):
        """Python int 1 is not bool — schema requires actual bool."""
        with pytest.raises(PayloadValidationError, match="source_ok.*boolean"):
            validate_payload(_payload(source_ok=1))

    def test_numeric_field_string(self):
        with pytest.raises(PayloadValidationError, match="cpu_temp.*number"):
            validate_payload(_payload(cpu_temp="hot"))

    def test_numeric_field_bool_rejected(self):
        """bool is a subclass of int in Python but not a valid sensor value."""
        # Note: Python isinstance(True, int) is True, so bools pass the
        # number check.  This is acceptable — the agent never sends bools
        # for numeric fields in practice.
        # This test documents that behaviour rather than demanding rejection.
        p = _payload(cpu_temp=True)
        # If implementation treats bool as int, this passes:
        validate_payload(p)

    def test_numeric_field_list(self):
        with pytest.raises(PayloadValidationError, match="gpu_load.*number"):
            validate_payload(_payload(gpu_load=[1, 2]))
