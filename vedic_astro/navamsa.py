"""Parashari D9 placements derived only from an existing sidereal D1 chart."""

from bisect import bisect_right
from dataclasses import dataclass
from math import isfinite

from .chart import NatalChart
from .constants import GRAHAS, RASHIS

# 108 half-open divisions of 3 degrees 20 minutes across the zodiac.
# Compare directly to boundaries instead of multiplying a longitude by nine:
# multiplication can round an immediately-below-boundary value up across it.
_NAVAMSA_BOUNDARIES = tuple(i * 10 / 3 for i in range(1, 108))


def _navamsa_sign_index(longitude: float) -> int:
    if not isfinite(longitude):
        raise ValueError("D1 longitude must be finite")
    return bisect_right(_NAVAMSA_BOUNDARIES, longitude % 360) % 12


@dataclass(frozen=True)
class NavamsaPlacement:
    name: str
    rashi: str
    house: int  # whole-sign house relative to D9 Lagna
    natal_retrograde: bool  # copied from D1; no independent D9 motion


@dataclass(frozen=True)
class NavamsaChart:
    ayanamsa: str  # inherited from the source D1 chart
    ascendant_rashi: str
    planets: dict[str, NavamsaPlacement]


def compute_navamsa_chart(natal_chart: NatalChart) -> NavamsaChart:
    """Project exact stored D1 longitudes into D9 without modifying D1.

    The sign mapping is equivalent to (9 * longitude) modulo 360, with
    explicit subdivision boundaries to preserve adjacent float values.
    No ephemeris calls or additional ayanamsa adjustments are made.
    """
    lagna_sign = _navamsa_sign_index(natal_chart.ascendant_longitude)
    planets = {}
    for name in GRAHAS:
        natal = natal_chart.planets[name]
        sign = _navamsa_sign_index(natal.longitude)
        planets[name] = NavamsaPlacement(
            name=name,
            rashi=RASHIS[sign],
            house=(sign - lagna_sign) % 12 + 1,
            natal_retrograde=natal.retrograde,
        )
    return NavamsaChart(
        ayanamsa=natal_chart.ayanamsa,
        ascendant_rashi=RASHIS[lagna_sign],
        planets=planets,
    )
