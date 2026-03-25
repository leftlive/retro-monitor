from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfFrequency, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RetroMonitorCoordinator
from .entity import RetroMonitorCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class RetroMonitorSensorDescription(SensorEntityDescription):
    field: str


DESCRIPTIONS: tuple[RetroMonitorSensorDescription, ...] = (
    RetroMonitorSensorDescription(key="cpu_temp", field="cpu_temp", name="CPU Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="cpu_load", field="cpu_load", name="CPU Load", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="cpu_clock", field="cpu_clock", name="CPU Clock", native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="cpu_power", field="cpu_power", name="CPU Power", native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="gpu_temp", field="gpu_temp", name="GPU Temperature", native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="gpu_load", field="gpu_load", name="GPU Load", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="gpu_clock", field="gpu_clock", name="GPU Clock", native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="gpu_power", field="gpu_power", name="GPU Power", native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="memory_used_mb", field="memory_used_mb", name="Memory Used", native_unit_of_measurement="MiB", state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="memory_total_mb", field="memory_total_mb", name="Memory Total", native_unit_of_measurement="MiB", state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="memory_percent", field="memory_percent", name="Memory Percent", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="fan_rpm_max", field="fan_rpm_max", name="Fan RPM Max", native_unit_of_measurement="rpm", state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="fan_rpm_avg", field="fan_rpm_avg", name="Fan RPM Avg", native_unit_of_measurement="rpm", state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="disk_temp_max", field="disk_temp_max", name="Disk Temperature Max", native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="disk_activity_percent", field="disk_activity_percent", name="Disk Activity", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="net_up_bps", field="net_up_bps", name="Net Upload", native_unit_of_measurement="bit/s", state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="net_down_bps", field="net_down_bps", name="Net Download", native_unit_of_measurement="bit/s", state_class=SensorStateClass.MEASUREMENT),
    RetroMonitorSensorDescription(key="system_power_estimated", field="system_power_estimated", name="System Power Estimated", native_unit_of_measurement=UnitOfPower.WATT, state_class=SensorStateClass.MEASUREMENT),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([RetroMonitorSensor(coordinator, entry, description) for description in DESCRIPTIONS])


class RetroMonitorSensor(RetroMonitorCoordinatorEntity, SensorEntity):
    entity_description: RetroMonitorSensorDescription

    def __init__(self, coordinator: RetroMonitorCoordinator, entry: ConfigEntry, description: RetroMonitorSensorDescription) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.field}"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self.entity_description.field)
