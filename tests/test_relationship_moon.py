from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from vedic_astro.chart import compute_natal_chart
from vedic_astro.relationships import analyze
from vedic_astro.transits import transit_houses, compute_transits
from relationship_consumer import top_reasons

@pytest.mark.parametrize('moon_sign',range(12))
def test_shared_house_references_all_signs(moon_sign):
    chart=SimpleNamespace(planets={'Moon':SimpleNamespace(longitude=moon_sign*30+15)},ascendant_longitude=((moon_sign+3)%12)*30+1)
    for sign in range(12):
        assert transit_houses(chart,sign*30)=={'house_from_moon':(sign-moon_sign)%12+1,'house_from_lagna':(sign-moon_sign-3)%12+1}


def test_occupancy_is_moon_only_and_secondary_cannot_count(monkeypatch):
    import vedic_astro.relationships as rel
    from vedic_astro.ephemeris import PlanetPosition
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    # Isolate occupancy using deliberately different Moon and Lagna references.
    chart.planets['Moon'].longitude=345;chart.ascendant_longitude=70
    raw={p:PlanetPosition(p,100,1,False) for p in chart.planets}
    monkeypatch.setattr(rel,'get_planet_positions',lambda *args:raw)
    before=deepcopy(chart);r=analyze(chart,datetime(2026,10,9,3,tzinfo=timezone.utc))
    assert chart==before
    houses=[f for f in r['activations'] if f['signature'].endswith('|occupancy')]
    assert {f['source'] for f in houses if f['score_eligible']}=={'Jupiter','Saturn'}
    assert all(f['target']=='house5' and 'Moon / Chandra Lagna' in f['detail'] for f in houses)
    assert all(not f['score_eligible'] for f in r['activations'] if f['family']=='house_lagna')
    assert all(t['house_from_moon']==5 and t['house_from_lagna']==2 for t in r['transits'])
    assert any('Moon / Chandra Lagna' in t for t in top_reasons(r))
    # Same longitude in H5 from Lagna, H8 from Moon must not earn an occupancy point.
    for v in raw.values():v.longitude=195
    r=analyze(chart,datetime(2026,10,9,3,tzinfo=timezone.utc))
    assert not any(f['score_eligible'] for f in r['activations'] if f['signature'].endswith('|occupancy'))
    secondary=[f for f in r['activations'] if f['family']=='house_lagna']
    assert secondary and all(not f['score_eligible'] for f in secondary)


def test_existing_transits_and_relationship_rows_share_houses(monkeypatch):
    import vedic_astro.transits as tr
    monkeypatch.setattr(tr,'_find_next_rashi_change',lambda *args:None)
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    at=datetime(2026,10,9,3,tzinfo=timezone.utc)
    placements=compute_transits(chart,at,chart.ayanamsa)
    for r in analyze(chart,at)['transits']:
        p=placements[r['planet']]
        assert (r['house_from_moon'],r['house_from_lagna'])==(p.house_from_moon,p.house_from_lagna)


def test_legacy_dk_source_eligibility_documented_and_preserved():
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    r=analyze(chart,chart.birth_datetime_utc)
    assert any(f['source']=='Sun' and f['target']=='Darakaraka' and f['score_eligible'] for f in r['activations'])
    assert 'ANY transit graha' in r['rules']['eligible']


def test_ending_house_rule_reads_moon_not_legacy_alias(monkeypatch):
    import vedic_astro.relationships as rel
    from vedic_astro.ephemeris import PlanetPosition
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    chart.planets['Moon'].longitude=345;chart.ascendant_longitude=70
    raw={p:PlanetPosition(p,345,1,False) for p in chart.planets}
    monkeypatch.setattr(rel,'get_planet_positions',lambda *args:raw)
    r=analyze(chart,datetime(2026,10,9,3,tzinfo=timezone.utc))
    ending=[f for f in r['activations'] if 'ending/separation' in f['categories']]
    assert any(f['source']=='Saturn' and f['family']=='house' and f['target']=='house1' and f['eligible'] for f in ending)
    for v in raw.values():v.longitude=70
    r=analyze(chart,datetime(2026,10,9,3,tzinfo=timezone.utc))
    ending=[f for f in r['activations'] if 'ending/separation' in f['categories']]
    assert not any(f['source']=='Saturn' and f['family']=='house' for f in ending)
    assert any(f['source']=='Saturn' and f['family']=='house_lagna' and not f['eligible'] for f in ending)
