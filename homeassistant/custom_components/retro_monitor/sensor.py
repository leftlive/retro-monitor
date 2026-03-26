"""Telemetry sensor entities for Retro Monitor."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PROFILE_DESKTOP, PROFILE_ROUTER
from .coordinator import RetroMonitorCoordinator
from .entity import RetroMonitorCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class RetroMonitorSensorDescription(SensorEntityDescription):
    """Extended sensor description carrying the JSON field name."""

    field: str


# ---------------------------------------------------------------------------
# Core sensors — shown by default in the Lovelace UI
# ---------------------------------------------------------------------------

_CORE_SENSORS: tuple[RetroMonitorSensorDescription, ...] = (
    RetroMonitorSensorDescription(
        key="cpu_temp",
        field="cpu_temp",
        name="CPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="cpu_load",
        field="cpu_load",
        name="CPU Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="cpu_clock",
        field="cpu_clock",
        name="CPU Clock",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="cpu_power",
        field="cpu_power",
        name="CPU Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="gpu_temp",
        field="gpu_temp",
        name="GPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="gpu_load",
        field="gpu_load",
        name="GPU Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="gpu_clock",
        field="gpu_clock",
        name="GPU Clock",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="gpu_power",
        field="gpu_power",
        name="GPU Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="memory_used_mb",
        field="memory_used_mb",
        name="Memory Used",
        native_unit_of_measurement="MiB",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="memory_percent",
        field="memory_percent",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="fan_rpm_max",
        field="fan_rpm_max",
        name="Fan Speed (Max)",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="disk_activity_percent",
        field="disk_activity_percent",
        name="Disk Activity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="net_up_bps",
        field="net_up_bps",
        name="Network Upload",
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="net_down_bps",
        field="net_down_bps",
        name="Network Download",
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# ---------------------------------------------------------------------------
# Diagnostic sensors — hidden from default UI, visible via "show all"
# ---------------------------------------------------------------------------

_DIAGNOSTIC_SENSORS: tuple[RetroMonitorSensorDescription, ...] = (
    RetroMonitorSensorDescription(
        key="memory_total_mb",
        field="memory_total_mb",
        name="Memory Total",
        native_unit_of_measurement="MiB",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="fan_rpm_avg",
        field="fan_rpm_avg",
        name="Fan Speed (Average)",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="disk_temp_max",
        field="disk_temp_max",
        name="Disk Temperature (Max)",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="system_power_estimated",
        field="system_power_estimated",
        name="System Power (Estimated)",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

DESCRIPTIONS: tuple[RetroMonitorSensorDescription, ...] = (
    *_CORE_SENSORS,
    *_DIAGNOSTIC_SENSORS,
)

_ROUTER_CORE_SENSORS: tuple[RetroMonitorSensorDescription, ...] = (
    RetroMonitorSensorDescription(
        key="net_down_bps",
        field="net_down_bps",
        name="WAN Download",
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="net_up_bps",
        field="net_up_bps",
        name="WAN Upload",
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="cpu_temp",
        field="cpu_temp",
        name="CPU Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="cpu_load_percent",
        field="cpu_load_percent",
        name="CPU Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="memory_used_mb",
        field="memory_used_mb",
        name="Memory Used",
        native_unit_of_measurement="MiB",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    RetroMonitorSensorDescription(
        key="memory_percent",
        field="memory_percent",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_ROUTER_DIAGNOSTIC_SENSORS: tuple[RetroMonitorSensorDescription, ...] = (
    RetroMonitorSensorDescription(
        key="net_link_mbps",
        field="net_link_mbps",
        name="WAN Link Speed",
        native_unit_of_measurement="Mbps",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="net_util_percent",
        field="net_util_percent",
        name="WAN Utilization",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="memory_total_mb",
        field="memory_total_mb",
        name="Memory Total",
        native_unit_of_measurement="MiB",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="wan_uptime_s",
        field="wan_uptime_s",
        name="WAN Uptime",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RetroMonitorSensorDescription(
        key="wan_ip",
        field="wan_ip",
        name="WAN IP",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

ROUTER_DESCRIPTIONS: tuple[RetroMonitorSensorDescription, ...] = (
    *_ROUTER_CORE_SENSORS,
    *_ROUTER_DIAGNOSTIC_SENSORS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Retro Monitor sensor entities."""
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = (
        ROUTER_DESCRIPTIONS
        if coordinator.profile == PROFILE_ROUTER
        else DESCRIPTIONS
    )
    async_add_entities(
        RetroMonitorSensor(coordinator, entry, desc) for desc in descriptions
    )
    async_add_entities([RetroMonitorPayloadSensor(coordinator, entry)])


class RetroMonitorPayloadSensor(RetroMonitorCoordinatorEntity, SensorEntity):
    """A sensor that aggregates essential telemetry into a compact JSON string for ESP32."""

    def __init__(
        self,
        coordinator: RetroMonitorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_display_payload"
        self._attr_name = "Display Payload"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Return a minified JSON payload of current stats."""
        data = self.coordinator.data
        if data is None:
            return None

        # Heartbeat ensures the payload state changes on every successful
        # coordinator refresh, even when the underlying metrics remain flat.
        heartbeat = time.monotonic_ns() // 1_000_000

        profile = self.coordinator.profile
        if profile == PROFILE_DESKTOP:
            payload = {
                "ct": data.get("cpu_temp"),
                "cl": data.get("cpu_load"),
                "cp": data.get("cpu_power"),
                "gt": data.get("gpu_temp"),
                "gl": data.get("gpu_load"),
                "sp": data.get("system_power_estimated"),
                "mu": data.get("memory_used_mb"),
                "mp": data.get("memory_percent"),
                "dt": data.get("disk_temp_max"),
                "ok": 1 if data.get("source_ok") else 0,
                "hb": heartbeat,
            }
        else:
            payload = {
                "nd": data.get("net_down_bps"),
                "nu": data.get("net_up_bps"),
                "ct": data.get("cpu_temp"),
                "cl": data.get("cpu_load_percent"),
                "wu": data.get("wan_uptime_s"),
                "mu": data.get("memory_used_mb"),
                "mt": data.get("memory_total_mb"),
                "mp": data.get("memory_percent"),
                "ok": 1 if data.get("source_ok") else 0,
                "hb": heartbeat,
            }

        # Uses separators=(',', ':') to eliminate all external whitespace.
        return json.dumps(payload, separators=(',', ':'))


class RetroMonitorSensor(RetroMonitorCoordinatorEntity, SensorEntity):
    """A single telemetry measurement from the retro-monitor agent."""

    entity_description: RetroMonitorSensorDescription

    def __init__(
        self,
        coordinator: RetroMonitorCoordinator,
        entry: ConfigEntry,
        description: RetroMonitorSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.field}"

    @property
    def native_value(self):
        """Return the sensor value.  ``None`` → HA shows *unknown*."""
        data = self.coordinator.data
        if data is None:
            return None
        return data.get(self.entity_description.field)
