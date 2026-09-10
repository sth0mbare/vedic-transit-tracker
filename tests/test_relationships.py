from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_navamsa import synthetic_chart
from vedic_astro.chart import compute_natal_chart
from vedic_astro.relationships import (Activation, analyze, arudha_sign, contact_rows,
    indicators, repeated_signatures, score_activations, scan_windows)

BIRTH=datetime(1990,5,15,9,tzinfo=timezone.utc)

@pytest.fixture
def chart():
    return compute_natal_chart(BIRTH,18.5213738,73.8545071)

@pytest.mark.parametrize('base', range(12))
def test_ul_all_offsets_and_both_exceptions(base):
    expected=(9,2,4,3,8,10,9,2,4,3,8,10)
    for offset,value in enumerate(expected):
        assert arudha_sign(base,(base+offset)%12)==(base+value)%12


def test_darakaraka_and_ul_trace(chart):
    data=indicators(chart)
    assert data['darakaraka']==['Sun']
    assert data['ul_trace']['house12_sign']=='Karka'
    assert data['ul_trace']['lord']=='Moon'
    assert data['ul_trace']['raw_sign']=='Karka'
    assert data['ul_sign']=='Mesha'
    assert data['ul_house']==9
    assert data['d9_lagna']=='Dhanu'
    assert data['d9_seventh']=='Mithuna'
    assert data['d9_seventh_lord']=='Mercury'
    c=synthetic_chart(10)
    c.planets['Rahu'].longitude=0
    assert len(indicators(c)['darakaraka'])==7  # exact ties preserved; nodes excluded


def test_contacts_wraparound_orbs_and_directed_aspects():
    rows=contact_rows({'Mars':350,'Saturn':0,'Jupiter':0,'Rahu':0},
                      {'Venus':2,'Moon':180,'Mercury':60,'Sun':120},3)
    assert any(r['source']=='Saturn' and r['target']=='Mercury' and r['kind']=='whole-sign aspect 3' for r in rows)
    assert any(r['source']=='Jupiter' and r['target']=='Sun' and r['kind']=='whole-sign aspect 5' for r in rows)
    assert not any(r['source']=='Rahu' and 'whole-sign' in r['kind'] for r in rows)
    assert any(r['source']=='Rahu' and r['target']=='Moon' and r['kind']=='opposition' for r in rows)
    close=contact_rows({'Venus':359},{'Moon':2},3)
    assert close[0]['kind']=='conjunction' and close[0]['separation']==3
    assert not contact_rows({'Venus':359},{'Moon':2.001},3)
    assert not contact_rows({'Mercury':0},{'Moon':90},3)
    with pytest.raises(ValueError): contact_rows({}, {}, 11)


def fact(family,source='Venus',signature=None):
    return Activation(signature or family+'|'+source,family,source,'house7',
                      ('relationship formation',),'test evidence',True)


def test_scoring_dedup_and_source_matching():
    # Three families supplied by one planet cannot qualify.
    facts=[fact('dasha'),fact('slow'),fact('d9')]*5
    score=score_activations(facts)['relationship formation']
    assert score['score']==3 and score['independent_source_count']==1 and not score['flagged']
    facts=[fact('dasha','Venus'),fact('slow','Jupiter'),fact('d9','Saturn')]
    assert score_activations(facts)['relationship formation']['flagged']
    # Context-only facts never inflate score.
    facts.append(Activation('context','fast','Mars','house7',('relationship formation',),'context'))
    assert score_activations(facts)['relationship formation']['score']==3


def test_repeated_signatures_need_distinct_events():
    f={'signature':'dasha|Venus|house7|AD','detail':'Calculated Venus AD'}
    result={'activations':[f,f]}
    assert repeated_signatures([('a',result),('a',result)])==[]
    rows=repeated_signatures([('a',result),('b',result)])
    assert rows[0]['event_count']==2
    assert rows[0]['evidence']=={'a':f['detail'],'b':f['detail']}


def test_snapshot_is_deterministic_and_preserves_chart(chart):
    before=deepcopy(chart)
    result=analyze(chart,BIRTH)
    assert result==analyze(chart,BIRTH)
    assert chart==before
    assert len(result['transits'])==9
    for row in result['transits']:
        natal=chart.planets[row['planet']]
        assert row['longitude']==natal.longitude
        assert row['natal_house']==natal.house
    assert [p['level'] for p in result['dashas']]==['MD','AD','PD']
    assert result['natal_d1']['ayanamsa']==chart.ayanamsa
    assert all(f['signature'] and f['detail'] for f in result['activations'])
    assert analyze(chart,BIRTH-timedelta(days=1))['dashas']==[]


def test_selected_ayanamsa_propagates(monkeypatch,chart):
    import vedic_astro.relationships as rel
    original=rel.get_planet_positions
    seen=[]
    def capture(at,ayanamsa):
        seen.append(ayanamsa)
        return original(at,ayanamsa)
    monkeypatch.setattr(rel,'get_planet_positions',capture)
    chart.ayanamsa='Raman'
    assert rel.analyze(chart,BIRTH)['ayanamsa']=='Raman'
    assert seen==['Raman']


def test_window_grouping_requires_baseline_and_actual_support(monkeypatch,chart):
    import vedic_astro.relationships as rel
    start=datetime(2027,1,1,tzinfo=timezone.utc)
    def fake(chart,at,orb):
        high=at.date() in {start.date(),(start+timedelta(days=1)).date(),(start+timedelta(days=3)).date()}
        return {'transits':[],'dashas':[],'at_utc':at.isoformat(),'scores':{'relationship formation':{
            'score':4 if high else 2,'flagged':high,'families':['dasha','slow','d9','fast'] if high else [],
            'signatures':['verified'] if high else []}},
            'activations':[{'categories':['relationship formation'],'detail':'verified'}] if high else []}
    monkeypatch.setattr(rel,'analyze',fake)
    result=scan_windows(chart,start,start+timedelta(days=4))
    assert result['baseline_samples']==90
    assert result['thresholds']['relationship formation']=={'median':2,'p75':2}
    assert len(result['windows'])==1
    assert [len(w['samples']) for w in result['windows']]==[2]
    assert len(result['isolated_samples'])==1
    assert result['windows'][0]['last_sample']==(start+timedelta(days=1)).isoformat()
    # A constant-high baseline must not turn every future day into an unusual window.
    def constant(chart,at,orb):
        r=fake(chart,start,orb);r['at_utc']=at.isoformat();return r
    monkeypatch.setattr(rel,'analyze',constant)
    assert scan_windows(chart,start,start+timedelta(days=2))['windows']==[]
    with pytest.raises(ValueError): scan_windows(chart,start,start-timedelta(days=1))


def test_event_export_carries_unknown_time_assumption(chart):
    from vedic_astro.relationship_records import RelationshipEvent
    from vedic_astro.relationships import analyze_event
    event=RelationshipEvent('id','Test','first met','2020-05-15',None,'Asia/Kolkata')
    result=analyze_event(chart,event)
    assert result['event']['clock'] is None
    assert result['input_timezone']=='Asia/Kolkata'
    assert 'noon assumed' in result['time_precision']
    assert result['at_utc']=='2020-05-15T06:30:00+00:00'
