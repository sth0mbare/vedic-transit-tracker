from copy import deepcopy
from math import nextafter, inf

import pytest
import swisseph as swe

from tests.test_navamsa import synthetic_chart
from vedic_astro.constants import GRAHAS, RASHIS
from vedic_astro.divisional import compute_chaturthamsa_chart, compute_dasamsa_chart

CASES = [(4, compute_chaturthamsa_chart), (10, compute_dasamsa_chart)]


def expected(division, segment):
    sign, part = divmod(segment, division)
    if division == 4:
        return (sign + [0, 3, 6, 9][part]) % 12
    starts = [0, 9, 2, 11, 4, 1, 6, 3, 8, 5, 10, 7]
    return (starts[sign] + part) % 12


@pytest.mark.parametrize('division,compute', CASES)
def test_all_boundaries_and_adjacent_values(division, compute):
    for i in range(1, division * 12):
        boundary = i * 30 / division
        for longitude, segment in [(nextafter(boundary, -inf), i-1),
                                   (boundary, i), (nextafter(boundary, inf), i)]:
            result = compute(synthetic_chart(longitude, longitude))
            assert result.ascendant_rashi == RASHIS[expected(division, segment)]
            assert len(result.planets) == 9
            for p in result.planets.values():
                assert p.rashi == result.ascendant_rashi
                assert p.house == 1


@pytest.mark.parametrize('division,compute', CASES)
def test_all_signs_parts_and_houses(division, compute):
    for lagna_segment in range(12 * division):
        lagna = (lagna_segment + .5) * 30 / division
        for segment in range(12 * division):
            longitude = (segment + .5) * 30 / division
            result = compute(synthetic_chart(longitude, lagna))
            expected_sign = expected(division, segment)
            expected_lagna = expected(division, lagna_segment)
            assert result.ascendant_rashi == RASHIS[expected_lagna]
            for p in result.planets.values():
                assert p.rashi == RASHIS[expected_sign]
                assert p.house == (expected_sign - expected_lagna) % 12 + 1


@pytest.mark.parametrize('division,compute', CASES)
def test_wraparound(division, compute):
    for longitude in (0, 360, 720, -360):
        assert compute(synthetic_chart(longitude)).planets['Sun'].rashi == 'Mesha'
    for longitude in (-1, nextafter(360, -inf)):
        assert compute(synthetic_chart(longitude)).planets['Sun'].rashi == RASHIS[expected(division, division*12-1)]


@pytest.mark.parametrize('division,compute', CASES)
def test_isolation_and_nine_distinct_inputs(division, compute, monkeypatch):
    chart = synthetic_chart(lagna=148.368)
    chart.ayanamsa = 'Raman'
    for i, name in enumerate(GRAHAS):
        chart.planets[name].longitude = i * 37 + 1
    before = deepcopy(chart)
    def forbidden(*args, **kwargs):
        pytest.fail('Additional ephemeris call')
    for name in ('calc_ut', 'houses_ex', 'set_sid_mode', 'julday'):
        monkeypatch.setattr(swe, name, forbidden)
    result = compute(chart)
    assert chart == before
    assert result.ayanamsa == 'Raman'
    for i, name in enumerate(GRAHAS):
        segment = int((i * 37 + 1) / (30 / division))
        assert result.planets[name].rashi == RASHIS[expected(division, segment)]
        assert result.planets[name].natal_retrograde == chart.planets[name].retrograde
    result.planets.clear()
    assert chart == before


@pytest.mark.parametrize('division,compute', CASES)
def test_invalid_longitudes(division, compute):
    for longitude in (inf, -inf, float('nan')):
        with pytest.raises(ValueError):
            compute(synthetic_chart(longitude))


@pytest.mark.parametrize('compute,longitude,rashi', [
    (compute_chaturthamsa_chart, 33, 'Vrishabha'),
    (compute_chaturthamsa_chart, 44, 'Simha'),
    (compute_chaturthamsa_chart, 53, 'Kumbha'),
    (compute_dasamsa_chart, 70, 'Kanya'),
    (compute_dasamsa_chart, 229, 'Makara'),
])
def test_published_examples(compute, longitude, rashi):
    # Rao, chapter 6, examples 12 and 17.
    assert compute(synthetic_chart(longitude)).planets['Sun'].rashi == rashi
