"""The two numbers the clicker asks for on every iteration.

Every test seeds its own `random.Random`, so a failure here is reproducible
rather than something that shows up one run in fifty.
"""

from __future__ import annotations

import random

import pytest

from autoclicker.core import (
    MINIMUM_INTERVAL_SECONDS,
    estimate_run,
    format_duration,
    next_interval,
    next_position,
    should_stop,
)
from autoclicker.settings import ClickSettings, ClickType


def settings(**overrides: object) -> ClickSettings:
    base: dict[str, object] = {"interval_seconds": 0.1}
    base.update(overrides)
    return ClickSettings(**base)  # type: ignore[arg-type]


# ------------------------------------------------------------------ interval


def test_without_jitter_the_interval_is_exactly_what_was_asked_for() -> None:
    run = settings(interval_seconds=0.25)
    rng = random.Random(1)
    assert [next_interval(run, rng) for _ in range(5)] == [0.25] * 5


def test_jitter_stays_inside_the_range_it_was_given() -> None:
    run = settings(interval_seconds=0.1, random_interval_milliseconds=40)
    rng = random.Random(7)

    values = [next_interval(run, rng) for _ in range(2000)]

    assert min(values) >= 0.06 - 1e-9
    assert max(values) <= 0.14 + 1e-9
    # Symmetric jitter, so the mean lands on the interval itself.
    assert sum(values) / len(values) == pytest.approx(0.1, abs=0.005)


def test_the_same_seed_gives_the_same_sequence() -> None:
    run = settings(random_interval_milliseconds=50)
    first = [next_interval(run, random.Random(42)) for _ in range(3)]
    second = [next_interval(run, random.Random(42)) for _ in range(3)]
    assert first == second


def test_the_interval_never_goes_below_the_floor() -> None:
    """Validation makes this unreachable through settings; arithmetic is not a
    reason to trust it."""
    run = settings(interval_seconds=0.05, random_interval_milliseconds=50)
    rng = random.Random(3)
    assert all(next_interval(run, rng) >= MINIMUM_INTERVAL_SECONDS for _ in range(500))


# ------------------------------------------------------------------ position


def test_without_an_offset_the_position_is_left_alone() -> None:
    run = settings(fixed_position=(100, 200))
    assert next_position(run, random.Random(1), (5, 5)) == (100, 200)


def test_without_a_fixed_position_the_cursor_is_the_starting_point() -> None:
    run = settings()
    assert next_position(run, random.Random(1), (640, 480)) == (640, 480)


def test_the_offset_applies_with_or_without_a_fixed_position() -> None:
    """v1.0.0 computed a scatter and then clicked wherever the pointer was
    unless a fixed position was set. The offset is the reason somebody turns it
    on, so it has to apply to the cursor too."""
    pinned = settings(fixed_position=(300, 300), random_offset_pixels=5)
    floating = settings(random_offset_pixels=5)

    pinned_points = {next_position(pinned, random.Random(i), (0, 0)) for i in range(50)}
    floating_points = {next_position(floating, random.Random(i), (300, 300)) for i in range(50)}

    assert len(pinned_points) > 1
    assert len(floating_points) > 1
    for x, y in pinned_points | floating_points:
        assert 295 <= x <= 305
        assert 295 <= y <= 305


def test_the_offset_can_reach_every_corner_of_its_square() -> None:
    run = settings(fixed_position=(0, 0), random_offset_pixels=2)
    seen = {next_position(run, random.Random(seed), (0, 0)) for seed in range(400)}
    assert (-2, -2) in seen
    assert (2, 2) in seen


# ---------------------------------------------------------------- stopping


def test_a_count_of_zero_never_stops_on_its_own() -> None:
    run = settings(click_count=0)
    assert not should_stop(run, 0)
    assert not should_stop(run, 1_000_000)


def test_a_run_stops_on_the_click_it_was_asked_for() -> None:
    run = settings(click_count=3)
    assert not should_stop(run, 2)
    assert should_stop(run, 3)
    assert should_stop(run, 4)


# ---------------------------------------------------------------- estimates


def test_an_unlimited_run_has_no_estimate() -> None:
    assert estimate_run(settings(click_count=0)) is None


def test_the_estimate_brackets_the_run() -> None:
    run = settings(interval_seconds=0.1, click_count=100, random_interval_milliseconds=20)
    estimate = estimate_run(run)
    assert estimate is not None

    assert estimate.clicks == 100
    assert estimate.expected_seconds == pytest.approx(10.0)
    assert estimate.shortest_seconds == pytest.approx(8.0)
    assert estimate.longest_seconds == pytest.approx(12.0)


def test_a_drag_costs_its_own_duration_on_every_click() -> None:
    run = settings(
        interval_seconds=0.1,
        click_count=10,
        click_type=ClickType.DRAG,
        drag_duration_seconds=0.4,
    )
    estimate = estimate_run(run)
    assert estimate is not None
    assert estimate.expected_seconds == pytest.approx(5.0)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0.05, "50 ms"),
        (0.999, "999 ms"),
        (1.0, "1.0 s"),
        (42.5, "42.5 s"),
        (60, "1 min 0 s"),
        (185, "3 min 5 s"),
        (3600, "1 h 0 min"),
        (7500, "2 h 5 min"),
    ],
)
def test_durations_are_written_for_a_person(seconds: float, expected: str) -> None:
    assert format_duration(seconds) == expected
