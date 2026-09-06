"""When to click, and where.

The two numbers the clicker asks for on every iteration, and the decision of
when to stop. Pure arithmetic over a `ClickSettings` and a `random.Random`,
which is what makes it testable: hand it a seeded generator and the sequence is
the same every time.

The thread that calls this, the mouse it drives and the window it lives in are
all somewhere else.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from autoclicker.settings import ClickSettings

# The floor the original code clamped to. Settings validation refuses a jitter
# wider than the interval, so this is now only reachable through arithmetic
# rounding rather than through a misconfiguration.
MINIMUM_INTERVAL_SECONDS = 0.001


def next_interval(settings: ClickSettings, rng: random.Random) -> float:
    """How long to sleep before the next click.

    Uniform jitter either side of the interval, in milliseconds, exactly as
    v1.0.0 did it. The difference is that the settings can no longer ask for a
    jitter wider than the interval, so the result no longer needs a clamp to
    stay sane - the floor below is arithmetic hygiene, not a policy.
    """
    if settings.random_interval_milliseconds == 0:
        return settings.interval_seconds

    jitter = rng.uniform(
        -settings.random_interval_milliseconds, settings.random_interval_milliseconds
    )
    return max(settings.interval_seconds + jitter / 1000.0, MINIMUM_INTERVAL_SECONDS)


def next_position(
    settings: ClickSettings, rng: random.Random, cursor: tuple[int, int]
) -> tuple[int, int]:
    """Where the next click lands.

    `cursor` is where the pointer is now, used when the run is not pinned to a
    fixed position. The random offset applies to both, because a person asking
    for scatter wants it wherever they are clicking.
    """
    x, y = settings.fixed_position if settings.fixed_position is not None else cursor

    if settings.random_offset_pixels > 0:
        spread = settings.random_offset_pixels
        x += rng.randint(-spread, spread)
        y += rng.randint(-spread, spread)

    return x, y


def should_stop(settings: ClickSettings, clicks_done: int) -> bool:
    """True once the run has done what it was asked for."""
    if settings.is_unlimited:
        return False
    return clicks_done >= settings.click_count


@dataclass(frozen=True)
class RunEstimate:
    """What a run will cost, before it starts."""

    clicks: int
    expected_seconds: float
    shortest_seconds: float
    longest_seconds: float


def estimate_run(settings: ClickSettings) -> RunEstimate | None:
    """How long this run takes, or None when it never ends.

    The jitter is symmetric, so the expectation is the plain interval; the
    bounds are what makes it worth printing, because "between 4 and 6 minutes"
    is a different decision from "about 5".
    """
    if settings.is_unlimited:
        return None

    clicks = settings.click_count
    per_click = settings.interval_seconds
    if settings.click_type == settings.click_type.DRAG:
        per_click += settings.drag_duration_seconds

    jitter = settings.random_interval_milliseconds / 1000.0
    return RunEstimate(
        clicks=clicks,
        expected_seconds=clicks * per_click,
        shortest_seconds=clicks * max(per_click - jitter, MINIMUM_INTERVAL_SECONDS),
        longest_seconds=clicks * (per_click + jitter),
    )


def format_duration(seconds: float) -> str:
    """A duration a person reads at a glance, not a float."""
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, remainder = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes} min {remainder} s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"
