"""IUVO maintenance buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up rescan button."""
    async_add_entities([IuvoRescanButton(entry.runtime_data)])


class IuvoRescanButton(CoordinatorEntity, ButtonEntity):
    """Trigger safe read-only module discovery."""

    _attr_has_entity_name = True
    _attr_name = "Wykryj moduły"
    _attr_unique_id = "iuvo-rescan-modules"
    _attr_icon = "mdi:magnify-scan"

    async def async_press(self) -> None:
        await self.coordinator.async_rescan()
        await self.coordinator.async_request_refresh()
