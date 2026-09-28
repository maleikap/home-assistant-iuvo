"""Per-installation IUVO project profile support."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MomentaryOutput:
    """Configuration of one momentary relay output."""

    name: str
    pulse_seconds: float = 0.7


@dataclass(frozen=True)
class ProjectProfile:
    """Names and channel roles belonging to one installation only."""

    switch_names: dict[int, dict[int, str]] = field(default_factory=dict)
    cover_names: dict[int, dict[int, str]] = field(default_factory=dict)
    light_names: dict[int, dict[int, str]] = field(default_factory=dict)
    momentary_outputs: dict[tuple[int, int], MomentaryOutput] = field(default_factory=dict)

    def switch_name(self, address: int, channel: int) -> str:
        return self.switch_names.get(address, {}).get(channel, f"Wyjście {channel}")

    def cover_name(self, address: int, channel: int) -> str:
        return self.cover_names.get(address, {}).get(channel, f"Roleta {channel}")

    def light_name(self, address: int, channel: int) -> str:
        return self.light_names.get(address, {}).get(channel, f"Lampka {channel}")


EMPTY_PROFILE = ProjectProfile()


def _channel_names(value: Any) -> dict[int, dict[int, str]]:
    if not isinstance(value, dict):
        return {}
    result: dict[int, dict[int, str]] = {}
    for raw_address, raw_channels in value.items():
        if not isinstance(raw_channels, dict):
            continue
        try:
            address = int(raw_address)
        except (TypeError, ValueError):
            continue
        channels: dict[int, str] = {}
        for raw_channel, name in raw_channels.items():
            try:
                channel = int(raw_channel)
            except (TypeError, ValueError):
                continue
            clean_name = str(name).strip()
            if clean_name:
                channels[channel] = clean_name
        if channels:
            result[address] = channels
    return result


def _momentary_outputs(value: Any) -> dict[tuple[int, int], MomentaryOutput]:
    if not isinstance(value, dict):
        return {}
    result: dict[tuple[int, int], MomentaryOutput] = {}
    for key, config in value.items():
        try:
            address_text, channel_text = str(key).split(":", 1)
            address, channel = int(address_text), int(channel_text)
        except (TypeError, ValueError):
            continue
        if isinstance(config, str):
            name, pulse = config.strip(), 0.7
        elif isinstance(config, dict):
            name = str(config.get("name", "")).strip()
            try:
                pulse = float(config.get("pulse_seconds", 0.7))
            except (TypeError, ValueError):
                continue
        else:
            continue
        if name:
            result[(address, channel)] = MomentaryOutput(name=name, pulse_seconds=max(0.1, min(pulse, 10.0)))
    return result


def load_project_profile(path: str) -> ProjectProfile:
    if not path.strip():
        return EMPTY_PROFILE
    with Path(path).expanduser().open(encoding="utf-8") as profile_file:
        data = json.load(profile_file)
    if not isinstance(data, dict):
        raise ValueError("IUVO profile root must be a JSON object")
    return ProjectProfile(
        switch_names=_channel_names(data.get("switch_names")),
        cover_names=_channel_names(data.get("cover_names")),
        light_names=_channel_names(data.get("light_names")),
        momentary_outputs=_momentary_outputs(data.get("momentary_outputs")),
    )


def is_shutter_module(module_type: str | None) -> bool:
    return bool(module_type and "Roller Shutter" in module_type)
