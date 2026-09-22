"""IUVO digital inputs."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import STATE_INPUTS
from .entity import IuvoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up IUVO inputs."""
    coordinator = entry.runtime_data
    async_add_entities(
        IuvoBinarySensor(coordinator, module, channel)
        for module in coordinator.data.values()
        for channel in range(1, 9)
    )


class IuvoBinarySensor(IuvoEntity, BinarySensorEntity):
    """One IUVO digital input."""

    def __init__(self, coordinator, module, channel: int) -> None:
        super().__init__(coordinator, module, channel, STATE_INPUTS)
        self._attr_name = f"Wejście {channel}"

    @property
    def is_on(self) -> bool:
        """Return raw active state; NC inversion can be configured in HA."""
        return self._channel_value() != 0
