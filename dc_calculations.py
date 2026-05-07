"""Calculation helpers for Adaptive Day Cycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

PHASE_NIGHT = "night"
PHASE_DAWN = "dawn"
PHASE_MORNING = "morning"
PHASE_AFTERNOON = "afternoon"
PHASE_DUSK = "dusk"
PHASE_EVENING = "evening"

PHASE_ORDER = [
    PHASE_NIGHT,
    PHASE_DAWN,
    PHASE_MORNING,
    PHASE_AFTERNOON,
    PHASE_DUSK,
    PHASE_EVENING,
]

DAYTIME_PHASE_ORDER = [
    PHASE_DAWN,
    PHASE_MORNING,
    PHASE_AFTERNOON,
    PHASE_DUSK,
    PHASE_EVENING,
    PHASE_NIGHT,
]

DEFAULT_DAWN_OFFSET = timedelta(hours=0)
DEFAULT_MORNING_OFFSET = timedelta(hours=2.5)
DEFAULT_DUSK_OFFSET = timedelta(hours=2.5)
DEFAULT_EVENING_OFFSET = timedelta(hours=0)

WEATHER_ADJUSTMENTS = {
    "sunny": 0,
    "clear-night": 0,
    "partlycloudy": 15,
    "cloudy": 45,
    "fog": 60,
    "rainy": 75,
    "pouring": 105,
    "lightning": 120,
    "lightning-rainy": 135,
    "snowy": 30,
    "snowy-rainy": 60,
}


@dataclass(frozen=True)
class EnvironmentalConditions:
    """Normalized environmental conditions for a specific target time."""

    condition: str | None = None
    cloud_coverage: float | None = None
    precipitation: float | None = None
    illuminance: float | None = None


@dataclass(frozen=True)
class DayCycleData:
    """Calculated day cycle state and phase transition times."""

    current_phase: str
    next_phase: str
    next_transition: datetime
    phase_starts: dict[str, datetime]
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime


def combine_local_time(reference: datetime, local_time: time) -> datetime:
    """Combine a reference date with a local time, preserving timezone."""

    return datetime.combine(
        reference.date(),
        local_time,
        tzinfo=reference.tzinfo,
    )


def calculate_solar_noon(sunrise: datetime, sunset: datetime) -> datetime:
    """Calculate solar noon as the midpoint between sunrise and sunset."""

    return sunrise + ((sunset - sunrise) / 2)




def calculate_phase_adjustment(
    target_time: datetime,
    conditions: EnvironmentalConditions | None = None,
) -> timedelta:
    """Calculate a phase-specific environmental adjustment.

    The adjustment system is intentionally timestamp-driven. The supplied
    target_time represents the calculated raw phase boundary before any
    environmental adjustments are applied.

    Environmental conditions should therefore be evaluated relative to the
    expected conditions at the actual phase transition time rather than the
    current time.
    """

    _ = target_time

    if conditions is None:
        return timedelta(0)

    if conditions.condition is None:
        return timedelta(0)

    base_adjustment = WEATHER_ADJUSTMENTS.get(
        conditions.condition,
        0,
    )

    return timedelta(minutes=base_adjustment)


def calculate_daycycle(
    now: datetime,
    sunrise: datetime,
    sunset: datetime,
    earliest_dawn: time,
    night_start: time,
    morning_conditions: EnvironmentalConditions | None = None,
    dusk_conditions: EnvironmentalConditions | None = None,
    evening_conditions: EnvironmentalConditions | None = None,
) -> DayCycleData:
    """Calculate day phase boundaries and current state.

    The model is boundary-driven: each phase only has a start time. The end of
    each phase is determined by the start of the next phase.
    """

    solar_noon = calculate_solar_noon(sunrise, sunset)

    earliest_dawn_dt = combine_local_time(now, earliest_dawn)
    night_start_dt = combine_local_time(now, night_start)

    # Calculate raw phase anchors before environmental adjustments.
    raw_dawn_start = max(
        earliest_dawn_dt,
        sunrise + DEFAULT_DAWN_OFFSET,
    )

    raw_morning_start = sunrise + DEFAULT_MORNING_OFFSET
    raw_afternoon_start = solar_noon
    raw_dusk_start = sunset - DEFAULT_DUSK_OFFSET
    raw_evening_start = sunset + DEFAULT_EVENING_OFFSET

    dawn_start = raw_dawn_start

    morning_start = (
        raw_morning_start
        + calculate_phase_adjustment(
            raw_morning_start,
            morning_conditions,
        )
    )

    afternoon_start = (
        raw_afternoon_start
        + calculate_phase_adjustment(
            raw_afternoon_start,
        )
    )

    dusk_start = (
        raw_dusk_start
        - calculate_phase_adjustment(
            raw_dusk_start,
            dusk_conditions,
        )
    )

    evening_start = (
        raw_evening_start
        - calculate_phase_adjustment(
            raw_evening_start,
            evening_conditions,
        )
    )

    # If night_start is earlier than evening_start, it belongs to the next day.
    if night_start_dt <= evening_start:
        night_start_dt += timedelta(days=1)

    phase_starts = {
        PHASE_DAWN: dawn_start,
        PHASE_MORNING: morning_start,
        PHASE_AFTERNOON: afternoon_start,
        PHASE_DUSK: dusk_start,
        PHASE_EVENING: evening_start,
        PHASE_NIGHT: night_start_dt,
    }

    current_phase = get_current_phase(now, phase_starts)
    next_phase, next_transition = get_next_transition(now, phase_starts)

    return DayCycleData(
        current_phase=current_phase,
        next_phase=next_phase,
        next_transition=next_transition,
        phase_starts=phase_starts,
        sunrise=sunrise,
        sunset=sunset,
        solar_noon=solar_noon,
    )


def get_current_phase(now: datetime, phase_starts: dict[str, datetime]) -> str:
    """Return the active phase for the supplied time."""

    ordered_starts = sorted(
        phase_starts.items(),
        key=lambda item: item[1],
    )

    current_phase = PHASE_NIGHT

    for phase, start_time in ordered_starts:
        if now >= start_time:
            current_phase = phase
        else:
            break

    return current_phase


def get_next_transition(
    now: datetime,
    phase_starts: dict[str, datetime],
) -> tuple[str, datetime]:
    """Return the next phase and its transition time."""

    future_transitions = sorted(
        (
            (phase, start_time)
            for phase, start_time in phase_starts.items()
            if start_time > now
        ),
        key=lambda item: item[1],
    )

    if future_transitions:
        return future_transitions[0]

    # Fallback: this should normally only happen if stale phase data is reused
    # after the calculated cycle has fully passed.
    next_dawn = phase_starts[PHASE_DAWN] + timedelta(days=1)
    return PHASE_DAWN, next_dawn