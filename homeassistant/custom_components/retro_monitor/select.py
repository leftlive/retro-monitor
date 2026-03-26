"""OLED display mode select entity for Retro Monitor.

This is a local-only entity — it stores the user's preference inside
Home Assistant.  A future v2 write-back API will push it to the agent.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DISPLAY_MODE_OPTIONS, DOMAIN
from .coordinator import RetroMonitorCoordinator
from .entity import RetroMonitorCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the OLED display mode selector."""
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RetroMonitorDisplayModeSelect(coordinator, entry)])


class RetroMonitorDisplayModeSelect(
    RetroMonitorCoordinatorEntity, SelectEntity, RestoreEntity
):
    """Display mode preference (local-only until v2 write-back)."""

    _attr_options = DISPLAY_MODE_OPTIONS
    _attr_name = "Display Mode"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:monitor-eye"

    def __init__(
        self,
        coordinator: RetroMonitorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_oled_display_mode"
        self._attr_current_option = DISPLAY_MODE_OPTIONS[0]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            if last_state.state in self._attr_options:
                self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
