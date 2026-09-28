"""Config flow for IUVO RS-232."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_MAX_MODULES,
    CONF_POLL_INTERVAL,
    CONF_PROFILE_PATH,
    CONF_RESPONSE_TIMEOUT,
    DEFAULT_MAX_MODULES,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PROFILE_PATH,
    DEFAULT_RESPONSE_TIMEOUT,
    DOMAIN,
    MAX_MODULES,
    MIN_MODULES,
)
from .protocol import IuvoConnectionError, IuvoSerialClient


def _port_schema(
    default_port: str = "/dev/ttyUSB0", default_modules: int = DEFAULT_MAX_MODULES
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PORT, default=default_port): str,
            vol.Required(CONF_MAX_MODULES, default=default_modules): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_MODULES, max=MAX_MODULES)
            ),
        }
    )


class IuvoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle IUVO configuration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Configure serial port."""
        errors: dict[str, str] = {}
        if user_input is not None:
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(port)
            self._abort_if_unique_id_configured()
            client = IuvoSerialClient(port, DEFAULT_RESPONSE_TIMEOUT)
            try:
                await self.hass.async_add_executor_job(client.connect)
            except IuvoConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.hass.async_add_executor_job(client.close)
                return self.async_create_entry(title=f"IUVO ({port})", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_port_schema(), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return IuvoOptionsFlow(config_entry)


class IuvoOptionsFlow(config_entries.OptionsFlow):
    """IUVO options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Edit polling and scan limits."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self._entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAX_MODULES, default=current.get(CONF_MAX_MODULES, self._entry.data.get(CONF_MAX_MODULES, DEFAULT_MAX_MODULES))): vol.All(vol.Coerce(int), vol.Range(min=MIN_MODULES, max=MAX_MODULES)),
                    vol.Required(CONF_POLL_INTERVAL, default=current.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)): vol.All(vol.Coerce(int), vol.Range(min=2, max=60)),
                    vol.Required(CONF_RESPONSE_TIMEOUT, default=current.get(CONF_RESPONSE_TIMEOUT, DEFAULT_RESPONSE_TIMEOUT)): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=3.0)),
                    vol.Optional(CONF_PROFILE_PATH, default=current.get(CONF_PROFILE_PATH, DEFAULT_PROFILE_PATH)): str,
                }
            ),
        )
