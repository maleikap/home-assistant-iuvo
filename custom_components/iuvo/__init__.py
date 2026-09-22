"""IUVO RS-232 integration."""

from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError

from .const import (
    ATTR_COMMAND,
    CONF_MAX_MODULES,
    CONF_POLL_INTERVAL,
    CONF_RESPONSE_TIMEOUT,
    DEFAULT_MAX_MODULES,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RESPONSE_TIMEOUT,
    DOMAIN,
    PLATFORMS,
    SERVICE_RESCAN,
    SERVICE_SEND_COMMAND,
)
from .coordinator import IuvoCoordinator
from .protocol import IuvoConnectionError, IuvoSerialClient


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IUVO from a config entry."""
    client = IuvoSerialClient(
        entry.data[CONF_PORT],
        float(entry.options.get(CONF_RESPONSE_TIMEOUT, DEFAULT_RESPONSE_TIMEOUT)),
    )
    coordinator = IuvoCoordinator(
        hass,
        client,
        int(
            entry.options.get(
                CONF_MAX_MODULES, entry.data.get(CONF_MAX_MODULES, DEFAULT_MAX_MODULES)
            )
        ),
        int(entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
    )
    try:
        await coordinator.async_connect()
        await coordinator.async_config_entry_first_refresh()
    except IuvoConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def send_command(call: ServiceCall) -> None:
        command = call.data[ATTR_COMMAND]
        if command.startswith(("AT+key=", "AT+Save=")):
            raise HomeAssistantError(
                "Programming commands are locked until verified on hardware"
            )
        await coordinator.async_command(command)
        await coordinator.async_request_refresh()

    async def rescan(_: ServiceCall) -> None:
        await coordinator.async_rescan()
        await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            send_command,
            schema=vol.Schema({vol.Required(ATTR_COMMAND): cv.string}),
        )
    if not hass.services.has_service(DOMAIN, SERVICE_RESCAN):
        hass.services.async_register(DOMAIN, SERVICE_RESCAN, rescan)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload IUVO entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.async_close()
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
