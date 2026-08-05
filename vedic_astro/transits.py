"""Gochara (transit) analysis: comparing current planetary positions to a
natal chart, plus Sade Sati -- Saturn's transit through the 12th, 1st, and
2nd houses counted from the natal Moon.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .chart import NatalChart
from .constants import DEFAULT_AYANAMSA, MOON, SATURN
from .ephemeris import get_planet_positions
from .util import house_from_sign, rashi_index, rashi_name

SADE_SATI_PHASES = {
    12: "Rising (Arohi)",
    1: "Peak (Chudasi)",
    2: "Setting (Vaakri)",
}

SADE_SATI_PHASE_BLURBS = {
    "Rising (Arohi)": (
        "Saturn is transiting the sign before your natal Moon (the 12th house from it) -- "
        "traditionally the build-up phase, as its effects begin to intensify."
    ),
    "Peak (Chudasi)": (
        "Saturn is transiting the same sign as your natal Moon (the 1st house from it) -- "
        "traditionally considered the most intense phase of Sade Sati."
    ),
    "Setting (Vaakri)": (
        "Saturn is transiting the sign after your natal Moon (the 2nd house from it) -- "
        "traditionally the winding-down phase, as its effects gradually ease off."
    ),
}

SADE_SATI_OVERVIEW_BLURB = (
    "Sade Sati is Saturn's roughly 7.5-year transit through the signs before, on, and "
    "after your natal Moon -- it happens about twice in an average lifetime."
)


@dataclass
class TransitPlacement:
    name: str
    longitude: float
    rashi: str
    house_from_moon: int
    house_from_lagna: int
    retrograde: bool


@dataclass
class SadeSatiStatus:
    active: bool
    phase: str | None  # "Rising (Arohi)" / "Peak (Chudasi)" / "Setting (Vaakri)" / None
    house_from_moon: int | None  # 12, 1, or 2 when active
    saturn_rashi: str
    next_transition: datetime | None  # approx. date Saturn next crosses a sign boundary


def compute_transits(
    natal_chart: NatalChart,
    at_dt: datetime | None = None,
    ayanamsa_name: str = DEFAULT_AYANAMSA,
) -> dict[str, TransitPlacement]:
    """Current sidereal positions of all grahas, with houses relative to the
    natal Moon (traditional Vedic gochara reference point) and natal Lagna.
    """
    if at_dt is None:
        at_dt = datetime.now(timezone.utc)

    moon_longitude = natal_chart.planets[MOON].longitude
    lagna_longitude = natal_chart.ascendant_longitude

    raw_positions = get_planet_positions(at_dt, ayanamsa_name)
    return {
        name: TransitPlacement(
            name=name,
            longitude=pos.longitude,
            rashi=rashi_name(pos.longitude),
            house_from_moon=house_from_sign(pos.longitude, moon_longitude),
            house_from_lagna=house_from_sign(pos.longitude, lagna_longitude),
            retrograde=pos.retrograde,
        )
        for name, pos in raw_positions.items()
    }


def _find_next_rashi_change(
    planet_name: str,
    from_dt: datetime,
    ayanamsa_name: str,
    coarse_step_days: int = 5,
    max_days: int = 365 * 5,
) -> datetime | None:
    """Approximate next time `planet_name` crosses into a different sidereal
    sign, searched forward from `from_dt`.

    Coarse forward stepping, then bisected to ~1-hour precision. Note: during
    a retrograde loop a planet can dip back across a boundary and return, so
    this finds the *next* crossing, not necessarily a final exit.
    """
    start_positions = get_planet_positions(from_dt, ayanamsa_name)
    start_sign = rashi_index(start_positions[planet_name].longitude)

    prev_dt = from_dt
    dt = from_dt
    elapsed = 0
    while elapsed < max_days:
        dt = dt + timedelta(days=coarse_step_days)
        elapsed += coarse_step_days
        sign = rashi_index(get_planet_positions(dt, ayanamsa_name)[planet_name].longitude)
        if sign != start_sign:
            lo, hi = prev_dt, dt
            for _ in range(20):  # bisect down to ~hour-level precision
                mid = lo + (hi - lo) / 2
                mid_sign = rashi_index(get_planet_positions(mid, ayanamsa_name)[planet_name].longitude)
                if mid_sign == start_sign:
                    lo = mid
                else:
                    hi = mid
            return hi
        prev_dt = dt
    return None


def compute_sade_sati(
    natal_chart: NatalChart,
    at_dt: datetime | None = None,
    ayanamsa_name: str = DEFAULT_AYANAMSA,
) -> SadeSatiStatus:
    if at_dt is None:
        at_dt = datetime.now(timezone.utc)

    moon_longitude = natal_chart.planets[MOON].longitude
    saturn_position = get_planet_positions(at_dt, ayanamsa_name)[SATURN]
    house = house_from_sign(saturn_position.longitude, moon_longitude)

    phase = SADE_SATI_PHASES.get(house)
    next_transition = _find_next_rashi_change(SATURN, at_dt, ayanamsa_name)

    return SadeSatiStatus(
        active=phase is not None,
        phase=phase,
        house_from_moon=house if phase else None,
        saturn_rashi=rashi_name(saturn_position.longitude),
        next_transition=next_transition,
    )
