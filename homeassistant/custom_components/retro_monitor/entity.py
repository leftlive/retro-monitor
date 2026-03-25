from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RetroMonitorCoordinator


class RetroMonitorCoordinatorEntity(CoordinatorEntity[RetroMonitorCoordinator], Entity):
    def __init__(self, coordinator: RetroMonitorCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        device_id = data.get("device_id") or self._entry.entry_id
        hostname = data.get("hostname") or "Retro Monitor Host"
        return DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=hostname,
            manufacturer="Retro Monitor",
            model=data.get("platform") or "telemetry-agent",
        )

