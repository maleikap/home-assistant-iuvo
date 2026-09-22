"""IUVO ASCII protocol and serial transport."""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass, field

import serial

from .const import (
    DEFAULT_BAUDRATE,
    STATE_INPUTS,
    STATE_LAMPS,
    STATE_OUTPUTS,
    STATE_SHUTTERS,
)

_LOGGER = logging.getLogger(__name__)

_STATE_NAMES = {
    "StanIn": STATE_INPUTS,
    "StanOut": STATE_OUTPUTS,
    "StanLamp": STATE_LAMPS,
    "StanRol": STATE_SHUTTERS,
}
_STATE_RE = re.compile(
    r"^(?:AT\+)?(StanIn|StanOut|StanLamp|StanRol)\s*=\s*(.+)$", re.IGNORECASE
)
_FIND_RE = re.compile(r"^(?:AT\+)?(?:Find|Search)\s*=\s*(.+)$", re.IGNORECASE)


class IuvoError(Exception):
    """Base IUVO exception."""


class IuvoConnectionError(IuvoError):
    """Serial connection error."""


@dataclass(slots=True)
class IuvoModule:
    """Runtime representation of one IUVO module."""

    address: int
    mac: str | None = None
    module_type: str | None = None
    online: bool = False
    last_seen: float | None = None
    states: dict[str, list[int]] = field(default_factory=dict)
    raw: dict[str, str] = field(default_factory=dict)

    @property
    def identifier(self) -> str:
        """Return stable identifier, preferring the hardware MAC."""
        return self.mac or f"address-{self.address}"


@dataclass(slots=True)
class ParsedFrame:
    """Parsed IUVO response."""

    kind: str
    address: int | None
    values: list[int] = field(default_factory=list)
    mac: str | None = None
    module_type: str | None = None
    raw: str = ""


def parse_frame(line: str) -> ParsedFrame | None:
    """Parse a state/discovery response produced by IUVO Expert commands."""
    raw = line.strip()
    if not raw:
        return None

    state_match = _STATE_RE.match(raw)
    if state_match:
        name, payload = state_match.groups()
        fields = [item.strip() for item in payload.split(",")]
        integers: list[int] = []
        for item in fields:
            try:
                integers.append(int(item, 0))
            except ValueError:
                continue
        if not integers:
            return ParsedFrame(_STATE_NAMES[name], None, raw=raw)
        return ParsedFrame(_STATE_NAMES[name], integers[0], integers[1:], raw=raw)

    find_match = _FIND_RE.match(raw)
    if find_match:
        fields = [item.strip() for item in find_match.group(1).split(",")]
        address: int | None = None
        if fields:
            try:
                address = int(fields[0], 0)
            except ValueError:
                pass
        mac = next(
            (item for item in fields if re.fullmatch(r"[0-9A-Fa-f]{4,12}", item)), None
        )
        module_type = next(
            (
                item
                for item in fields
                if "IUVO" in item or "Controller" in item or "Roller" in item
            ),
            None,
        )
        return ParsedFrame(
            "discovery", address, mac=mac, module_type=module_type, raw=raw
        )

    return ParsedFrame("unknown", None, raw=raw)


def build_state_command(kind: str, address: int) -> str:
    """Build one of the read-only state commands."""
    commands = {
        STATE_OUTPUTS: "StanOut",
        STATE_INPUTS: "StanIn",
        STATE_LAMPS: "StanLamp",
        STATE_SHUTTERS: "StanRol",
    }
    return f"AT+{commands[kind]}={address}"


def build_set_output(address: int, channel: int) -> str:
    """Build output toggle command (3 = toggle, 0 = unchanged)."""
    if not 1 <= channel <= 6:
        raise ValueError("Output channel must be 1..6")
    values = [0] * 6
    values[channel - 1] = 3
    return f"AT+SetOut={address}," + ",".join(map(str, values))


def build_set_lamp(address: int, channel: int, on: bool) -> str:
    """Build lamp command (1 = on, 2 = off, 0 = unchanged)."""
    if not 1 <= channel <= 8:
        raise ValueError("Lamp channel must be 1..8")
    values = [0] * 8
    values[channel - 1] = 1 if on else 2
    return f"AT+SetLamp={address}," + ",".join(map(str, values))


def build_set_shutter(
    address: int, channel: int, action: int, seconds: int = 30
) -> str:
    """Build shutter command; actions 1/2/3 are open/close/stop."""
    if not 1 <= channel <= 4:
        raise ValueError("Shutter channel must be 1..4")
    if action not in (1, 2, 3, 4):
        raise ValueError("Shutter action must be 1..4")
    values = [0] * 4
    values[channel - 1] = action
    return f"AT+SetRol={address},{seconds}," + ",".join(map(str, values))


class IuvoSerialClient:
    """Thread-safe synchronous serial client used through HA's executor."""

    def __init__(self, port: str, timeout: float) -> None:
        self.port = port
        self.timeout = timeout
        self._serial: serial.Serial | None = None
        self._lock = threading.RLock()

    @property
    def connected(self) -> bool:
        """Return whether the serial port is open."""
        return self._serial is not None and self._serial.is_open

    def connect(self) -> None:
        """Open IUVO serial port using parameters recovered from IUVO Expert."""
        with self._lock:
            if self.connected:
                return
            try:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=DEFAULT_BAUDRATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                    write_timeout=1,
                )
                self._serial.reset_input_buffer()
            except (OSError, serial.SerialException) as err:
                self._serial = None
                raise IuvoConnectionError(str(err)) from err

    def close(self) -> None:
        """Close serial port."""
        with self._lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                finally:
                    self._serial = None

    def command(self, command: str, *, expect_reply: bool = True) -> list[str]:
        """Write a CRLF-terminated command and collect available response lines."""
        with self._lock:
            if not self.connected:
                self.connect()
            assert self._serial is not None
            safe_command = command.strip().replace("\r", "").replace("\n", "")
            try:
                self._serial.write((safe_command + "\r\n").encode("ascii"))
                self._serial.flush()
                if not expect_reply:
                    return []

                lines: list[str] = []
                deadline = time.monotonic() + self.timeout
                while time.monotonic() < deadline:
                    raw = self._serial.readline()
                    if not raw:
                        break
                    decoded = raw.decode("ascii", errors="replace").strip()
                    if decoded:
                        lines.append(decoded)
                    if self._serial.in_waiting == 0:
                        break
                return lines
            except (OSError, serial.SerialException) as err:
                self.close()
                raise IuvoConnectionError(str(err)) from err
