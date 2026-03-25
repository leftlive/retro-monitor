from __future__ import annotations

from typing import Optional

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RetroMonitorCoordinator
from .entity import RetroMonitorCoordinatorEntity

SOURCE_OK_DESCRIPTION = BinarySensorEntityDescription(
    key="source_ok",
    name="Source OK",
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RetroMonitorSourceOkEntity(coordinator, entry)])


class RetroMonitorSourceOkEntity(RetroMonitorCoordinatorEntity, BinarySensorEntity):
    entity_description = SOURCE_OK_DESCRIPTION

    def __init__(self, coordinator: RetroMonitorCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_source_ok"

    @property
    def is_on(self) -> Optional[bool]:
        return (self.coordinator.data or {}).get("source_ok")
