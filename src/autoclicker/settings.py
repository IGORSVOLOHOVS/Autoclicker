"""What a click run is, and what a saved preset means.

Two shapes, on purpose.

``Preset`` is the file on disk: every value a string, the mouse button and the
click type written in Russian because that is what the interface shows. It has
been that shape since v1.0.0 and presets people already have must keep loading.

``ClickSettings`` is what the clicker actually runs on: numbers, enumerations,
and a validator that refuses a run that cannot do what it says. Nothing in here
imports Qt, pyautogui or keyboard, so all of it can be tested without a screen.

The conversion between the two lives here as well, which is the only place the
Russian labels are allowed to appear below the user interface.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class MouseButton(str, Enum):
    """The button pyautogui is asked for."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ClickType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    DRAG = "drag"


# The interface is Russian; the domain is not. This table is the border.
# See docs/decisions.md for why the interface stays Russian.
BUTTON_LABELS: dict[str, MouseButton] = {
    "Левая": MouseButton.LEFT,
    "Правая": MouseButton.RIGHT,
    "Средняя": MouseButton.MIDDLE,
}

CLICK_TYPE_LABELS: dict[str, ClickType] = {
    "Один клик": ClickType.SINGLE,
    "Двойной клик": ClickType.DOUBLE,
    "Перетаскивание": ClickType.DRAG,
}

LABELS_BY_BUTTON = {value: key for key, value in BUTTON_LABELS.items()}
LABELS_BY_CLICK_TYPE = {value: key for key, value in CLICK_TYPE_LABELS.items()}

DEFAULT_HOTKEYS: dict[str, str] = {"start": "F6", "stop": "F7", "get_pos": "F8"}


class SettingsError(ValueError):
    """A run that cannot do what it says it will."""


@dataclass(frozen=True)
class ClickSettings:
    """A validated click run.

    `click_count` of 0 means "until stopped", which is how the interface has
    always spelled it.
    """

    interval_seconds: float
    click_count: int = 0
    click_type: ClickType = ClickType.SINGLE
    mouse_button: MouseButton = MouseButton.LEFT
    drag_duration_seconds: float = 0.5
    fixed_position: tuple[int, int] | None = None
    random_offset_pixels: int = 0
    random_interval_milliseconds: int = 0

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.interval_seconds <= 0:
            raise SettingsError(f"interval must be positive, got {self.interval_seconds}")
        if self.click_count < 0:
            raise SettingsError(f"click count cannot be negative, got {self.click_count}")
        if self.drag_duration_seconds < 0:
            raise SettingsError("drag duration cannot be negative")
        if self.random_offset_pixels < 0:
            raise SettingsError("random offset cannot be negative")
        if self.random_interval_milliseconds < 0:
            raise SettingsError("random interval cannot be negative")

        # The original code added uniform(-range, range)/1000 to the interval
        # and then clamped a negative result to 1 ms. The clamp was silent, so
        # a range wider than the interval turned a deliberate 50 ms rhythm into
        # a 1000-clicks-per-second storm, and nothing said why. Refuse it here,
        # where both numbers are in front of the person who typed them.
        jitter_seconds = self.random_interval_milliseconds / 1000.0
        if jitter_seconds > self.interval_seconds:
            raise SettingsError(
                f"random interval +/-{self.random_interval_milliseconds} ms is wider than "
                f"the interval of {self.interval_seconds * 1000:.0f} ms, so some clicks "
                f"would land at the 1 ms floor instead of the rhythm asked for"
            )

    @property
    def is_unlimited(self) -> bool:
        return self.click_count == 0


