from copy import deepcopy
from math import nextafter, inf
import pytest
import swisseph as swe
from tests.test_navamsa import synthetic_chart
from vedic_astro.divisional import compute_hora_chart

# First/second halves for Aries through Pisces, using traditional sign numbering.
SIGNS = [('Simha', 'Karka'), ('Karka', 'Simha')] * 6

@pytest.mark.parametrize('sign', range(12))
def test_halves_and_boundaries(sign):
    midpoint = sign * 30 + 15
    for longitude, expected in [(sign*30, SIGNS[sign][0]),
                                (nextafter(midpoint, -inf), SIGNS[sign][0]),
                                (midpoint, SIGNS[sign][1]),
                                (nextafter(midpoint, inf), SIGNS[sign][1]),
                                (nextafter((sign+1)*30, -inf), SIGNS[sign][1])]:
        d = compute_hora_chart(synthetic_chart(longitude, longitude))
        assert d.ascendant_rashi == expected
        assert len(d.planets) == 9
        assert all(p.rashi == expected and p.house == 1 for p in d.planets.values())

@pytest.mark.parametrize('lagna,planet,house', [(1,16,12),(16,1,2),(1,1,1),(16,16,1)])
def test_houses(lagna, planet, house):
    assert compute_hora_chart(synthetic_chart(planet,lagna)).planets['Sun'].house == house

def test_wraparound_and_isolation(monkeypatch):
    for lon in (0,360,720,-360):
        assert compute_hora_chart(synthetic_chart(lon)).planets['Sun'].rashi == 'Simha'
    c=synthetic_chart();c.ayanamsa='Raman'
    for i,p in enumerate(c.planets.values()):
        p.longitude=i*31+10
    before=deepcopy(c)
    def forbidden(*args, **kwargs):
        pytest.fail('Unexpected ephemeris call')
    for name in ('calc_ut','houses_ex','set_sid_mode','julday'):
        monkeypatch.setattr(swe,name,forbidden)
    d=compute_hora_chart(c)
    assert d.ayanamsa=='Raman'
    for name,p in c.planets.items():
        assert d.planets[name].rashi==SIGNS[int(p.longitude//30)][int(p.longitude%30>=15)]
        assert d.planets[name].natal_retrograde==p.retrograde
    d.planets.clear()
    assert c==before
