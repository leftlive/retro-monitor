"""OLED auto-rotate switch entity for Retro Monitor.

This is a local-only entity — it stores the user's preference inside
Home Assistant.  A future v2 write-back API will push it to the agent.
"""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, PROFILE_DESKTOP
from .coordinator import RetroMonitorCoordinator
from .entity import RetroMonitorCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the OLED auto-rotate switch."""
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.profile != PROFILE_DESKTOP:
        return
    async_add_entities([RetroMonitorAutoRotateSwitch(coordinator, entry)])


class RetroMonitorAutoRotateSwitch(
    RetroMonitorCoordinatorEntity, SwitchEntity, RestoreEntity
):
    """Auto-rotate preference (local-only until v2 write-back)."""

    _attr_name = "Display Auto Rotate"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:rotate-3d-variant"

    def __init__(
        self,
        coordinator: RetroMonitorCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_oled_auto_rotate"
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
