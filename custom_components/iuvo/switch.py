"""IUVO relay outputs."""

from __future__ import annotations

import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import STATE_OUTPUTS
from .entity import IuvoEntity
from .protocol import build_set_output
from .project_profile import MOMENTARY_OUTPUTS, SWITCH_NAMES, is_shutter_module

GATE_PULSE_SECONDS = 0.7


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up all detected IUVO relay channels."""
    coordinator = entry.runtime_data
    async_add_entities(
        IuvoSwitch(coordinator, module, channel)
        for module in coordinator.data.values()
        if not is_shutter_module(module.module_type)
        for channel in range(1, 7)
    )


class IuvoSwitch(IuvoEntity, SwitchEntity):
    """One IUVO output."""

    def __init__(self, coordinator, module, channel: int) -> None:
        super().__init__(coordinator, module, channel, STATE_OUTPUTS)
        self._attr_name = SWITCH_NAMES.get(module.address, {}).get(
            channel, f"Wyjście {channel}"
        )
        self._optimistic_state = False
        self._attr_assumed_state = False
        self._momentary = (module.address, channel) in MOMENTARY_OUTPUTS
        self._pulse_lock = asyncio.Lock()

    @property
    def is_on(self) -> bool:
        """Return output state."""
        if self._momentary:
            return self._optimistic_state
        if self.kind in self.module.states:
            return self._channel_value() != 0
        return self._optimistic_state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on, or generate a short pulse for a gate output."""
        if self._momentary:
            async with self._pulse_lock:
                if self._optimistic_state:
                    return
                await self._send(build_set_output(self.module_address, self.channel))
                self._optimistic_state = True
                self.async_write_ha_state()
                try:
                    await asyncio.sleep(GATE_PULSE_SECONDS)
                finally:
                    await self._send(
                        build_set_output(self.module_address, self.channel)
                    )
                    self._optimistic_state = False
                    self.async_write_ha_state()
            return

        if not self.is_on:
            await self._send(build_set_output(self.module_address, self.channel))
            self._optimistic_state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off using IUVO's safe toggle only when currently on."""
        if self._momentary:
            return
        if self.is_on:
            await self._send(build_set_output(self.module_address, self.channel))
            self._optimistic_state = False
            self.async_write_ha_state()

    async def async_toggle(self, **kwargs) -> None:
        """Toggle output."""
        if self._momentary:
            await self.async_turn_on(**kwargs)
            return
        await self._send(build_set_output(self.module_address, self.channel))
        self._optimistic_state = not self._optimistic_state
        self.async_write_ha_state()
