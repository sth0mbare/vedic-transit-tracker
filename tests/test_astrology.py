"""Regression tests for the core Vedic astrology calculations.

The reference chart (Pune, India, 1990-05-15 14:30 IST / 09:00 UTC, Lahiri
ayanamsa) was hand-verified during development:
  - House placements were checked manually against the Lagna sign (Simha),
    counting whole-sign houses around the zodiac.
  - The Vimshottari dasha balance/antardasha math was independently
    recomputed by hand from the Moon's nakshatra position.
  - Mercury retrograde in mid-May 1990 and Saturn's 2025-2027 transit through
    sidereal Pisces are both independently documented astronomical/
    astrological facts, corroborating the ephemeris + ayanamsa layer.
These values lock in that verified behavior so future changes don't
silently break the math.
"""

from datetime import datetime, timezone

import pytest

from vedic_astro.chart import compute_natal_chart
from vedic_astro.constants import SUN, VENUS
from vedic_astro.dasha import current_dasha, mahadasha_periods_for_lords
from vedic_astro.transits import compute_guru_gochar, compute_sade_sati, compute_transits

PUNE_LAT, PUNE_LON = 18.5213738, 73.8545071
BIRTH_DT = datetime(1990, 5, 15, 9, 0, tzinfo=timezone.utc)  # 14:30 IST


@pytest.fixture(scope="module")
def natal_chart():
    return compute_natal_chart(BIRTH_DT, PUNE_LAT, PUNE_LON)


def test_ascendant(natal_chart):
    assert natal_chart.ascendant_rashi == "Simha"
    assert natal_chart.ascendant_longitude == pytest.approx(148.368, abs=0.01)


def test_moon_nakshatra(natal_chart):
    assert natal_chart.moon_rashi == "Makara"
    assert natal_chart.moon_nakshatra == "Uttara Ashadha"
    assert natal_chart.moon_pada == 2
    assert natal_chart.moon_nakshatra_lord == "Sun"


def test_planet_houses_from_lagna(natal_chart):
    expected_houses = {
        "Sun": 10, "Moon": 6, "Mars": 7, "Mercury": 9, "Jupiter": 11,
        "Venus": 8, "Saturn": 6, "Rahu": 6, "Ketu": 12,
    }
    for planet, house in expected_houses.items():
        assert natal_chart.house_of(planet) == house, planet


def test_mercury_retrograde_may_1990(natal_chart):
    assert natal_chart.planets["Mercury"].retrograde is True


def test_dasha_at_birth(natal_chart):
    moon_longitude = natal_chart.planets["Moon"].longitude
    status = current_dasha(BIRTH_DT, moon_longitude, at_dt=BIRTH_DT)

    assert status.mahadasha.lord == "Sun"
    assert status.mahadasha.start.date().isoformat() == "1988-01-07"
    assert status.mahadasha.end.date().isoformat() == "1994-01-06"
    assert status.antardasha.lord == "Jupiter"
    assert status.antardasha.contains(BIRTH_DT)


def test_antardasha_falls_within_mahadasha(natal_chart):
    moon_longitude = natal_chart.planets["Moon"].longitude
    status = current_dasha(BIRTH_DT, moon_longitude, at_dt=BIRTH_DT)
    assert status.mahadasha.start <= status.antardasha.start
    assert status.antardasha.end <= status.mahadasha.end


def test_next_mahadasha_and_antardasha_at_birth(natal_chart):
    moon_longitude = natal_chart.planets["Moon"].longitude
    status = current_dasha(BIRTH_DT, moon_longitude, at_dt=BIRTH_DT)

    # Next mahadasha follows Sun's directly in the DASHA_LORD_CYCLE order.
    assert status.next_mahadasha.lord == "Moon"
    assert status.next_mahadasha.start == status.mahadasha.end
    assert status.next_mahadasha.start.date().isoformat() == "1994-01-06"

    # Next antardasha follows Jupiter directly within the Sun mahadasha.
    assert status.next_antardasha.lord == "Saturn"
    assert status.next_antardasha.start == status.antardasha.end


def test_sun_venus_mahadasha_periods(natal_chart):
    moon_longitude = natal_chart.planets["Moon"].longitude
    periods = mahadasha_periods_for_lords(BIRTH_DT, moon_longitude, [SUN, VENUS])

    assert periods[SUN].start.date().isoformat() == "1988-01-07"
    assert periods[SUN].end.date().isoformat() == "1994-01-06"
    assert periods[VENUS].start.date().isoformat() == "2088-01-06"
    assert periods[VENUS].end.date().isoformat() == "2108-01-07"


def test_sade_sati_active_at_birth(natal_chart):
    # Natal Saturn and natal Moon are both in Makara -- Saturn conjunct Moon
    # by sign at the moment of birth, i.e. Peak-phase Sade Sati at birth.
    status = compute_sade_sati(natal_chart, at_dt=BIRTH_DT)
    assert status.active is True
    assert status.house_from_moon == 1
    assert status.phase == "Peak (Chudasi)"


def test_guru_gochar_at_birth(natal_chart):
    # At birth, "current" Jupiter is just natal Jupiter: Mithuna, which is
    # house 6 from natal Moon (Makara) -- not one of the 5 favorable houses.
    status = compute_guru_gochar(natal_chart, at_dt=BIRTH_DT)
    assert status.jupiter_rashi == "Mithuna"
    assert status.house_from_moon == 6
    assert status.favorable is False


def test_transits_cover_all_grahas_with_valid_houses(natal_chart):
    transits = compute_transits(natal_chart, at_dt=BIRTH_DT)
    assert set(transits) == {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    }
    for placement in transits.values():
        assert 1 <= placement.house_from_moon <= 12
        assert 1 <= placement.house_from_lagna <= 12

    # At the birth instant, "current" transits equal the natal chart itself.
    assert transits["Saturn"].rashi == "Makara"
    assert transits["Saturn"].house_from_moon == 1
