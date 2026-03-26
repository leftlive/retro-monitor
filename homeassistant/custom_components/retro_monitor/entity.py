"""Base entity for Retro Monitor."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RetroMonitorCoordinator


class RetroMonitorCoordinatorEntity(CoordinatorEntity[RetroMonitorCoordinator], Entity):
    """Base class for entities that track the coordinator's telemetry data."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RetroMonitorCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Build device info from cached identity or config entry fallback."""
        cached = self.coordinator.last_device_info
        if cached:
            device_id = cached.get("device_id") or self._entry.entry_id
            hostname = cached.get("hostname") or "Retro Monitor Host"
            platform = cached.get("platform") or "telemetry-agent"
        else:
            device_id = self._entry.entry_id
            hostname = "Retro Monitor Host"
            platform = "telemetry-agent"

        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=hostname,
            manufacturer="Retro Monitor",
            model=platform,
            configuration_url=self.coordinator.url,
        )
