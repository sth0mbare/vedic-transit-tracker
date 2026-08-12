"""Weekly horoscope: a data-driven summary of the coming week's notable
transits, built entirely from the same primitives as the other calculators
(Moon's sign each day, and which grahas are about to change sign) -- not
fabricated predictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from .chart import NatalChart
from .constants import DEFAULT_AYANAMSA, MOON
from .ephemeris import get_planet_positions
from .transits import TransitPlacement
from .util import house_from_sign, rashi_name

WEEK_DAYS = 7


@dataclass
class MoonDay:
    start: date
    rashi: str
    house_from_moon: int  # relative to the natal Moon


@dataclass
class WeeklyHoroscope:
    start: date
    end: date
    moon_journey: list[MoonDay]  # one entry per rashi change, deduped across consecutive days
    upcoming_sign_changes: dict[str, TransitPlacement]  # grahas changing sign within the week


def compute_moon_journey(
    natal_chart: NatalChart, from_dt: datetime, ayanamsa_name: str = DEFAULT_AYANAMSA, days: int = WEEK_DAYS
) -> list[MoonDay]:
    """Moon's rashi across the week, one entry per calendar day, collapsed so
    consecutive days in the same rashi share a single entry.
    """
    natal_moon_longitude = natal_chart.planets[MOON].longitude
    entries: list[MoonDay] = []
    last_rashi = None
    for i in range(days):
        day_dt = from_dt + timedelta(days=i)
        moon_longitude = get_planet_positions(day_dt, ayanamsa_name)[MOON].longitude
        rashi = rashi_name(moon_longitude)
        if rashi != last_rashi:
            entries.append(
                MoonDay(
                    start=day_dt.date(),
                    rashi=rashi,
                    house_from_moon=house_from_sign(moon_longitude, natal_moon_longitude),
                )
            )
            last_rashi = rashi
    return entries


def compute_weekly_horoscope(
    natal_chart: NatalChart,
    transits: dict[str, TransitPlacement],
    start_dt: datetime | None = None,
    ayanamsa_name: str = DEFAULT_AYANAMSA,
) -> WeeklyHoroscope:
    """Builds the week-ahead summary. `transits` should be the same
    already-computed current-transits dict the Live Transits table uses
    (each placement's next_sign_change is reused here rather than
    recomputed) so both stay consistent with each other.
    """
    if start_dt is None:
        start_dt = datetime.now(timezone.utc)
    end_dt = start_dt + timedelta(days=WEEK_DAYS)

    moon_journey = compute_moon_journey(natal_chart, start_dt, ayanamsa_name)

    upcoming_sign_changes = {
        name: t
        for name, t in transits.items()
        if t.next_sign_change is not None and start_dt <= t.next_sign_change <= end_dt
    }

    return WeeklyHoroscope(
        start=start_dt.date(),
        end=end_dt.date(),
        moon_journey=moon_journey,
        upcoming_sign_changes=upcoming_sign_changes,
    )
