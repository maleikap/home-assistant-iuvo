"""IUVO relay outputs."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, STATE_OUTPUTS
from .entity import IuvoEntity
from .protocol import build_set_output
from .project_profile import is_shutter_module


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    momentary_outputs = coordinator.project_profile.momentary_outputs
    registry = er.async_get(hass)
    for module in coordinator.data.values():
        for address, channel in momentary_outputs:
            if address != module.address:
                continue
            unique_id = f"{module.identifier}-{STATE_OUTPUTS}-{channel}"
            entity_id = registry.async_get_entity_id("switch", DOMAIN, unique_id)
            if entity_id is not None:
                registry.async_remove(entity_id)
    async_add_entities(
        IuvoSwitch(coordinator, module, channel)
        for module in coordinator.data.values()
        if not is_shutter_module(module.module_type)
        for channel in range(1, 7)
        if (module.address, channel) not in momentary_outputs
    )


class IuvoSwitch(IuvoEntity, SwitchEntity):
    def __init__(self, coordinator, module, channel: int) -> None:
        super().__init__(coordinator, module, channel, STATE_OUTPUTS)
        self._attr_name = coordinator.project_profile.switch_name(module.address, channel)
        self._optimistic_state = False
        self._attr_assumed_state = False

    @property
    def is_on(self) -> bool:
        if self.kind in self.module.states:
            return self._channel_value() != 0
        return self._optimistic_state

    async def async_turn_on(self, **kwargs) -> None:
        if not self.is_on:
            await self._send(build_set_output(self.module_address, self.channel))
            self._optimistic_state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        if self.is_on:
            await self._send(build_set_output(self.module_address, self.channel))
            self._optimistic_state = False
            self.async_write_ha_state()

    async def async_toggle(self, **kwargs) -> None:
        await self._send(build_set_output(self.module_address, self.channel))
        self._optimistic_state = not self._optimistic_state
        self.async_write_ha_state()
