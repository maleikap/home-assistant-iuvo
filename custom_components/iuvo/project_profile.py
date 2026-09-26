"""Names imported from the Knop budynek Finisch IUVO Expert project."""

from __future__ import annotations

SWITCH_NAMES: dict[int, dict[int, str]] = {
    2: {1: "Lampe Lager Mitte", 2: "Lampe Lager"},
    3: {1: "Lampe Bad", 3: "Beleuchtung Flur"},
    4: {
        1: "Beleuchtung Zimmer 1",
        2: "Beleuchtung Zimmer 2",
        3: "Beleuchtung Zimmer 3",
        6: "Beleuchtung Küche",
    },
    7: {1: "Beleuchtung WC 1", 2: "Beleuchtung WC 2"},
    8: {6: "Beleuchtung Abstellraum"},
}

# Outputs renamed by the user in Home Assistant as gate controls. Keep them
# in the switch platform (and keep their unique IDs) so custom names and
# dashboard references survive upgrades, but operate them as short pulses.
MOMENTARY_OUTPUTS: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 5),  # Brama wjazdowa
        (2, 6),  # Brama Lager
    }
)

COVER_NAMES: dict[int, dict[int, str]] = {
    5: {
        1: "Jalousie Küche",
        2: "Jalousie Zimmer 1",
        3: "Jalousie Zimmer 3",
    },
    6: {
        1: "Jalousie Bad",
        2: "Jalousie Zimmer 2",
        3: "Jalousie Wohnzimmer 1",
        4: "Jalousie Wohnzimmer 2",
    },
    10: {
        1: "Jalousie 3",
        2: "Fenster 3",
        3: "Jalousie 2",
        4: "Fenster 2",
    },
    12: {2: "Jalousie Lager"},
}


def is_shutter_module(module_type: str | None) -> bool:
    """Return whether a discovered module is a Roller Shutter0804."""
    return bool(module_type and "Roller Shutter" in module_type)
