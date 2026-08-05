"""Natal chart computation: Lagna, planet placements, Moon's nakshatra."""

from dataclasses import dataclass, field
from datetime import datetime

from .constants import DEFAULT_AYANAMSA, MOON
from .ephemeris import get_ascendant, get_planet_positions
from .util import house_from_sign, nakshatra_lord, nakshatra_name, nakshatra_pada, rashi_name


@dataclass
class PlanetPlacement:
    name: str
    longitude: float
    rashi: str
    house: int  # whole-sign house from Lagna, 1-12
    retrograde: bool


@dataclass
class NatalChart:
    birth_datetime_utc: datetime
    latitude: float
    longitude: float
    ayanamsa: str
    ascendant_longitude: float
    ascendant_rashi: str
    planets: dict[str, PlanetPlacement] = field(default_factory=dict)
    moon_rashi: str = ""
    moon_nakshatra: str = ""
    moon_nakshatra_lord: str = ""
    moon_pada: int = 0

    def house_of(self, planet_name: str) -> int:
        return self.planets[planet_name].house


def compute_natal_chart(
    birth_datetime_utc: datetime,
    latitude: float,
    longitude: float,
    ayanamsa_name: str = DEFAULT_AYANAMSA,
) -> NatalChart:
    ascendant_longitude = get_ascendant(birth_datetime_utc, latitude, longitude, ayanamsa_name)
    raw_positions = get_planet_positions(birth_datetime_utc, ayanamsa_name)

    planets = {
        name: PlanetPlacement(
            name=name,
            longitude=pos.longitude,
            rashi=rashi_name(pos.longitude),
            house=house_from_sign(pos.longitude, ascendant_longitude),
            retrograde=pos.retrograde,
        )
        for name, pos in raw_positions.items()
    }

    moon_longitude = raw_positions[MOON].longitude

    return NatalChart(
        birth_datetime_utc=birth_datetime_utc,
        latitude=latitude,
        longitude=longitude,
        ayanamsa=ayanamsa_name,
        ascendant_longitude=ascendant_longitude,
        ascendant_rashi=rashi_name(ascendant_longitude),
        planets=planets,
        moon_rashi=rashi_name(moon_longitude),
        moon_nakshatra=nakshatra_name(moon_longitude),
        moon_nakshatra_lord=nakshatra_lord(moon_longitude),
        moon_pada=nakshatra_pada(moon_longitude),
    )
