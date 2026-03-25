from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(
        [
            RetroMonitorNumberEntity(entry, "oled_page_interval", "OLED Page Interval", 5, 60, 1, 10),
            RetroMonitorNumberEntity(entry, "oled_brightness", "OLED Brightness", 0, 255, 1, 180),
        ]
    )


class RetroMonitorNumberEntity(NumberEntity, RestoreEntity):
    def __init__(self, entry: ConfigEntry, key: str, name: str, min_value: float, max_value: float, step: float, default_value: float) -> None:
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_value = default_value

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_number_data := await self.async_get_last_number_data():
            self._attr_native_value = last_number_data.native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()