@dataclass(frozen=True)
class Preset:
    """A preset file, exactly as it is on disk since v1.0.0."""

    interval: str = "100"
    interval_unit: str = "ms"
    click_count: str = "0"
    mouse_button: str = "Левая"
    click_type: str = "Один клик"
    drag_duration: str = "500"
    fixed_pos_enabled: bool = False
    coord_x: str = ""
    coord_y: str = ""
    random_offset_enabled: bool = False
    random_offset_range: str = "5"
    random_interval_enabled: bool = False
    random_interval_range: str = "10"
    hotkeys: dict[str, str] | None = None

    @classmethod
    def from_mapping(cls, document: dict[str, Any]) -> Preset:
        """Read a preset, filling in anything an older file did not have."""
        defaults = cls()
        return cls(
            interval=str(document.get("interval", defaults.interval)),
            interval_unit=str(document.get("interval_unit", defaults.interval_unit)),
            click_count=str(document.get("click_count", defaults.click_count)),
            mouse_button=str(document.get("mouse_button", defaults.mouse_button)),
            click_type=str(document.get("click_type", defaults.click_type)),
            drag_duration=str(document.get("drag_duration", defaults.drag_duration)),
            fixed_pos_enabled=bool(document.get("fixed_pos_enabled", False)),
            coord_x=str(document.get("coord_x", defaults.coord_x)),
            coord_y=str(document.get("coord_y", defaults.coord_y)),
            random_offset_enabled=bool(document.get("random_offset_enabled", False)),
            random_offset_range=str(
                document.get("random_offset_range", defaults.random_offset_range)
            ),
            random_interval_enabled=bool(document.get("random_interval_enabled", False)),
            random_interval_range=str(
                document.get("random_interval_range", defaults.random_interval_range)
            ),
            hotkeys=dict(document.get("hotkeys", DEFAULT_HOTKEYS)),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "interval": self.interval,
            "interval_unit": self.interval_unit,
            "click_count": self.click_count,
            "mouse_button": self.mouse_button,
            "click_type": self.click_type,
            "drag_duration": self.drag_duration,
            "fixed_pos_enabled": self.fixed_pos_enabled,
            "coord_x": self.coord_x,
            "coord_y": self.coord_y,
            "random_offset_enabled": self.random_offset_enabled,
            "random_offset_range": self.random_offset_range,
            "random_interval_enabled": self.random_interval_enabled,
            "random_interval_range": self.random_interval_range,
            "hotkeys": self.hotkeys if self.hotkeys is not None else dict(DEFAULT_HOTKEYS),
        }


def load_preset(path: Path) -> Preset:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SettingsError(f"{path} does not hold a preset")
    return Preset.from_mapping(document)


def save_preset(preset: Preset, path: Path) -> None:
    path.write_text(
        json.dumps(preset.to_mapping(), indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _whole_number(text: str, field: str) -> int:
    try:
        return int(text.strip())
    except (AttributeError, ValueError) as error:
        raise SettingsError(f"{field} must be a whole number, got {text!r}") from error


def preset_to_settings(preset: Preset) -> ClickSettings:
    """Turn a preset into a run, or say exactly which field is wrong.

    This is where a file written by hand meets the validator, so the message
    has to name the field - "invalid literal for int()" is not something to put
    in front of somebody who was editing JSON in Notepad.
    """
    interval = _whole_number(preset.interval, "interval")
    interval_seconds = interval if preset.interval_unit == "s" else interval / 1000.0

    button = BUTTON_LABELS.get(preset.mouse_button)
    if button is None:
        raise SettingsError(
            f"unknown mouse button {preset.mouse_button!r}; "
            f"expected one of {', '.join(BUTTON_LABELS)}"
        )

    click_type = CLICK_TYPE_LABELS.get(preset.click_type)
    if click_type is None:
        raise SettingsError(
            f"unknown click type {preset.click_type!r}; "
            f"expected one of {', '.join(CLICK_TYPE_LABELS)}"
        )

    position: tuple[int, int] | None = None
    if preset.fixed_pos_enabled:
        position = (
            _whole_number(preset.coord_x, "coord_x"),
            _whole_number(preset.coord_y, "coord_y"),
        )

    offset = (
        _whole_number(preset.random_offset_range, "random_offset_range")
        if preset.random_offset_enabled
        else 0
    )
    jitter = (
        _whole_number(preset.random_interval_range, "random_interval_range")
        if preset.random_interval_enabled
        else 0
    )

    return ClickSettings(
        interval_seconds=interval_seconds,
        click_count=_whole_number(preset.click_count, "click_count"),
        click_type=click_type,
        mouse_button=button,
        drag_duration_seconds=_whole_number(preset.drag_duration, "drag_duration") / 1000.0,
        fixed_position=position,
        random_offset_pixels=offset,
        random_interval_milliseconds=jitter,
    )
