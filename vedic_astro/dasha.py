"""Vimshottari Dasha: the 120-year cycle of planetary periods used for timing
predictions in Vedic astrology.

The birth Moon's position within its nakshatra fixes how far into the first
(birth) mahadasha the native already was at birth -- that fraction is reused
directly to find the true start of that mahadasha (which precedes birth),
which in turn is what antardasha (sub-period) proportions are computed from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .constants import DASHA_LORD_CYCLE, DASHA_YEARS, DEG_PER_NAKSHATRA, NAKSHATRA_LORDS
from .util import nakshatra_index

DAYS_PER_YEAR = 365.2425  # Gregorian mean year; standard approximation for dasha math

MAX_MAHADASHA_ENTRIES = 30  # ~3+ full 120-year cycles worth of entries, generous safety cap

DASHA_OVERVIEW_BLURB = (
    "Vimshottari Dasha divides a 120-year cycle into planetary mahadashas "
    "(major periods) and antardashas (sub-periods within them), fixed by your "
    "Moon's position at birth -- a common framework for timing predictions "
    "in Vedic astrology."
)


@dataclass
class DashaPeriod:
    lord: str
    start: datetime
    end: datetime

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt < self.end


@dataclass
class DashaStatus:
    mahadasha: DashaPeriod
    antardasha: DashaPeriod
    next_mahadasha: DashaPeriod
    next_antardasha: DashaPeriod


def _years_to_timedelta(years: float) -> timedelta:
    return timedelta(days=years * DAYS_PER_YEAR)


def _birth_nakshatra_lord_and_fraction(moon_longitude: float) -> tuple[str, float]:
    idx = nakshatra_index(moon_longitude)
    lord = NAKSHATRA_LORDS[idx]
    fraction_elapsed = (moon_longitude % DEG_PER_NAKSHATRA) / DEG_PER_NAKSHATRA
    return lord, fraction_elapsed


def _mahadasha_sequence(birth_dt_utc: datetime, moon_longitude: float, until_dt: datetime) -> list[DashaPeriod]:
    """Full mahadasha spans, starting from the TRUE start of the birth
    mahadasha (which is before birth), through at least `until_dt`.
    """
    birth_lord, fraction_elapsed = _birth_nakshatra_lord_and_fraction(moon_longitude)
    full_years = DASHA_YEARS[birth_lord]

    true_start = birth_dt_utc - _years_to_timedelta(full_years * fraction_elapsed)
    true_end = true_start + _years_to_timedelta(full_years)

    periods = [DashaPeriod(lord=birth_lord, start=true_start, end=true_end)]

    cycle_idx = DASHA_LORD_CYCLE.index(birth_lord)
    current_start = true_end
    i = 1
    while current_start <= until_dt and len(periods) < MAX_MAHADASHA_ENTRIES:
        lord = DASHA_LORD_CYCLE[(cycle_idx + i) % 9]
        years = DASHA_YEARS[lord]
        current_end = current_start + _years_to_timedelta(years)
        periods.append(DashaPeriod(lord=lord, start=current_start, end=current_end))
        current_start = current_end
        i += 1
    return periods


def _antardasha_sequence(mahadasha: DashaPeriod) -> list[DashaPeriod]:
    maha_full_years = DASHA_YEARS[mahadasha.lord]
    cycle_idx = DASHA_LORD_CYCLE.index(mahadasha.lord)

    periods = []
    current_start = mahadasha.start
    for i in range(9):
        lord = DASHA_LORD_CYCLE[(cycle_idx + i) % 9]
        antar_years = maha_full_years * DASHA_YEARS[lord] / 120.0
        current_end = current_start + _years_to_timedelta(antar_years)
        periods.append(DashaPeriod(lord=lord, start=current_start, end=current_end))
        current_start = current_end
    return periods


def mahadasha_periods_for_lords(
    birth_dt_utc: datetime, moon_longitude: float, lords: list[str]
) -> dict[str, DashaPeriod]:
    """The single mahadasha span for each requested lord.

    Each of the 9 grahas rules exactly one mahadasha per 120-year
    Vimshottari cycle, and the true cycle start is never more than one
    lord's full period (at most 20 years, Venus) before birth -- so a
    121-year search window from birth is always enough to find all of them.
    """
    until_dt = birth_dt_utc + _years_to_timedelta(121)
    periods = _mahadasha_sequence(birth_dt_utc, moon_longitude, until_dt=until_dt)
    by_lord: dict[str, DashaPeriod] = {}
    for p in periods:
        by_lord.setdefault(p.lord, p)  # keep the first (earliest) occurrence of each lord
    return {lord: by_lord[lord] for lord in lords}


def current_dasha(
    birth_dt_utc: datetime, moon_longitude: float, at_dt: datetime | None = None
) -> DashaStatus:
    """Mahadasha and antardasha in effect at `at_dt` (defaults to now, UTC)."""
    if at_dt is None:
        at_dt = datetime.now(timezone.utc)

    mahadashas = _mahadasha_sequence(birth_dt_utc, moon_longitude, until_dt=at_dt)
    mahadasha = next((p for p in mahadashas if p.contains(at_dt)), mahadashas[-1])

    cycle_idx = DASHA_LORD_CYCLE.index(mahadasha.lord)
    next_lord = DASHA_LORD_CYCLE[(cycle_idx + 1) % 9]
    next_mahadasha = DashaPeriod(
        lord=next_lord,
        start=mahadasha.end,
        end=mahadasha.end + _years_to_timedelta(DASHA_YEARS[next_lord]),
    )

    antardashas = _antardasha_sequence(mahadasha)
    antardasha_index = next(
        (i for i, p in enumerate(antardashas) if p.contains(at_dt)), len(antardashas) - 1
    )
    antardasha = antardashas[antardasha_index]

    if antardasha_index + 1 < len(antardashas):
        next_antardasha = antardashas[antardasha_index + 1]
    else:
        next_antardasha = _antardasha_sequence(next_mahadasha)[0]

    return DashaStatus(
        mahadasha=mahadasha,
        antardasha=antardasha,
        next_mahadasha=next_mahadasha,
        next_antardasha=next_antardasha,
    )
