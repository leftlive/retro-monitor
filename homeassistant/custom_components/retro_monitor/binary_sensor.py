"""Source OK binary sensor for Retro Monitor."""

from __future__ import annotations

from typing import Any, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RetroMonitorCoordinator
from .entity import RetroMonitorCoordinatorEntity

SOURCE_OK_DESCRIPTION = BinarySensorEntityDescription(
    key="source_ok",
    name="Data Source OK",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the source_ok binary sensor."""
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RetroMonitorSourceOkEntity(coordinator, entry)])


class RetroMonitorSourceOkEntity(RetroMonitorCoordinatorEntity, BinarySensorEntity):
    """Reflects whether the telemetry agent considers its data trustworthy."""

    entity_description = SOURCE_OK_DESCRIPTION

    def __init__(
        self,
        coordinator: RetroMonitorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_source_ok"

    @property
    def is_on(self) -> Optional[bool]:
        """True when the agent reports source_ok=true."""
        data = self.coordinator.data
        if data is None:
            return None
        return data.get("source_ok")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose timestamp and platform as diagnostic attributes."""
        data = self.coordinator.data
        if data is None:
            return {}
        attrs: dict[str, Any] = {}
        if ts := data.get("timestamp"):
            attrs["sample_timestamp"] = ts
        if platform := data.get("platform"):
            attrs["agent_platform"] = platform
        return attrs
