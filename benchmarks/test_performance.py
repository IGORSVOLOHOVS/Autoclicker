"""How long the per-click decisions take.

This matters more here than the numbers suggest. The clicker asks for an
interval and a position before every single click, and the shortest interval
the interface allows is 1 ms - so anything these functions spend comes out of
the rhythm the user asked for. A decision that costs 50 microseconds is 5 % of
a 1 ms interval.
"""

from __future__ import annotations

import random

from autoclicker.core import estimate_run, format_duration, next_interval, next_position
from autoclicker.settings import ClickSettings, Preset, preset_to_settings

PLAIN = ClickSettings(interval_seconds=0.05)
JITTERED = ClickSettings(interval_seconds=0.05, random_interval_milliseconds=25)
SCATTERED = ClickSettings(interval_seconds=0.05, fixed_position=(1200, 800), random_offset_pixels=5)


def test_next_interval_without_jitter(benchmark) -> None:
    rng = random.Random(1)
    benchmark(next_interval, PLAIN, rng)


def test_next_interval_with_jitter(benchmark) -> None:
    rng = random.Random(1)
    benchmark(next_interval, JITTERED, rng)


def test_next_position_pinned(benchmark) -> None:
    rng = random.Random(1)
    benchmark(next_position, PLAIN.__class__(interval_seconds=0.05), rng, (640, 480))


def test_next_position_with_offset(benchmark) -> None:
    rng = random.Random(1)
    benchmark(next_position, SCATTERED, rng, (640, 480))


def test_preset_to_settings(benchmark) -> None:
    """Runs once when a preset is chosen, not per click - measured to show
    that it is nowhere near the per-click path."""
    preset = Preset(fixed_pos_enabled=True, coord_x="100", coord_y="200")
    benchmark(preset_to_settings, preset)


def test_estimate_run(benchmark) -> None:
    settings = ClickSettings(interval_seconds=0.05, click_count=10_000)
    benchmark(estimate_run, settings)


def test_format_duration(benchmark) -> None:
    benchmark(format_duration, 7500.0)
