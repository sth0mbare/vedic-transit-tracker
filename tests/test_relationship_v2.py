"""Synthetic methodology tests only: fabricated positions/periods, no event data."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
import hashlib,json
import pytest
from vedic_astro.chart import NatalChart,PlanetPlacement
from vedic_astro.ephemeris import PlanetPosition
from vedic_astro.constants import GRAHAS,RASHIS
from vedic_astro.util import house_from_sign
from vedic_astro.timing import HierarchyPeriod
from vedic_astro.relationship_v2.engine import analyze_v2
from vedic_astro.relationship_v2.evidence import EvidenceBook,actor_group
from vedic_astro.relationship_v2.natal import build_natal
from vedic_astro.relationship_v2.climate import compute_climate
from vedic_astro.relationship_v2.periods import activate_periods
from vedic_astro.relationship_v2.assessment import assess
from vedic_astro.relationship_v2.geometry import rashi_aspect,sign_operators,jaimini_operators
from vedic_astro.relationship_v2.transits import activate_transits
from vedic_astro.relationship_v2.windows import discover_boundaries,windows_from_segments,scan_v2
from vedic_astro.relationship_v2.spec import VEDHA,PARAMETERS,VERSION

UTC=timezone.utc
AT=datetime(2000,1,1,tzinfo=UTC)  # Arbitrary synthetic fixture origin, not an event.


def chart():
    longs=dict(zip(GRAHAS,[10,345,45,78,132,194,263,307,127]))
    return NatalChart(datetime(1900,1,1,tzinfo=UTC),0,0,'Lahiri',0,'Mesha',
        {p:PlanetPlacement(p,v,RASHIS[int(v//30)],house_from_sign(v,0),False) for p,v in longs.items()})


def positions(**overrides):
    longs={p:10.0 for p in GRAHAS};longs.update(Moon=180,Venus=150,Rahu=307,Ketu=127);longs.update(overrides)
    return {p:PlanetPosition(p,v,-0.05 if p in ('Rahu','Ketu') else 1.0,p in ('Rahu','Ketu')) for p,v in longs.items()}


def periods(md='Venus',ad='Venus',pd='Mars'):
    return tuple(HierarchyPeriod(level,p,AT-timedelta(days=1),AT+timedelta(days=1),md,ad if level=='PD' else '')
                 for level,p in zip(('MD','AD','PD'),(md,ad,pd)))


def evaluate(c=None,pos=None,per=None):
    return analyze_v2(c or chart(),AT,position_provider=lambda *a:pos or positions(),period_provider=lambda *a:per or periods())


def atom(book,actor,feature,layer='structural',target='sign:1'):
    i=book.add(actor,target,'natal D1','sign_conjunction',layer,feature,'Synthetic gate witness')
    book.feature(feature,[i]);return i


@pytest.mark.parametrize('moon_sign',range(12))
def test_moon_house_and_lagna_references(moon_sign):
    c=chart();c.planets['Moon'].longitude=moon_sign*30+15
    b=EvidenceBook(AT);pos=positions(Jupiter=((moon_sign+4)%12)*30+2)
    out=compute_climate(c,pos,b)
    assert out['Jupiter']['house_from_moon']==5
    assert out['Jupiter']['house_from_lagna']==((moon_sign+4)%12)+1


def test_d1_d9_and_legacy_chart_not_mutated():
    from vedic_astro.relationships import indicators
    c=chart();before=deepcopy(c);r=evaluate(c)
    assert c==before
    assert r['natal']['metadata']==indicators(c)
    assert r['natal']['d1_lords'][7]=='Venus'
    assert not any('projected' in a['operator'] for a in r['evidence'])
    assert r['data_quality']['warnings']
    r['methodology']['source_classifications'].clear()
    assert evaluate()['methodology']['source_classifications']


def role_natal():
    return {'roles':{'romance':{'Venus'},'partner_direct':{'Mars'},'partner_support':{'Venus'},
                     'difficulty':{'Saturn'},'d9_eligible':{'Venus'},'continuity':{'Mars'}}}


@pytest.mark.parametrize('md,ad,pd,expected',[
 ('Venus','Mercury','Moon',False),('Mercury','Mercury','Venus',False),
 ('Venus','Venus','Moon',True),('Mercury','Venus','Venus',True)])
def test_romance_hierarchy_and_md_pd_alone(md,ad,pd,expected):
    b=EvidenceBook(AT);activate_periods(role_natal(),periods(md,ad,pd),b)
    assert bool(b.features.get('romance_period'))==expected


@pytest.mark.parametrize('md,ad,pd,expected',[
 ('Mercury','Mars','Moon',True),('Mars','Venus','Moon',True),('Mercury','Venus','Mars',True),
 ('Venus','Mercury','Mars',False),('Mars','Mercury','Moon',False)])
def test_partnership_hierarchy(md,ad,pd,expected):
    b=EvidenceBook(AT);activate_periods(role_natal(),periods(md,ad,pd),b)
    assert bool(b.features.get('partnership_period'))==expected


def test_md_d9_background_only():
    b=EvidenceBook(AT);activate_periods(role_natal(),periods('Venus','Mercury','Moon'),b)
    assert not b.features.get('d9_croboration') and not b.features.get('d9_corroboration')


def test_fast_only_never_manufactures_entry_or_commitment():
    b=EvidenceBook(AT)
    atom(b,'Moon','romance_trigger','trigger');atom(b,'Venus','partner_trigger','trigger')
    r=assess(b)
    assert r['romance']['state']=='short-term trigger only'
    for key in ('partner_entry','commitment'):
        assert r[key]['state']=='not established'
        assert 'partnership_period' in r[key]['gates_failed']
        assert 'jupiter_support' in r[key]['gates_failed']


def test_clear_jupiter_requires_natal_contact_not_just_climate():
    good=evaluate(pos=positions(Jupiter=10))
    assert good['general_gochara']['Jupiter']['status']=='favorable'
    assert good['assessments']['partner_entry']['gates']['jupiter_support']
    absent=evaluate(pos=positions(Jupiter=100))  # H5 from Moon; no contact to the constructed partnership signs.
    assert absent['general_gochara']['Jupiter']['house_from_moon']==5
    assert not absent['assessments']['partner_entry']['gates']['jupiter_support']
    mixed=evaluate(pos=positions(Jupiter=194))  # Natal seventh target, but H8 climate.
    assert not mixed['assessments']['partner_entry']['gates']['jupiter_support']
    assert any(a['details'].get('climate_qualification')=='mixed' for a in mixed['evidence'])


def test_vedha_blocks_jupiter_without_changing_natal_geometry():
    base=evaluate(pos=positions(Jupiter=10))
    blocked=evaluate(pos=positions(Jupiter=10,Mercury=305))
    assert blocked['general_gochara']['Jupiter']['status']=='favorable but obstructed'
    assert blocked['general_gochara']['Jupiter']['blockers']==['Mercury']
    assert not blocked['assessments']['partner_entry']['gates']['jupiter_support']
    assert base['natal']==blocked['natal']


@pytest.mark.parametrize('p,exception',[('Sun','Saturn'),('Saturn','Sun'),('Moon','Mercury'),('Mercury','Moon')])
def test_vedha_exceptions(p,exception):
    c=chart();c.planets['Moon'].longitude=0
    house,block=next(iter(VEDHA[p].items()))
    vals={q:((house-1)*30+2) for q in GRAHAS};vals[exception]=(block-1)*30+2
    out=compute_climate(c,positions(**vals),EvidenceBook(AT))
    assert out[p]['status']=='favorable'


def test_nodes_cannot_obstruct_general_climate():
    r=evaluate(pos=positions(Jupiter=10,Rahu=305,Ketu=125))
    assert r['general_gochara']['Jupiter']['status']=='favorable'


@pytest.mark.parametrize('source',range(12))
def test_jaimini_aspects_are_distinct(source):
    expected={t for t in range(12) if t!=source and (
        source%3==2 and t%3==2 or source%3==0 and t%3==1 and t!=(source+1)%12 or
        source%3==1 and t%3==0 and t!=(source-1)%12)}
    assert {t for t in range(12) if rashi_aspect(source,t)}==expected
    assert all(not jaimini_operators('Rahu',source,t) for t in range(12) if t!=source)


def test_dk_restrictions_and_operator_labels():
    r=evaluate(pos=positions(Sun=10,Mercury=10,Jupiter=10,Saturn=10))
    dk=[a for a in r['evidence'] if 'DK' in a['roles']]
    assert dk
    for a in dk:
        if a['actor'] not in ('Jupiter','Saturn'):
            assert 'positive_ul_dk' not in a['feature_roles'] and 'saturn_stress' not in a['feature_roles']
    operators={a['operator'] for a in r['evidence']}
    assert 'parashari_graha_drishti' in operators
    assert not any(op=='aspect' for op in operators)
    assert all(a['status']=='excluded' and not a['feature_roles'] for a in r['evidence'] if 'diagnostic' in a['layers'])


def test_canonical_aliases_and_nodes():
    b=EvidenceBook(AT)
    a=b.add('Jupiter','sign:4','natal D1','sign_conjunction','structural','seventh lord','a')
    d=b.add('Jupiter','sign:4','natal UL/DK','sign_conjunction','ul_dk','UL','b')
    assert a==d and len(b.atoms)==1 and len(b.redundant)==1
    assert b.atoms[a]['roles']==['seventh lord','UL']
    assert actor_group('Rahu')==actor_group('Ketu')=='Nodes'


@pytest.mark.parametrize('period_actor,transit_actor,passes',[('Jupiter','Jupiter',False),('Venus','Jupiter',True),('Rahu','Ketu',False)])
def test_two_actors_only_from_gate_witnesses(period_actor,transit_actor,passes):
    b=EvidenceBook(AT)
    atom(b,period_actor,'partnership_period','period');atom(b,transit_actor,'jupiter_support')
    atom(b,'Moon','d9_corroboration','d9');atom(b,'Mars','partner_trigger','trigger')
    r=assess(b)['partner_entry']
    assert r['architecture_active']==passes
    assert r['gates']['two_distinct_gate_actors']==passes


def test_d1_d9_same_planet_not_two_actors():
    b=EvidenceBook(AT)
    for f in ('partnership_period','d9_corroboration'):atom(b,'Jupiter',f,'period')
    atom(b,'Jupiter','jupiter_support')
    assert not assess(b)['partner_entry']['architecture_active']


def test_positive_and_stress_coexist_and_no_certainty():
    r=evaluate()
    assert r['assessments']['partner_entry']['architecture_active']
    assert r['assessments']['stress']['architecture_active']
    assert 'separation' not in r['assessments']['stress']['state']
    assert r['assessments']['commitment']['architecture_active']
    assert all('score' not in a and 'probability' not in a for a in r['assessments'].values())


def test_diagnostic_cannot_override_failed_structure_and_no_legacy_occupancy():
    r=evaluate(pos=positions(Jupiter=194))
    assert any(a['operator']=='diagnostic_degree_conjunction' for a in r['evidence'])
    assert not r['assessments']['partner_entry']['architecture_active']
    assert not any('D1 Lagna occupancy' in a['feature_roles'] for a in r['evidence'])
    assert r['general_gochara']['Jupiter']['house_from_lagna']==7
    assert r['general_gochara']['Jupiter']['house_from_moon']==8


def test_complete_audit_serializes_and_input_errors():
    r=evaluate();json.dumps(r,default=str)
    for a in r['evidence']:
        assert {'actor','target','reference','operator','interval','eligible_categories','layers','dependency_group','status','reason','category_use'}<=a.keys()
    assert r['version']==VERSION
    with pytest.raises(ValueError):analyze_v2(chart(),AT.replace(tzinfo=None))
    c=chart();c.planets['Sun'].longitude=float('nan')
    with pytest.raises(ValueError):evaluate(c)


def test_window_boundaries_with_fabricated_motion_and_periods():
    start=AT;end=AT+timedelta(hours=4)
    def motion(at,ayanamsa):
        h=(at-AT).total_seconds()/3600
        return positions(Moon=29+h)
    def fake_periods(*args):
        at=args[-1];boundary=AT+timedelta(hours=2,minutes=30)
        nxt=boundary if at<boundary else end+timedelta(days=1)
        return tuple(HierarchyPeriod(level,p,start-timedelta(days=1),nxt,'Venus') for level,p in zip(('MD','AD','PD'),('Venus','Venus','Mars')))
    bounds=discover_boundaries(chart(),start,end,position_provider=motion,period_provider=fake_periods)
    assert AT+timedelta(hours=1) in bounds
    assert AT+timedelta(hours=2,minutes=30) in bounds
    out=scan_v2(chart(),start,end,position_provider=motion,period_provider=fake_periods)
    assert out['boundaries']==bounds
    assert out['segments'][-1]['end']==end


def test_windows_no_gap_fill_and_triggers_inside_only():
    r=evaluate();off=deepcopy(r)
    off['broad_periods']={k:False for k in off['broad_periods']}
    for a in off['assessments'].values():a['architecture_active']=False;a['trigger_active']=True
    segments=[{'start':AT+timedelta(hours=i),'end':AT+timedelta(hours=i+1),'result':x} for i,x in enumerate((r,off,r))]
    out=windows_from_segments(segments)
    entry=[w for w in out if w['kind']=='partner_entry']
    assert len(entry)==2 and all(w['end']-w['start']==timedelta(hours=1) for w in entry)
    assert not any(w['start']==AT+timedelta(hours=1) for w in out)


@pytest.mark.parametrize('md,ad,pd,expected',[
 ('Mercury','Saturn','Moon',False),('Mars','Saturn','Moon',True),
 ('Mercury','Mars','Saturn',True),('Mercury','Mercury','Saturn',False)])
def test_stress_period_requires_partnership_link(md,ad,pd,expected):
    b=EvidenceBook(AT);activate_periods(role_natal(),periods(md,ad,pd),b)
    assert bool(b.features.get('stress_period'))==expected


def test_commitment_requires_continuity_and_d9_separately():
    b=EvidenceBook(AT);atom(b,'Venus','partnership_period','period');atom(b,'Jupiter','jupiter_support')
    atom(b,'Jupiter','positive_ul_dk','ul_dk')
    assert assess(b)['partner_entry']['architecture_active']
    assert set(assess(b)['commitment']['gates_failed']) >= {'d9_corroboration','continuity'}
    atom(b,'Venus','d9_corroboration','period');atom(b,'Mars','continuity','period')
    assert assess(b)['commitment']['state']=='commitment architecture active'


def test_synthetic_station_loop_not_missed_with_equal_endpoint_signs():
    def motion(at,ayanamsa):
        h=(at-AT).total_seconds()/3600
        out=positions();out['Moon']=PlanetPosition('Moon',29+8*h*(1-h),8-16*h,h>0.5)
        return out
    bounds=discover_boundaries(chart(),AT,AT+timedelta(hours=1),position_provider=motion,period_provider=lambda *a:periods())
    assert len(bounds)==4  # start, entry, reverse exit, end
    assert 500 < (bounds[1]-AT).total_seconds() < 600
    assert 3000 < (bounds[2]-AT).total_seconds() < 3200


def test_venus_trigger_cannot_bypass_vedha_by_natal_sign_match():
    c=chart();c.planets['Venus'].longitude=10
    r=evaluate(c,pos=positions(Venus=10,Mercury=150)) # H2 favorable, vedha H7 occupied by Mercury.
    assert r['general_gochara']['Venus']['status']=='favorable but obstructed'
    assert not any(a['actor']=='Venus' and 'romance_trigger' in a['feature_roles'] for a in r['evidence'])


def test_ul_rashi_drishti_and_actor_context_are_auditable():
    c=chart();b=EvidenceBook(AT);n=build_natal(c,b)
    # A constructed UL sign isolates the operator without modifying shared UL calculation.
    n['ul_sign']=4;n['ul_second_sign']=5;n['dk_signs']=[8]
    pos=positions(Jupiter=0,Saturn=0,Sun=0)
    climate=compute_climate(c,pos,b);pd=activate_periods(n,periods(),b)
    activate_transits(c,n,pos,climate,pd,b)
    assert any(a['actor']=='Jupiter' and a['operator']=='jaimini_rashi_drishti' and 'UL' in a['roles'] for a in b.atoms.values())
    assert not any(a['actor']=='Sun' and 'positive_ul_dk' in a['feature_roles'] for a in b.atoms.values())


def test_no_extra_astronomy_and_provider_ayanamsa():
    c=chart();c.ayanamsa='Raman';calls=[]
    def provider(at,ayanamsa):calls.append(ayanamsa);return positions()
    analyze_v2(c,AT,position_provider=provider,period_provider=lambda *a:periods())
    assert calls==['Raman']
