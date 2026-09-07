"""D9 boundary, traditional mapping, regression and isolation tests."""

from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from math import inf, nextafter

import pytest
import swisseph as swe

from vedic_astro.chart import NatalChart, PlanetPlacement, compute_natal_chart
from vedic_astro.constants import GRAHAS, RASHIS
from vedic_astro.navamsa import compute_navamsa_chart


def synthetic_chart(longitude=0.0, lagna=0.0):
    return NatalChart(
        birth_datetime_utc=datetime(1990, 5, 15, 9, tzinfo=timezone.utc),
        latitude=18.5213738, longitude=73.8545071, ayanamsa="Lahiri",
        ascendant_longitude=lagna, ascendant_rashi="Mesha",
        planets={name: PlanetPlacement(name, longitude, "Mesha", 1, name == "Mercury")
                 for name in GRAHAS},
    )


@pytest.mark.parametrize("division", range(1, 108))
def test_every_boundary_and_adjacent_floats(division):
    # Independently construct each rational boundary, then its nearest float.
    boundary = float(Fraction(division * 10, 3))
    for longitude, expected in (
        (nextafter(boundary, -inf), (division - 1) % 12),
        (boundary, division % 12),
        (nextafter(boundary, inf), division % 12),
    ):
        result = compute_navamsa_chart(synthetic_chart(longitude))
        assert all(p.rashi == RASHIS[expected] for p in result.planets.values())
        lagna_result = compute_navamsa_chart(synthetic_chart(lagna=longitude))
        assert lagna_result.ascendant_rashi == RASHIS[expected]


@pytest.mark.parametrize("longitude,expected", [
    (0.0, "Mesha"), (360.0, "Mesha"), (720.0, "Mesha"),
    (-360.0, "Mesha"), (-1.0, "Meena"),
    (nextafter(360.0, -inf), "Meena"), (nextafter(360.0, inf), "Mesha"),
])
def test_zodiac_wraparound(longitude, expected):
    result = compute_navamsa_chart(synthetic_chart(longitude, longitude))
    assert result.ascendant_rashi == expected
    assert all(p.rashi == expected and p.house == 1 for p in result.planets.values())


@pytest.mark.parametrize("d1_sign", range(12))
def test_traditional_movable_fixed_dual_mapping(d1_sign):
    # Traditional start: same sign for movable, ninth for fixed, fifth for dual.
    start = (d1_sign + (0, 8, 4)[d1_sign % 3]) % 12
    for part in range(9):
        longitude = d1_sign * 30 + (part + 0.5) * (10 / 3)
        result = compute_navamsa_chart(synthetic_chart(longitude))
        assert result.planets["Sun"].rashi == RASHIS[(start + part) % 12]


@pytest.mark.parametrize("lagna_sign", range(12))
def test_whole_sign_houses(lagna_sign):
    for planet_sign in range(12):
        result = compute_navamsa_chart(synthetic_chart(
            (planet_sign + 0.5) * (10 / 3), (lagna_sign + 0.5) * (10 / 3)))
        assert result.ascendant_rashi == RASHIS[lagna_sign]
        assert result.planets["Sun"].house == (planet_sign - lagna_sign) % 12 + 1


def test_no_mutation_or_ephemeris_calls(monkeypatch):
    chart = synthetic_chart(34.5, 148.368)
    chart.ayanamsa = "Raman"
    before = deepcopy(chart)

    def forbidden(*args, **kwargs):
        pytest.fail("D9 must not call Swiss Ephemeris")

    for name in ("calc_ut", "houses_ex", "set_sid_mode", "julday"):
        monkeypatch.setattr(swe, name, forbidden)
    result = compute_navamsa_chart(chart)
    assert chart == before
    assert result.ayanamsa == "Raman"
    assert set(result.planets) == set(GRAHAS)
    assert result.planets is not chart.planets
    for name in GRAHAS:
        assert result.planets[name] is not chart.planets[name]
        assert result.planets[name].natal_retrograde == chart.planets[name].retrograde
    result.planets.clear()
    assert chart == before


@pytest.mark.parametrize("longitude", [float("nan"), inf, -inf])
def test_nonfinite_longitudes_rejected(longitude):
    with pytest.raises(ValueError, match="finite"):
        compute_navamsa_chart(synthetic_chart(longitude))


def test_example_chart_placements():
    chart = compute_natal_chart(
        datetime(1990, 5, 15, 9, tzinfo=timezone.utc), 18.5213738, 73.8545071)
    before = deepcopy(chart)
    result = compute_navamsa_chart(chart)
    # Independent traditional division counting, using each stored D1 longitude.
    for name in GRAHAS:
        longitude = chart.planets[name].longitude
        sign, degree = divmod(longitude, 30)
        start = (int(sign) + (0, 8, 4)[int(sign) % 3]) % 12
        part = int(Fraction(degree) / Fraction(10, 3))
        assert result.planets[name].rashi == RASHIS[(start + part) % 12]
    assert result.ascendant_rashi == "Dhanu"
    assert chart == before
