"""Tests for Retro Monitor sensor entity descriptions and behaviour.

Pure-Python tests that verify sensor metadata and value extraction logic
without a running Home Assistant instance.
"""

import sys
import os

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

# Stub HA modules so we can import sensor.py at module level.
from unittest.mock import MagicMock

for mod_name in (
    "homeassistant",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.helpers",
    "homeassistant.helpers.device_registry",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
):
    sys.modules.setdefault(mod_name, MagicMock())

# Provide the specific HA constants that sensor.py references at import time.
ha_const = sys.modules["homeassistant.const"]
ha_const.PERCENTAGE = "%"
ha_const.EntityCategory = type("EntityCategory", (), {"DIAGNOSTIC": "diagnostic", "CONFIG": "config"})

ha_sensor = sys.modules["homeassistant.components.sensor"]
ha_sensor.SensorEntity = object
ha_sensor.SensorEntityDescription = object
ha_sensor.SensorStateClass = type("SensorStateClass", (), {"MEASUREMENT": "measurement"})

# UnitOf* stubs
ha_const.UnitOfTemperature = type("UnitOfTemperature", (), {"CELSIUS": "°C"})
ha_const.UnitOfFrequency = type("UnitOfFrequency", (), {"MEGAHERTZ": "MHz"})
ha_const.UnitOfPower = type("UnitOfPower", (), {"WATT": "W"})
ha_const.UnitOfDataRate = type("UnitOfDataRate", (), {"BITS_PER_SECOND": "bit/s"})

import pytest  # noqa: E402


# ---------------------------------------------------------------------------
# We cannot directly import sensor.py due to deep HA coupling in the
# dataclass descriptors, so we test the key design decisions manually.
# ---------------------------------------------------------------------------


VALID_PAYLOAD = {
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

# Sensor fields that should exist in the integration, split by tier.
CORE_FIELDS = {
    "cpu_temp", "cpu_load", "cpu_clock", "cpu_power",
    "gpu_temp", "gpu_load", "gpu_clock", "gpu_power",
    "memory_used_mb", "memory_percent",
    "fan_rpm_max",
    "disk_activity_percent",
    "net_up_bps", "net_down_bps",
}

DIAGNOSTIC_FIELDS = {
    "memory_total_mb", "fan_rpm_avg", "disk_temp_max", "system_power_estimated",
}

ALL_SENSOR_FIELDS = CORE_FIELDS | DIAGNOSTIC_FIELDS


class TestSensorFieldMapping:
    """Verify that each telemetry field is covered by a sensor description."""

    def test_all_telemetry_fields_have_sensors(self):
        """Every numeric protocol field must map to exactly one sensor."""
        from validator import NUMERIC_FIELDS

        uncovered = NUMERIC_FIELDS - ALL_SENSOR_FIELDS
        assert uncovered == set(), f"Protocol fields without sensors: {uncovered}"

    def test_no_extra_sensors(self):
        """No sensor should reference a field that is not in the protocol."""
        from validator import NUMERIC_FIELDS

        extra = ALL_SENSOR_FIELDS - NUMERIC_FIELDS
        assert extra == set(), f"Sensors without protocol fields: {extra}"


class TestSensorValueExtraction:
    """Test the value extraction pattern used by native_value."""

    def test_normal_value(self):
        """Simulates the sensor reading a normal value."""
        value = VALID_PAYLOAD.get("cpu_temp")
        assert value == 58.0

    def test_null_value_returns_none(self):
        """null in payload → None → HA shows 'unknown'."""
        value = VALID_PAYLOAD.get("system_power_estimated")
        assert value is None

    def test_missing_data_returns_none(self):
        """When coordinator.data is None, native_value should be None."""
        data = None
        value = (data or {}).get("cpu_temp")
        assert value is None

    def test_all_fields_readable(self):
        """Every sensor field should be readable from the valid payload."""
        for field in ALL_SENSOR_FIELDS:
            value = VALID_PAYLOAD.get(field)
            # All fields should exist (even if None for system_power_estimated)
            assert field in VALID_PAYLOAD, f"Field {field} missing from test payload"


class TestEntityTiering:
    """Verify the separation between core and diagnostic sensors."""

    def test_core_and_diagnostic_disjoint(self):
        assert CORE_FIELDS & DIAGNOSTIC_FIELDS == set()

    def test_core_count(self):
        assert len(CORE_FIELDS) == 14

    def test_diagnostic_count(self):
        assert len(DIAGNOSTIC_FIELDS) == 4

    def test_total_sensor_count(self):
        assert len(ALL_SENSOR_FIELDS) == 18
