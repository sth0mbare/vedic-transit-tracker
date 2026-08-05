"""Thin wrapper around Swiss Ephemeris for sidereal (Vedic) planetary positions.

All longitudes returned here are sidereal, in the ayanamsa the caller selects
(Lahiri by default), measured 0-360 deg from 0 Aries.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

import swisseph as swe

from .constants import AYANAMSAS, DEFAULT_AYANAMSA, GRAHAS, KETU, RAHU, SWE_BODY

_CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


@dataclass
class PlanetPosition:
    name: str
    longitude: float  # sidereal degrees, 0-360
    speed: float  # deg/day; negative means retrograde
    retrograde: bool


def _set_ayanamsa(ayanamsa_name: str) -> None:
    if ayanamsa_name not in AYANAMSAS:
        raise ValueError(
            f"Unknown ayanamsa '{ayanamsa_name}'. Choose from: {list(AYANAMSAS)}"
        )
    swe.set_sid_mode(AYANAMSAS[ayanamsa_name])


def julian_day_utc(dt_utc: datetime) -> float:
    """Convert a UTC-aware datetime to a Julian day number (UT)."""
    if dt_utc.tzinfo is None:
        raise ValueError("dt_utc must be timezone-aware (UTC)")
    dt_utc = dt_utc.astimezone(timezone.utc)
    hour_decimal = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_decimal)


def get_planet_positions(
    dt_utc: datetime, ayanamsa_name: str = DEFAULT_AYANAMSA
) -> dict[str, PlanetPosition]:
    """Sidereal longitude, speed, and retrograde status for all 9 grahas."""
    _set_ayanamsa(ayanamsa_name)
    jd = julian_day_utc(dt_utc)

    positions: dict[str, PlanetPosition] = {}
    for name in GRAHAS:
        if name == KETU:
            continue  # derived from Rahu below
        body_id = SWE_BODY[name]
        xx, _retflags = swe.calc_ut(jd, body_id, _CALC_FLAGS)
        longitude, _lat, _dist, speed = xx[0], xx[1], xx[2], xx[3]
        positions[name] = PlanetPosition(
            name=name,
            longitude=longitude % 360,
            speed=speed,
            retrograde=speed < 0,
        )

    rahu = positions[RAHU]
    ketu_longitude = (rahu.longitude + 180) % 360
    positions[KETU] = PlanetPosition(
        name=KETU,
        longitude=ketu_longitude,
        speed=rahu.speed,  # Ketu mirrors Rahu's motion
        retrograde=rahu.retrograde,  # nodes are always retrograde in mean motion
    )
    return positions


def get_ascendant(
    dt_utc: datetime, latitude: float, longitude: float, ayanamsa_name: str = DEFAULT_AYANAMSA
) -> float:
    """Sidereal longitude of the Lagna (ascendant), 0-360 deg."""
    _set_ayanamsa(ayanamsa_name)
    jd = julian_day_utc(dt_utc)
    # Whole-sign houses (b'W') is the traditional Vedic house system; the
    # ascendant degree itself (ascmc[0]) doesn't depend on house system choice.
    _cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b"W", swe.FLG_SIDEREAL)
    return ascmc[0] % 360
