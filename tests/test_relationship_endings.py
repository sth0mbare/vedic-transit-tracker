"""Synthetic, outcome-blind rules tests; personal historical results are not fixtures."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_navamsa import synthetic_chart
from vedic_astro.chart import compute_natal_chart
from vedic_astro.relationship_records import RelationshipEvent
from vedic_astro.relationships import (analyze, analyze_event, indicators, contact_rows,
    SIGN_LORDS, ASPECTS, RULE_VERSION, RULES)
from vedic_astro.relationship_endings import (ending_activations, score_ending_evidence,
    FAMILIES, CATEGORY)


def evidence(family, source, condition='a', eligible=True):
    return dict(signature=f'{family}|{source}|{condition}', condition_id=condition,
                source=source,family=family,eligible=eligible,detail='Synthetic evidence')


def test_single_planet_cannot_stack_in_any_family():
    rows=[evidence(f,'Saturn',str(i)) for f in FAMILIES for i in range(4)]
    score, audit=score_ending_evidence(rows*3)
    assert score['score']==1 and not score['flagged']
    assert len(audit)==24
    assert sum(r['counted'] for r in audit)==1
    assert all(r['status']=='Supporting context' for r in audit if not r['counted'])


def test_matching_stack_and_context():
    rows=[evidence('dasha','Venus'),evidence('slow','Saturn'),evidence('d9','Ketu'),evidence('fast','Moon')]
    score,_=score_ending_evidence(rows)
    assert score['score']==4 and score['flagged']
    rows += [evidence('house','Mars',eligible=False)]*10
    assert score_ending_evidence(rows)[0]==score
    # Repeated MD/AD/PD and DK/7th/Venus aliases still contribute only one actor.
    rows += [evidence('dasha','Venus',level) for level in ('MD','AD','PD')]
    assert score_ending_evidence(rows)[0]['score']==4


def test_matching_is_order_independent_and_prefers_required_families():
    rows=[evidence('dasha','Venus'),evidence('slow','Saturn'),evidence('house','Saturn'),evidence('fast','Mars')]
    score,audit=score_ending_evidence(rows)
    assert score['flagged'] and 'slow' in score['families']
    assert score_ending_evidence(list(reversed(rows)))==(score,audit)
    # Exhaustively verify maximum matching for small graphs.
    for mask in range(64):
        graph=[evidence(f,s) for i,(f,s) in enumerate(product(FAMILIES[:3],('Mars','Saturn'))) if mask & (1<<i)]
        actual,_=score_ending_evidence(graph)
        best=0
        for subset in range(1<<len(graph)):
            chosen=[r for i,r in enumerate(graph) if subset & (1<<i)]
            if len({r['family'] for r in chosen})==len(chosen)==len({r['source'] for r in chosen}):
                best=max(best,len(chosen))
        assert actual['score']==best


def run(chart=None, periods=(), transits=(), contacts=(), meta=None):
    chart=chart or synthetic_chart(0)
    return ending_activations(chart,meta or indicators(chart),periods,transits,contacts,SIGN_LORDS,ASPECTS)


def period(lord,level='MD'):
    at=datetime(2000,1,1,tzinfo=timezone.utc)
    return SimpleNamespace(lord=lord,level=level,start=at,end=at+timedelta(days=100))


def test_dasha_requires_both_roles_and_repeats_do_not_stack():
    chart=synthetic_chart(0)
    meta=indicators(chart)
    # Venus rules seventh for Aries, but is not inherently a disruption actor.
    chart.planets['Venus'].longitude=40
    meta['d9_placements']['Venus']['house']=2
    assert run(chart,[period('Venus')],meta=meta)[0]['score']==0
    chart.planets['Venus'].longitude=160  # 6th-house placement supplies second role
    s,a,_=run(chart,[period('Venus',level) for level in ('MD','AD','PD')],meta=meta)
    assert s['score']==1 and len(a)==3
    # Ketu alone needs a partnership role as well.
    chart.planets['Ketu'].longitude=40
    meta['d9_placements']['Ketu']['house']=2
    assert run(chart,[period('Ketu')],meta=meta)[0]['score']==0
    meta['d9_placements']['Ketu']['house']=7
    assert run(chart,[period('Ketu')],meta=meta)[0]['score']==1


@pytest.mark.parametrize('house',[1,7,6,8,12])
def test_axis_and_difficult_house_eligibility(house):
    row=dict(planet='Mars',longitude=(house-1)*30+1,house_from_moon=house,house_from_lagna=house)
    _,audit,_=run(transits=[row])
    fact=next(r for r in audit if r['family']=='house')
    assert fact['eligible']==(house in (1,7))
    contacts=contact_rows({'Mars':10},{'Venus':10},3)
    _,audit,_=run(transits=[row],contacts=contacts)
    assert next(r for r in audit if r['family']=='house')['eligible']
    assert sum(r['counted'] for r in audit)==1  # same Mars contact/occupancy/D9


def test_degree_boundaries_and_whole_sign_context():
    # Exact opposition also has a sign aspect: never two counts.
    for delta,expected in [(0,True),(3,True),(3.000001,False)]:
        contacts=contact_rows({'Saturn':0},{'Venus':180-delta},3)
        s,a,_=run(contacts=contacts)
        assert (s['score']>0)==expected
        assert all(not r['eligible'] for r in a if 'whole-sign' in r['condition_id'])
    assert run(contacts=contact_rows({'Ketu':359},{'Venus':2},3))[0]['score']==1


def test_d9_aliases_and_ul_have_no_invented_degree_contacts():
    chart=synthetic_chart(0);meta=indicators(chart)
    meta['d9_seventh']='Mesha'
    meta['d9_placements'][meta['d9_seventh_lord']]['rashi']='Mesha'
    meta['d9_placements']['Venus']['rashi']='Mesha'
    meta['ul_sign']='Mesha'
    s,a,_=run(chart,transits=[dict(planet='Saturn',longitude=0,house_from_moon=1,house_from_lagna=1)],meta=meta)
    assert len([r for r in a if r['family']=='d9'])==1
    assert any(r['family']=='ul_dk' and r['eligible'] for r in a)
    assert s['score']==1


def test_dk_and_seventh_lord_alias_does_not_double_count():
    chart=synthetic_chart(0);meta=indicators(chart);meta['darakaraka']=['Venus']
    s,a,_=run(chart,contacts=contact_rows({'Mars':10},{'Venus':10},3),meta=meta)
    assert s['score']==1 and len(a)==1
    meta['darakaraka']=['Mercury']
    s,a,_=run(chart,contacts=contact_rows({'Mars':10},{'Mercury':10},3),meta=meta)
    assert s['score']==1 and a[0]['family']=='ul_dk'


def test_moon_venus_triggers_need_background():
    chart=synthetic_chart(0);chart.planets['Venus'].longitude=160
    contacts=contact_rows({'Moon':10,'Venus':10},{'Venus':10},3)
    s,a,_=run(chart,contacts=contacts)
    assert s['score']==0 and not any(r['eligible'] for r in a)
    contacts+=contact_rows({'Saturn':10},{'Venus':10},3)
    s,a,_=run(chart,[period('Venus')],contacts=contacts)
    assert s['score']==3 and s['flagged']
    assert any(r['source']=='Moon' and r['counted'] for r in a)
    # A lunar contact to natal Ketu remains context even with that background.
    contacts+=contact_rows({'Moon':10},{'Ketu':10},3)
    _,a,_=run(chart,[period('Venus')],contacts=contacts)
    assert all(not r['eligible'] for r in a if r['target']=='Ketu')


def test_non_occupancy_results_remain_exactly_unchanged():
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    fixture=json.loads(Path('tests/fixtures/relationship_pre_moon.json').read_text())
    for old in fixture:
        chart.ayanamsa=old['ayanamsa']
        result=json.loads(json.dumps(analyze(chart,datetime.fromisoformat(old['at'])),default=str))
        for key in ('natal','natal_d1','contacts','dashas','birth_dasha_balance','ending_natal'):
            assert result[key]==old['result'][key]
        def retained(r):
            return [f for f in r['activations'] if CATEGORY not in f['categories']
                    and f['family']!='house_lagna' and not f['signature'].endswith('|occupancy')]
        assert retained(result)==retained(old['result'])


def test_no_extra_ephemeris_calls_or_outcome_dependency(monkeypatch):
    import vedic_astro.relationships as rel
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    before=deepcopy(chart);calls=[];original=rel.get_planet_positions
    def capture(*args):
        calls.append(args);return original(*args)
    monkeypatch.setattr(rel,'get_planet_positions',capture)
    event=RelationshipEvent('e','Synthetic','first met','2010-07-09',None,'UTC')
    first=analyze_event(chart,event)
    assert len(calls)==1
    for label in ('breakup','marriage','first date'):
        other=analyze_event(chart,replace(event,event_type=label,notes='Known ending',outcome_label='Long-term relationship start'))
        assert first['scores']==other['scores'] and first['activations']==other['activations']
    assert chart==before


def test_frozen_v1_1_source_manifest():
    lock=json.loads(Path('tests/fixtures/relationship_v1_1_lock.json').read_text())
    assert RULE_VERSION==lock['version']
    for path,digest in lock['files'].items():
        assert sha256(Path(path).read_bytes()).hexdigest()==digest, (
            f'{path}: frozen scoring changed; require an explicitly reviewed new rules version')
