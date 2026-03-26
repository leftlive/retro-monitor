"""OLED numeric control entities for Retro Monitor.

These are local-only entities — they store the user's preferences inside
Home Assistant.  A future v2 write-back API will push them to the agent.
"""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
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
    """Set up OLED brightness and page interval controls."""
    coordinator: RetroMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.profile != PROFILE_DESKTOP:
        return
    async_add_entities(
        [
            RetroMonitorNumberEntity(
                coordinator,
                entry,
                key="oled_page_interval",
                name="Display Page Interval",
                min_value=5,
                max_value=60,
                step=1,
                default_value=10,
                icon="mdi:timer-outline",
                unit="s",
            ),
            RetroMonitorNumberEntity(
                coordinator,
                entry,
                key="oled_brightness",
                name="Display Brightness",
                min_value=0,
                max_value=255,
                step=1,
                default_value=180,
                icon="mdi:brightness-6",
            ),
        ]
    )


class RetroMonitorNumberEntity(
    RetroMonitorCoordinatorEntity, NumberEntity, RestoreEntity
):
    """Numeric display preference (local-only until v2 write-back)."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: RetroMonitorCoordinator,
        entry: ConfigEntry,
        *,
        key: str,
        name: str,
        min_value: float,
        max_value: float,
        step: float,
        default_value: float,
        icon: str | None = None,
        unit: str | None = None,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_value = default_value
        if icon:
            self._attr_icon = icon
        if unit:
            self._attr_native_unit_of_measurement = unit

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            try:
                self._attr_native_value = float(last_state.state)
            except (TypeError, ValueError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
