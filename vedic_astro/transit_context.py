"""General transit snapshots assembled from unchanged calculation helpers."""
from dataclasses import dataclass
from datetime import datetime

from .chart import NatalChart
from .timing import HierarchyPeriod, dasha_at, utc
from .transits import TransitPlacement, compute_transits


@dataclass
class TransitSnapshot:
    at_utc: datetime
    ayanamsa: str
    placements: dict[str, TransitPlacement]
    periods: tuple[HierarchyPeriod, ...]
    warnings: list[str]


def compute_snapshot(chart: NatalChart, at: datetime) -> TransitSnapshot:
    at = utc(at)
    placements = compute_transits(chart, at_dt=at, ayanamsa_name=chart.ayanamsa)
    warnings = []
    periods = ()
    if at < utc(chart.birth_datetime_utc):
        warnings.append('This instant precedes birth. Transit positions are available; personal Vimshottari periods are not.')
    else:
        periods = dasha_at(chart.birth_datetime_utc, chart.planets['Moon'].longitude, at)
    return TransitSnapshot(at, chart.ayanamsa, placements, periods, warnings)
