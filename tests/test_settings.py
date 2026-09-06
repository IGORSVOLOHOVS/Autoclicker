"""What a preset means, and what the validator refuses.

The preset format has not changed since v1.0.0 and files people already have
must keep loading, so the first test here reads the one that ships with the
repository rather than a fixture invented for the occasion.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoclicker.settings import (
    ClickSettings,
    ClickType,
    MouseButton,
    Preset,
    SettingsError,
    load_preset,
    preset_to_settings,
    save_preset,
)

REPOSITORY = Path(__file__).resolve().parent.parent


def test_the_preset_that_ships_with_the_repository_still_loads() -> None:
    preset = load_preset(REPOSITORY / "configs" / "Dota2Pudge.json")
    settings = preset_to_settings(preset)

    assert settings.interval_seconds == pytest.approx(0.05)
    assert settings.click_count == 0
    assert settings.is_unlimited
    assert settings.click_type is ClickType.SINGLE
    assert settings.mouse_button is MouseButton.LEFT
    assert settings.fixed_position == (3057, 1654)
    assert settings.random_offset_pixels == 1
    assert settings.random_interval_milliseconds == 25


def test_a_preset_survives_a_round_trip(tmp_path: Path) -> None:
    original = load_preset(REPOSITORY / "configs" / "Dota2Pudge.json")
    path = tmp_path / "copy.json"
    save_preset(original, path)

    assert load_preset(path) == original
    # And it is still readable as plain JSON with the Russian labels intact.
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["mouse_button"] == "Левая"


def test_an_old_preset_without_hotkeys_gets_the_defaults() -> None:
    preset = Preset.from_mapping({"interval": "200", "interval_unit": "ms"})
    assert preset.hotkeys == {"start": "F6", "stop": "F7", "get_pos": "F8"}
    assert preset_to_settings(preset).interval_seconds == pytest.approx(0.2)


def test_seconds_and_milliseconds_are_both_understood() -> None:
    in_milliseconds = preset_to_settings(Preset(interval="250", interval_unit="ms"))
    in_seconds = preset_to_settings(Preset(interval="2", interval_unit="s"))

    assert in_milliseconds.interval_seconds == pytest.approx(0.25)
    assert in_seconds.interval_seconds == pytest.approx(2.0)


def test_disabled_options_do_not_leak_their_values() -> None:
    """A range typed and then switched off must not affect the run."""
    preset = Preset(
        random_offset_enabled=False,
        random_offset_range="40",
        random_interval_enabled=False,
        random_interval_range="90",
        fixed_pos_enabled=False,
        coord_x="10",
        coord_y="20",
    )
    settings = preset_to_settings(preset)

    assert settings.random_offset_pixels == 0
    assert settings.random_interval_milliseconds == 0
    assert settings.fixed_position is None


@pytest.mark.parametrize(
    ("field", "preset"),
    [
        ("interval", Preset(interval="not a number")),
        ("click_count", Preset(click_count="")),
        ("coord_x", Preset(fixed_pos_enabled=True, coord_x="left", coord_y="20")),
        ("drag_duration", Preset(drag_duration="1.5")),
    ],
)
def test_a_field_that_is_not_a_number_names_itself(field: str, preset: Preset) -> None:
    with pytest.raises(SettingsError, match=field):
        preset_to_settings(preset)


def test_an_unknown_label_says_what_was_expected() -> None:
    with pytest.raises(SettingsError, match="unknown mouse button"):
        preset_to_settings(Preset(mouse_button="Middle"))
    with pytest.raises(SettingsError, match="unknown click type"):
        preset_to_settings(Preset(click_type="Triple"))


def test_a_zero_interval_is_refused() -> None:
    with pytest.raises(SettingsError, match="interval must be positive"):
        ClickSettings(interval_seconds=0)


def test_negative_values_are_refused() -> None:
    with pytest.raises(SettingsError, match="click count"):
        ClickSettings(interval_seconds=0.1, click_count=-1)
    with pytest.raises(SettingsError, match="drag duration"):
        ClickSettings(interval_seconds=0.1, drag_duration_seconds=-1)
    with pytest.raises(SettingsError, match="random offset"):
        ClickSettings(interval_seconds=0.1, random_offset_pixels=-1)
    with pytest.raises(SettingsError, match="random interval"):
        ClickSettings(interval_seconds=0.1, random_interval_milliseconds=-1)


def test_jitter_wider_than_the_interval_is_refused_rather_than_clamped() -> None:
    """The fault this refactoring exists for.

    v1.0.0 added the jitter, saw a negative sleep, clamped it to 1 ms and said
    nothing. A 50 ms rhythm with a 200 ms spread became a click storm, and the
    only symptom was that it felt wrong.
    """
    with pytest.raises(SettingsError, match="wider than the interval"):
        ClickSettings(interval_seconds=0.05, random_interval_milliseconds=200)

    # Equal is allowed: the worst case is exactly zero, not negative.
    ClickSettings(interval_seconds=0.2, random_interval_milliseconds=200)


def test_a_broken_preset_file_is_reported_not_guessed(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(SettingsError, match="does not hold a preset"):
        load_preset(path)
