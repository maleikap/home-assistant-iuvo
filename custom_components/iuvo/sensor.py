"""IUVO module diagnostics."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up last-seen diagnostics."""
    coordinator = entry.runtime_data
    async_add_entities(
        IuvoLastSeen(coordinator, module.address)
        for module in coordinator.data.values()
    )


class IuvoLastSeen(CoordinatorEntity, SensorEntity):
    """Last successful response from a module."""

    _attr_has_entity_name = True
    _attr_name = "Ostatnia odpowiedź"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, address: int) -> None:
        super().__init__(coordinator)
        self.address = address
        module = coordinator.modules[address]
        self._attr_unique_id = f"{module.identifier}-last-seen"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, module.identifier)},
            "name": f"IUVO moduł {address}",
            "manufacturer": "IUVO",
            "model": module.module_type or "Moduł RS-232",
        }

    @property
    def native_value(self) -> datetime | None:
        stamp = self.coordinator.modules[self.address].last_seen
        return datetime.fromtimestamp(stamp).astimezone() if stamp else None
