"""The Retro Monitor integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import RetroMonitorCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.device_registry import DeviceEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Retro Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    coordinator = RetroMonitorCoordinator(hass, entry)

    # First refresh BEFORE any platform setup so that device_info is
    # available when entities are instantiated.
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Retro Monitor config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a Retro Monitor config entry and clear in-memory state."""
    domain_data = hass.data.get(DOMAIN)
    if isinstance(domain_data, dict):
        domain_data.pop(entry.entry_id, None)


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry: DeviceEntry,
) -> bool:
    """Remove the monitor config entry when its HA device is deleted.

    Retro Monitor represents one telemetry source per config entry.  If the
    user deletes that device from the device page, keeping the config entry
    would immediately recreate the same device and entities.  Removing the
    config entry is the only behavior that matches the UI intent.
    """
    if config_entry.entry_id not in device_entry.config_entries:
        return False

    await hass.config_entries.async_remove(config_entry.entry_id)
    return True
