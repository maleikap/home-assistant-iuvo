"""IUVO maintenance buttons."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import STATE_OUTPUTS
from .entity import IuvoEntity
from .project_profile import MOMENTARY_OUTPUTS
from .protocol import build_set_output

GATE_PULSE_SECONDS = 0.7


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up maintenance and momentary output buttons."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = [IuvoRescanButton(coordinator)]
    entities.extend(
        IuvoMomentaryOutputButton(
            coordinator,
            module,
            channel,
            MOMENTARY_OUTPUTS[(module.address, channel)],
        )
        for module in coordinator.data.values()
        for channel in range(1, 7)
        if (module.address, channel) in MOMENTARY_OUTPUTS
    )
    async_add_entities(entities)


class IuvoRescanButton(CoordinatorEntity, ButtonEntity):
    """Trigger safe read-only module discovery."""

    _attr_has_entity_name = True
    _attr_name = "Wykryj moduły"
    _attr_unique_id = "iuvo-rescan-modules"
    _attr_icon = "mdi:magnify-scan"

    async def async_press(self) -> None:
        await self.coordinator.async_rescan()
        await self.coordinator.async_request_refresh()


class IuvoMomentaryOutputButton(IuvoEntity, ButtonEntity):
    """Generate a short pulse on an IUVO output."""

    _attr_icon = "mdi:gate"

    def __init__(self, coordinator, module, channel: int, name: str) -> None:
        super().__init__(coordinator, module, channel, STATE_OUTPUTS)
        self._attr_name = name
        self._press_lock = asyncio.Lock()

    async def async_press(self) -> None:
        """Toggle the output on briefly and then turn it off again."""
        async with self._press_lock:
            await self._send(build_set_output(self.module_address, self.channel))
            await asyncio.sleep(GATE_PULSE_SECONDS)
            await self._send(build_set_output(self.module_address, self.channel))
