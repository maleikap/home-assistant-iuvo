"""Base entities for IUVO."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IuvoCoordinator
from .protocol import IuvoModule


class IuvoEntity(CoordinatorEntity[IuvoCoordinator]):
    """Base IUVO channel entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IuvoCoordinator,
        module: IuvoModule,
        channel: int,
        kind: str,
    ) -> None:
        super().__init__(coordinator)
        self.module_address = module.address
        self.channel = channel
        self.kind = kind
        self._attr_unique_id = f"{module.identifier}-{kind}-{channel}"

    @property
    def module(self) -> IuvoModule:
        """Return current module data."""
        return self.coordinator.data.get(
            self.module_address, self.coordinator.modules[self.module_address]
        )

    @property
    def available(self) -> bool:
        """Return availability based on module discovery/communication."""
        # IUVO does not return a full snapshot for AT+Stan*=0. State frames are
        # event-driven, so lack of a cached channel value must not block control.
        return super().available and self.module.online

    @property
    def device_info(self) -> DeviceInfo:
        """Group channels under their IUVO module."""
        module = self.module
        return DeviceInfo(
            identifiers={(DOMAIN, module.identifier)},
            name=f"IUVO moduł {module.address}",
            manufacturer="IUVO",
            model=module.module_type or "Moduł RS-232",
            serial_number=module.mac,
        )

    def _channel_value(self, default: int = 0) -> int:
        """Return raw channel value."""
        values = self.module.states.get(self.kind, [])
        if self.channel - 1 >= len(values):
            return default
        return values[self.channel - 1]

    async def _send(self, command: str) -> None:
        """Send command and refresh states."""
        await self.coordinator.async_command(command)
        await self.coordinator.async_request_refresh()
