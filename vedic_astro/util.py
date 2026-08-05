"""Pure helper functions for converting sidereal longitude to Vedic chart units.

Shared by chart.py (natal chart) and transits.py (gochara), so the same
sign/nakshatra/house math is used everywhere.
"""

from .constants import DEG_PER_NAKSHATRA, DEG_PER_PADA, DEG_PER_RASHI, NAKSHATRAS, NAKSHATRA_LORDS, RASHIS


def rashi_index(longitude: float) -> int:
    """0-11 zodiac sign index (0 = Mesha/Aries) for a sidereal longitude."""
    return int((longitude % 360) // DEG_PER_RASHI)


def rashi_name(longitude: float) -> str:
    return RASHIS[rashi_index(longitude)]


def nakshatra_index(longitude: float) -> int:
    """0-26 nakshatra index for a sidereal longitude."""
    return int((longitude % 360) // DEG_PER_NAKSHATRA)


def nakshatra_name(longitude: float) -> str:
    return NAKSHATRAS[nakshatra_index(longitude)]


def nakshatra_lord(longitude: float) -> str:
    return NAKSHATRA_LORDS[nakshatra_index(longitude)]


def nakshatra_pada(longitude: float) -> int:
    """1-4 quarter (pada) within the current nakshatra."""
    position_in_nakshatra = (longitude % 360) % DEG_PER_NAKSHATRA
    return int(position_in_nakshatra // DEG_PER_PADA) + 1


def house_from_sign(target_longitude: float, reference_longitude: float) -> int:
    """Whole-sign house number (1-12) of target, counted from reference's sign.

    This is the standard Vedic (Jyotish) house system: houses are whole
    zodiac signs, and the reference sign (Lagna or natal Moon) is always
    house 1.
    """
    offset = rashi_index(target_longitude) - rashi_index(reference_longitude)
    return (offset % 12) + 1
