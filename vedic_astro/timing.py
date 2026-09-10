"""Inspectable MD/AD/PD lookup; existing dasha APIs remain unchanged."""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from .constants import DASHA_LORD_CYCLE, DASHA_YEARS
from .dasha import (DashaPeriod, DAYS_PER_YEAR,
                    _years_to_timedelta, _antardasha_sequence)


@dataclass(frozen=True)
class HierarchyPeriod:
    level: str
    lord: str
    start: datetime
    end: datetime
    parent_md: str
    parent_ad: str = ""

    def contains(self, at):
        return self.start <= at < self.end


def utc(at):
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("A timezone-aware date/time is required")
    return at.astimezone(timezone.utc)


def birth_balance(moon_longitude):
    if not isfinite(moon_longitude):
        raise ValueError("Moon longitude must be finite")
    longitude=moon_longitude % 360
    boundaries=tuple(i * 40 / 3 for i in range(28))
    index=bisect_right(boundaries[1:-1],longitude)
    fraction=(longitude-boundaries[index])/(boundaries[index+1]-boundaries[index])
    lord=DASHA_LORD_CYCLE[index % 9]
    return {'moon_longitude':longitude,'nakshatra_index':index,
            'nakshatra_start':boundaries[index],'nakshatra_end':boundaries[index+1],
            'fraction_elapsed':fraction,'birth_lord':lord,
            'remaining_years':DASHA_YEARS[lord]*(1-fraction),'days_per_year':DAYS_PER_YEAR}


def mahadasha_at(birth, moon_longitude, at):
    birth, at = utc(birth), utc(at)
    if at < birth:
        raise ValueError("Dasha lookup is available from birth onward")
    if not isfinite(moon_longitude):
        raise ValueError("Moon longitude must be finite")
    balance=birth_balance(moon_longitude)
    lord, fraction = balance['birth_lord'], balance['fraction_elapsed']
    start = birth - _years_to_timedelta(DASHA_YEARS[lord] * fraction)
    index = DASHA_LORD_CYCLE.index(lord)
    while True:
        lord = DASHA_LORD_CYCLE[index % 9]
        end = start + _years_to_timedelta(DASHA_YEARS[lord])
        if start <= at < end:
            return DashaPeriod(lord, start, end)
        start, index = end, index + 1


def hierarchy_for_md(md):
    """One MD with its 9 ADs and 81 PDs. Intervals are [start, end)."""
    rows = [HierarchyPeriod("MD", md.lord, md.start, md.end, md.lord)]
    ads = _antardasha_sequence(md)
    # Force the final endpoint to its parent to prevent microsecond drift.
    ads[-1].end = md.end
    for ad in ads:
        rows.append(HierarchyPeriod("AD", ad.lord, ad.start, ad.end, md.lord))
        index = DASHA_LORD_CYCLE.index(ad.lord)
        start = ad.start
        cumulative = 0
        for i in range(9):
            lord = DASHA_LORD_CYCLE[(index + i) % 9]
            cumulative += DASHA_YEARS[lord]
            end = ad.end if i == 8 else ad.start + (ad.end - ad.start) * (cumulative / 120)
            rows.append(HierarchyPeriod("PD", lord, start, end, md.lord, ad.lord))
            start = end
    return rows


def dasha_at(birth, moon_longitude, at):
    at = utc(at)
    rows = hierarchy_for_md(mahadasha_at(birth, moon_longitude, at))
    return tuple(next(r for r in rows if r.level == level and r.contains(at))
                 for level in ("MD", "AD", "PD"))


def birth_cycle(birth, moon_longitude):
    """Nine full MDs starting with the one in effect at birth."""
    md = mahadasha_at(birth, moon_longitude, birth)
    periods = [md]
    for _ in range(8):
        md = mahadasha_at(birth, moon_longitude, md.end)
        periods.append(md)
    return periods
