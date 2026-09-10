"""Parashari D4 and D10 projections of stored sidereal natal positions.

Rules: P.V.R. Narasimha Rao, Vedic Astrology: An Integrated Approach,
chapter 6 (https://www.vedicastrologer.org/articles/vedic_astro_textbook.pdf).
"""
from bisect import bisect_right
from dataclasses import dataclass
from math import isfinite

from .chart import NatalChart
from .constants import GRAHAS, RASHIS

_BOUNDARIES = {d: tuple(i * (30 / d) for i in range(1, 12 * d)) for d in (4, 10)}


@dataclass(frozen=True)
class DivisionalPlacement:
    name: str
    rashi: str
    house: int
    natal_retrograde: bool


@dataclass(frozen=True)
class DivisionalChart:
    division: int
    ayanamsa: str
    ascendant_rashi: str
    planets: dict[str, DivisionalPlacement]


def _sign(longitude: float, division: int) -> int:
    if not isfinite(longitude):
        raise ValueError("D1 longitude must be finite")
    # Direct comparisons preserve immediately adjacent floating-point values.
    segment = bisect_right(_BOUNDARIES[division], longitude % 360)
    sign, part = divmod(segment, division)
    if division == 4:
        return (sign + 3 * part) % 12
    # Odd-numbered zodiac signs have even zero-based indices.
    return (sign + (8 if sign % 2 else 0) + part) % 12


def _compute(natal_chart: NatalChart, division: int) -> DivisionalChart:
    lagna = _sign(natal_chart.ascendant_longitude, division)
    planets = {}
    for name in GRAHAS:
        natal = natal_chart.planets[name]
        sign = _sign(natal.longitude, division)
        planets[name] = DivisionalPlacement(
            name, RASHIS[sign], (sign - lagna) % 12 + 1, natal.retrograde)
    return DivisionalChart(division, natal_chart.ayanamsa, RASHIS[lagna], planets)


def compute_chaturthamsa_chart(natal_chart: NatalChart) -> DivisionalChart:
    """D4: four 7°30′ parts map to the natal sign and its 4th, 7th, 10th."""
    return _compute(natal_chart, 4)


def compute_dasamsa_chart(natal_chart: NatalChart) -> DivisionalChart:
    """D10: ten 3° parts, starting from self (odd signs) or ninth (even)."""
    return _compute(natal_chart, 10)
