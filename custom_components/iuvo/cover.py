"""IUVO roller shutters."""

from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import STATE_SHUTTERS
from .entity import IuvoEntity
from .protocol import build_set_shutter
from .project_profile import COVER_NAMES, is_shutter_module


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up IUVO shutters."""
    coordinator = entry.runtime_data
    async_add_entities(
        IuvoCover(coordinator, module, channel)
        for module in coordinator.data.values()
        if is_shutter_module(module.module_type)
        for channel in range(1, 5)
    )


class IuvoCover(IuvoEntity, CoverEntity):
    """One IUVO shutter channel."""

    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, coordinator, module, channel: int) -> None:
        super().__init__(coordinator, module, channel, STATE_SHUTTERS)
        self._attr_name = COVER_NAMES.get(module.address, {}).get(
            channel, f"Roleta {channel}"
        )

    @property
    def is_opening(self) -> bool:
        return self._channel_value() == 1

    @property
    def is_closing(self) -> bool:
        return self._channel_value() == 2

    @property
    def is_closed(self) -> bool | None:
        """IUVO state does not expose a verified absolute position yet."""
        return None

    async def async_open_cover(self, **kwargs) -> None:
        await self._send(build_set_shutter(self.module_address, self.channel, 1))

    async def async_close_cover(self, **kwargs) -> None:
        await self._send(build_set_shutter(self.module_address, self.channel, 2))

    async def async_stop_cover(self, **kwargs) -> None:
        await self._send(build_set_shutter(self.module_address, self.channel, 3))
