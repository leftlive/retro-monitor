"""Config flow for the Retro Monitor integration."""

from __future__ import annotations

import logging
from typing import Any, Optional

import voluptuous as vol
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .validator import PayloadValidationError, validate_payload

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            int, vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_PATH, default=DEFAULT_PATH): str,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=1, max=60)
        ),
    }
)


class RetroMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Retro Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial user step with connection validation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Uniqueness check first.
            unique_id = (
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                f"{user_input[CONF_PATH]}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Attempt a real connection test before persisting the entry.
            error = await self._test_connection(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_PATH],
            )
            if error is None:
                return self.async_create_entry(
                    title="Retro Monitor", data=user_input
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def _test_connection(
        self, host: str, port: int, path: str
    ) -> str | None:
        """Test whether the agent responds with a valid telemetry payload.

        Returns an error key for translation, or ``None`` on success.
        """
        url = f"http://{host}:{port}{path}"
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
        except (ClientError, TimeoutError, OSError) as err:
            _LOGGER.debug("Connection test failed for %s: %s", url, err)
            return "cannot_connect"
        except ValueError:
            _LOGGER.debug("Non-JSON response from %s", url)
            return "invalid_response"

        try:
            validate_payload(data)
        except PayloadValidationError as err:
            _LOGGER.debug("Payload validation failed for %s: %s", url, err)
            return "invalid_response"

        return None
