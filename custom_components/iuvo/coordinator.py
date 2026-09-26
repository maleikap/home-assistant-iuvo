"""IUVO update coordinator."""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import STATE_INPUTS, STATE_LAMPS, STATE_OUTPUTS, STATE_SHUTTERS
from .protocol import (
    IuvoConnectionError,
    IuvoModule,
    IuvoSerialClient,
    build_state_command,
    parse_frame,
)

_LOGGER = logging.getLogger(__name__)
STATE_KINDS = (STATE_OUTPUTS, STATE_INPUTS, STATE_LAMPS, STATE_SHUTTERS)


class IuvoCoordinator(DataUpdateCoordinator[dict[int, IuvoModule]]):
    """Coordinate discovery, polling and commands over one serial connection."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: IuvoSerialClient,
        max_modules: int,
        poll_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="IUVO RS-232",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client
        self.max_modules = max_modules
        self.modules: dict[int, IuvoModule] = {}
        self.raw_log: list[str] = []
        self._discovery_complete = False

    async def async_connect(self) -> None:
        """Connect without blocking HA's event loop."""
        await self.hass.async_add_executor_job(self.client.connect)

    async def async_close(self) -> None:
        """Close connection."""
        await self.hass.async_add_executor_job(self.client.close)

    async def async_command(self, command: str, expect_reply: bool = True) -> list[str]:
        """Send a raw command and process returned frames."""
        lines = await self.hass.async_add_executor_job(
            lambda: self.client.command(command, expect_reply=expect_reply)
        )
        self._consume(lines)
        return lines

    async def async_rescan(self) -> dict[int, IuvoModule]:
        """Discover modules with the sequence recovered from IUVO Expert."""
        lines = await self.hass.async_add_executor_job(
            self.client.discover, self.max_modules
        )
        self._consume(lines)
        self._discovery_complete = True
        return self.modules

    async def _async_update_data(self) -> dict[int, IuvoModule]:
        """Poll all known modules; run safe discovery on first update."""
        try:
            if not self._discovery_complete:
                await self.async_rescan()
            # IUVO Expert requests one bus-wide snapshot with address 0.
            # Modules identify themselves in O=/I=/L=/R= response frames.
            for kind in STATE_KINDS:
                await self.async_command(build_state_command(kind, 0))
            return self.modules
        except IuvoConnectionError as err:
            raise UpdateFailed(f"IUVO serial communication failed: {err}") from err

    def _consume(self, lines: list[str]) -> None:
        """Update module state from received lines."""
        for line in lines:
            self.raw_log.append(line)
            del self.raw_log[:-100]
            frame = parse_frame(line)
            if frame is None or frame.address is None:
                continue
            if not 1 <= frame.address <= self.max_modules:
                continue
            module = self.modules.setdefault(
                frame.address, IuvoModule(address=frame.address)
            )
            module.online = True
            module.last_seen = time.time()
            module.raw[frame.kind] = frame.raw
            if frame.kind in STATE_KINDS:
                module.states[frame.kind] = frame.values
            if frame.mac:
                module.mac = frame.mac
            if frame.module_type:
                module.module_type = frame.module_type
