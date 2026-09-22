"""Constants for the IUVO integration."""

from __future__ import annotations

DOMAIN = "iuvo"
PLATFORMS = ["binary_sensor", "button", "cover", "light", "sensor", "switch"]

CONF_MAX_MODULES = "max_modules"
CONF_POLL_INTERVAL = "poll_interval"
CONF_RESPONSE_TIMEOUT = "response_timeout"

DEFAULT_BAUDRATE = 115200
DEFAULT_MAX_MODULES = 32
DEFAULT_POLL_INTERVAL = 5
DEFAULT_RESPONSE_TIMEOUT = 0.35

MIN_MODULES = 1
MAX_MODULES = 32

STATE_INPUTS = "inputs"
STATE_OUTPUTS = "outputs"
STATE_LAMPS = "lamps"
STATE_SHUTTERS = "shutters"

ATTR_COMMAND = "command"
SERVICE_SEND_COMMAND = "send_command"
SERVICE_RESCAN = "rescan"


def module_key(address: int) -> str:
    """Return stable module key."""
    return f"module_{address}"
