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
_SHORT_STATE_NAMES = {
    "I": STATE_INPUTS,
    "O": STATE_OUTPUTS,
    "L": STATE_LAMPS,
    "R": STATE_SHUTTERS,
}
_STATE_RE = re.compile(
    r"^(?:AT\+)?(StanIn|StanOut|StanLamp|StanRol)\s*=\s*(.+)$", re.IGNORECASE
)
_SHORT_STATE_RE = re.compile(r"^([OILR])\s*=\s*(.+)$", re.IGNORECASE)
_FIND_RE = re.compile(r"^AT\+Find\s*=\s*(.+)$", re.IGNORECASE)
_MODULE_TYPES = {
    "1": "IUVO Controller0806",
    "2": "IUVO Controller0806RTC",
    "3": "IUVO Roller Shutter0804",
    "4": "IUVO module type 4",
}


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
        """Return a stable identifier unique on one IUVO bus."""
        # The second AT+Find field is a module family/firmware number, not a
        # unique MAC: several modules commonly report e.g. 0604. The bus
        # address is therefore required to prevent HA merging devices.
        suffix = f"-{self.mac}" if self.mac else ""
        return f"address-{self.address}{suffix}"


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

    short_state_match = _SHORT_STATE_RE.match(raw)
    if short_state_match:
        name, payload = short_state_match.groups()
        fields = [item.strip() for item in payload.split(",")]
        integers: list[int] = []
        for item in fields:
            try:
                integers.append(int(item, 0))
            except ValueError:
                continue
        if not integers:
            return ParsedFrame(_SHORT_STATE_NAMES[name.upper()], None, raw=raw)
        return ParsedFrame(
            _SHORT_STATE_NAMES[name.upper()], integers[0], integers[1:], raw=raw
        )

    find_match = _FIND_RE.match(raw)
    if find_match:
        fields = [item.strip() for item in find_match.group(1).split(",")]
        address: int | None = None
        if fields:
            try:
                address = int(fields[0], 0)
            except ValueError:
                pass
        # IUVO Expert expects: AT+Find=<address>,<serial>,<type code>.
        # Type codes 1/2/3 are translated exactly like the original program.
        mac = fields[1] if len(fields) > 1 and fields[1] else None
        module_type = None
        if len(fields) > 2:
            module_type = _MODULE_TYPES.get(fields[2], fields[2] or None)
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
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False,
                )
                # .NET SerialPort (used by IUVO Expert) keeps both modem
                # control lines disabled. PySerial asserts them by default.
                self._serial.dtr = False
                self._serial.rts = False
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
                        continue
                    decoded = raw.decode("ascii", errors="replace").strip()
                    if decoded:
                        lines.append(decoded)
                return lines
            except (OSError, serial.SerialException) as err:
                self.close()
                raise IuvoConnectionError(str(err)) from err

    def discover(self, max_modules: int) -> list[str]:
        """Run the read-only discovery sequence used by IUVO Expert."""
        with self._lock:
            if not self.connected:
                self.connect()
            assert self._serial is not None
            try:
                self._serial.reset_input_buffer()
                self._serial.write(b"AT\r\n")
                self._serial.flush()
                # The gateway answers AT with OK and only then enters search
                # mode. IUVO Expert leaves roughly half a second here.
                time.sleep(0.5)

                lines: list[str] = []
                pending = bytearray()
                # Keep the port open for the whole scan. Real installations
                # can be noisy (time/temperature broadcasts share the bus),
                # so retry an address when its AT+Find response is lost.
                for address in range(0, max_modules + 1):
                    marker = f"AT+Find={address},"
                    for _attempt in range(3):
                        command = f"AT+Search=0,{address}\r\n".encode("ascii")
                        self._serial.write(command)
                        self._serial.flush()
                        reply_deadline = time.monotonic() + 0.35
                        while time.monotonic() < reply_deadline:
                            self._read_available(lines, pending)
                            if any(line.startswith(marker) for line in lines):
                                break
                            time.sleep(0.02)
                        if any(line.startswith(marker) for line in lines):
                            break

                deadline = time.monotonic() + max(1.5, self.timeout)
                while time.monotonic() < deadline:
                    self._read_available(lines, pending)
                    time.sleep(0.02)
                if pending:
                    decoded = pending.decode("ascii", errors="replace").strip()
                    if decoded:
                        lines.append(decoded)
                return lines
            except (OSError, serial.SerialException) as err:
                self.close()
                raise IuvoConnectionError(str(err)) from err

    def _read_available(self, lines: list[str], pending: bytearray) -> None:
        """Append all complete CR/LF-delimited frames currently buffered."""
        assert self._serial is not None
        waiting = self._serial.in_waiting
        if waiting:
            pending.extend(self._serial.read(waiting))
        while True:
            match = re.search(rb"[\r\n]", pending)
            if match is None:
                return
            raw = bytes(pending[: match.start()])
            del pending[: match.end()]
            while pending[:1] in (b"\r", b"\n"):
                del pending[:1]
            decoded = raw.decode("ascii", errors="replace").strip()
            if decoded:
                lines.append(decoded)
