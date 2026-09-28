"""IUVO indicator/light channels."""

from __future__ import annotations

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import STATE_LAMPS
from .entity import IuvoEntity
from .protocol import build_set_lamp
from .project_profile import is_shutter_module


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(IuvoLight(coordinator, module, channel) for module in coordinator.data.values() if not is_shutter_module(module.module_type) for channel in range(1, 9))


class IuvoLight(IuvoEntity, LightEntity):
    def __init__(self, coordinator, module, channel: int) -> None:
        super().__init__(coordinator, module, channel, STATE_LAMPS)
        self._attr_name = coordinator.project_profile.light_name(module.address, channel)

    @property
    def is_on(self) -> bool:
        return self._channel_value() != 0

    async def async_turn_on(self, **kwargs) -> None:
        await self._send(build_set_lamp(self.module_address, self.channel, True))

    async def async_turn_off(self, **kwargs) -> None:
        await self._send(build_set_lamp(self.module_address, self.channel, False))
