"""Data update coordinator for Retro Monitor telemetry."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, DOMAIN
from .validator import PayloadValidationError, validate_payload

_LOGGER = logging.getLogger(__name__)


class RetroMonitorCoordinator(DataUpdateCoordinator[dict]):
    """Fetches telemetry snapshots from the local agent.

    Error model:

    1. **Transport failure** – DNS, connection refused, timeout, non-2xx HTTP,
       or non-JSON body.  Raises ``UpdateFailed``; every entity becomes
       *unavailable* until a successful refresh.

    2. **Payload validation failure** – the body IS valid JSON but violates
       the telemetry schema (missing fields, wrong types).  Treated the same
       as transport failure: ``UpdateFailed`` + a WARNING log.

    3. **Degraded payload** – ``source_ok=false``.  This is **not** a failure.
       Data is returned normally; the ``source_ok`` binary sensor reflects the
       degradation and individual ``null`` fields become *unknown*.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.url: str = f"http://{self.host}:{self.port}/telemetry"
        self.session = async_get_clientsession(hass)

        # Cached device identity —— survives transient failures so that
        # device_info stays stable even when the agent is temporarily down.
        self.last_device_info: dict[str, str] | None = None

        # True when the most recent successful payload had source_ok=false.
        self.payload_degraded: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=entry.data[CONF_SCAN_INTERVAL]),
        )

    async def _async_update_data(self) -> dict:
        """Fetch a single telemetry snapshot from the agent."""

        # ------------------------------------------------------------------
        # Layer 1: Transport
        # ------------------------------------------------------------------
        try:
            async with self.session.get(self.url, timeout=10) as response:
                response.raise_for_status()
                payload: Any = await response.json()
        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(
                f"Transport failure when fetching {self.url}: {err}"
            ) from err
        except ValueError as err:
            # aiohttp raises ValueError for non-JSON bodies.
            raise UpdateFailed(
                f"Agent returned non-JSON response from {self.url}: {err}"
            ) from err

        # ------------------------------------------------------------------
        # Layer 2: Payload validation
        # ------------------------------------------------------------------
        try:
            validate_payload(payload)
        except PayloadValidationError as err:
            _LOGGER.warning(
                "Invalid telemetry payload from %s: %s", self.url, err
            )
            raise UpdateFailed(
                f"Invalid telemetry payload: {err}"
            ) from err

        # ------------------------------------------------------------------
        # Layer 3: Degraded payload (source_ok=false)
        # ------------------------------------------------------------------
        self.payload_degraded = not payload["source_ok"]
        if self.payload_degraded:
            _LOGGER.debug(
                "Telemetry from %s is degraded (source_ok=false)", self.url
            )

        # Cache device identity for stable device_info rendering.
        self.last_device_info = {
            "device_id": payload.get("device_id", ""),
            "hostname": payload.get("hostname", ""),
            "platform": payload.get("platform", ""),
        }

        return payload
