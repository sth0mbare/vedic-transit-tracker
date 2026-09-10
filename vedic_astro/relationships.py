"""Deterministic relationship indicators. Rules are descriptive, not predictions."""
from dataclasses import asdict, dataclass
from datetime import timedelta
from collections import defaultdict
from statistics import median
from math import ceil

from .relationship_endings import ending_activations, RULE_SPEC as ENDING_RULES
from .constants import RASHIS
from .ephemeris import get_planet_positions
from .navamsa import compute_navamsa_chart, _navamsa_sign_index
from .timing import birth_balance, dasha_at, utc
from .util import rashi_index, rashi_name, house_from_sign, angular_separation

SIGN_LORDS = ('Mars','Venus','Mercury','Moon','Sun','Mercury',
              'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter')
REL_HOUSES = (1,5,7,8,11)
CLASSICAL = ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn')
ASPECTS = {p: (7,) for p in CLASSICAL}
ASPECTS.update(Mars=(4,7,8), Jupiter=(5,7,9), Saturn=(3,7,10))
RULE_VERSION = 'Relationship Timing Rules v1.0'
RULES = {
    'version': RULE_VERSION,
    'ending_separation': ENDING_RULES,
    'houses': 'Whole-sign houses; classical sign lords (Mars for Scorpio, Saturn for Aquarius).',
    'darakaraka': 'Lowest unrounded degree within sign among Sun through Saturn; nodes excluded. Exact ties reported together.',
    'upapada': 'Arudha of D1 house 12: repeat sign distance to its lord. If result is 1st/7th from house 12, move 10th from that result.',
    'aspects': 'Whole-sign full graha drishti: 7th for seven classical planets; Mars 4/8, Jupiter 5/9, Saturn 3/10. No node drishti.',
    'contacts': 'Conjunction/opposition within user-selected orb, shortest angular distance. Not the same as whole-sign drishti.',
    'd9': 'Projected transit D9 sign co-occupation with natal D9 points; a divisional rule, not physical sky contact. No degree orbs in D9.',
    'dasha': 'MD/AD/PD from stored birth Moon, 365.2425 days/year; start inclusive, end exclusive.',
    'scoring': 'One point per eligible family (0–6), never per contact. Require dasha plus a slow-planet degree contact, at least 3 families, and a distinct source planet assignable to each of at least 3 families. Future samples must also exceed the preceding 90-day median and meet its 75th percentile. These are declared heuristics, not probabilities.',
    'eligible': 'Dasha: 5th/7th lord or Venus/Jupiter. House: Jupiter/Saturn occupying 5/7. Slow: Jupiter/Saturn degree contact to 5th/7th lord, Venus/Jupiter. Fast: Venus/Mars degree contact to those points. D9: Jupiter/Saturn projected into D9 seventh sign or seventh lord sign. UL/DK: Jupiter/Saturn co-occupying UL sign, or degree contact to Darakaraka. Other facts are context only.',
    'categories': 'Meeting/dating targets: house5, house11, Venus, Mars. Formation: these plus house7, Jupiter, UL, Darakaraka. Commitment: house7, Jupiter, UL, Darakaraka. D9 seventh lord is treated as house7. House1/8 and Moon/nodes are displayed as context only.',
    'sampling': 'Future scan is daily at the chosen UTC time. At least two consecutive qualifying samples form a window; isolated samples are reported separately. Intraday crossings and short windows may be missed; endpoints are samples, not exact ingress times.',
}


def arudha_sign(base, lord_sign):
    raw = (lord_sign + (lord_sign - base) % 12) % 12
    return (raw + 9) % 12 if (raw - base) % 12 in (0,6) else raw


def indicators(chart):
    lagna = rashi_index(chart.ascendant_longitude)
    d9 = compute_navamsa_chart(chart)
    d9lagna = RASHIS.index(d9.ascendant_rashi)
    degrees = {p: chart.planets[p].longitude % 30 for p in CLASSICAL}
    lowest = min(degrees.values())
    dk = [p for p, degree in degrees.items() if degree == lowest]
    base = (lagna + 11) % 12
    lord = SIGN_LORDS[base]
    lord_sign = rashi_index(chart.planets[lord].longitude)
    ul = arudha_sign(base, lord_sign)
    return {
        'd1_lords': {h: SIGN_LORDS[(lagna+h-1)%12] for h in REL_HOUSES},
        'd1_house_details': [{'house':h,'sign':RASHIS[(lagna+h-1)%12],
            'lord':SIGN_LORDS[(lagna+h-1)%12],
            'lord_longitude':chart.planets[SIGN_LORDS[(lagna+h-1)%12]].longitude,
            'lord_house':chart.planets[SIGN_LORDS[(lagna+h-1)%12]].house} for h in REL_HOUSES],
        'd9_lagna': d9.ascendant_rashi, 'd9_lagna_lord': SIGN_LORDS[d9lagna],
        'd9_seventh': RASHIS[(d9lagna+6)%12], 'd9_seventh_lord': SIGN_LORDS[(d9lagna+6)%12],
        'd9_placements': {p: asdict(v) for p,v in d9.planets.items()},
        'darakaraka': dk, 'darakaraka_degrees': degrees,
        'ul_sign': RASHIS[ul], 'ul_house': (ul-lagna)%12+1,
        'ul_trace': {'house12_sign':RASHIS[base], 'lord':lord,
                     'lord_longitude':chart.planets[lord].longitude,
                     'lord_sign':RASHIS[lord_sign], 'inclusive_distance':(lord_sign-base)%12+1,
                     'raw_sign':RASHIS[(2*lord_sign-base)%12], 'final_sign':RASHIS[ul]},
    }


def contact_rows(sources, targets, orb=3.0):
    """Directed contacts. targets maps labels to actual longitudes, never invented UL degrees."""
    if not 0 <= orb <= 10:
        raise ValueError('Contact orb must be between 0 and 10 degrees')
    rows=[]
    for name, lon in sources.items():
        for target, target_lon in targets.items():
            sep=angular_separation(lon,target_lon)
            offset=house_from_sign(target_lon,lon)
            kinds=[]
            if sep<=orb: kinds.append(('conjunction',sep))
            if 180-sep<=orb: kinds.append(('opposition',180-sep))
            if offset in ASPECTS.get(name,()): kinds.append((f'whole-sign aspect {offset}',None))
            for kind, deviation in kinds:
                rows.append({'source':name,'target':target,'kind':kind,
                             'source_longitude':lon,'target_longitude':target_lon,
                             'source_sign':rashi_name(lon),'target_sign':rashi_name(target_lon),
                             'separation':sep,'orb_deviation':deviation,
                             'rule':RULES['aspects'] if deviation is None else f'Degree contact within {orb}°'})
    return rows


@dataclass(frozen=True)
class Activation:
    signature: str
    family: str
    source: str
    target: str
    categories: tuple
    detail: str
    score_eligible: bool = False


def categories_for(target):
    if target in ('house5','house11','Venus','Mars'):
        return ('meeting/dating','relationship formation')
    if target in ('house7','Jupiter','UL','Darakaraka'):
        return ('relationship formation','commitment/marriage')
    if target == '7th lord':
        return ('relationship formation','commitment/marriage')
    return ()


def score_activations(facts):
    result={}
    for category in ('meeting/dating','relationship formation','commitment/marriage'):
        relevant=[f for f in facts if category in f.categories and f.score_eligible]
        families=sorted({f.family for f in relevant})
        sources=sorted({f.source for f in relevant})
        # Maximum family-to-source matching prevents one planet supplying a whole stack.
        matches={}
        def assign(family, seen):
            for source in sorted({f.source for f in relevant if f.family==family}):
                if source in seen: continue
                seen.add(source)
                if source not in matches or assign(matches[source], seen):
                    matches[source]=family
                    return True
            return False
        for family in families: assign(family,set())
        result[category]={'score':len(families), 'independent_source_count':len(matches),'families':families,'source_planets':sources,
                          'flagged':len(families)>=3 and len(matches)>=3 and 'dasha' in families and 'slow' in families,
                          'signatures':sorted({f.signature for f in relevant})}
    return result


def analyze(chart, at, orb=3.0):
    at=utc(at)
    meta=indicators(chart)
    positions=get_planet_positions(at,chart.ayanamsa)
    sources={p:v.longitude for p,v in positions.items()}
    targets={p:v.longitude for p,v in chart.planets.items()}
    targets['Lagna']=chart.ascendant_longitude
    contacts=contact_rows(sources,targets,orb)
    transit_rows=[{'planet':p,'longitude':v.longitude,'sign':rashi_name(v.longitude),
                   'degree_in_sign':v.longitude%30,
                   'natal_house':house_from_sign(v.longitude,chart.ascendant_longitude),
                   'retrograde':v.retrograde,'speed_deg_day':v.speed} for p,v in positions.items()]
    facts={}
    def add(family,source,target,kind,detail,eligible=False):
        key=f'{family}|{source}|{target}|{kind}'
        facts[key]=Activation(key,family,source,target,categories_for(target),detail,eligible)
    periods=() if at<chart.birth_datetime_utc else dasha_at(chart.birth_datetime_utc,chart.planets['Moon'].longitude,at)
    for period in periods:
        p=period.lord
        roles=[f'house{h}' for h,l in meta['d1_lords'].items() if l==p]
        if p in ('Venus','Jupiter','Moon','Mars','Rahu','Ketu'): roles.append(p)
        if p in meta['darakaraka']: roles.append('Darakaraka')
        if p == SIGN_LORDS[RASHIS.index(meta['ul_sign'])]: roles.append('UL')
        if p in (meta['d9_lagna_lord'],meta['d9_seventh_lord'],'Venus','Jupiter') or meta['d9_placements'][p]['house'] in (1,7):
            add('dasha',p,'D9 placement',period.level,
                f"{period.level} lord {p} occupies natal D9 {meta['d9_placements'][p]['rashi']}, house {meta['d9_placements'][p]['house']}; D9 Lagna lord {meta['d9_lagna_lord']}, seventh lord {meta['d9_seventh_lord']}. Context only, not an independent score.")
        for role in roles:
            add('dasha',p,role,period.level, f'{period.level} {p}: {period.start.isoformat()} to {period.end.isoformat()}; D1 role {role}', role in ('house5','house7','Venus','Jupiter'))
    for row in transit_rows:
        if row['natal_house'] in REL_HOUSES:
            h=row['natal_house']
            add('house',row['planet'],f'house{h}','occupancy',f"{row['longitude']:.9f}° in natal house {h}", h in (5,7) and row['planet'] in ('Jupiter','Saturn'))
    for c in contacts:
        p,t=c['source'],c['target']
        roles=[f'house{h}' for h,l in meta['d1_lords'].items() if l==t]
        if t in ('Venus','Jupiter','Moon','Mars','Rahu','Ketu'): roles.append(t)
        if t in meta['darakaraka']: roles.append('Darakaraka')
        if t=='Lagna': roles.append('house1')
        for role in roles:
            family='slow' if p in ('Jupiter','Saturn') else 'fast' if p in ('Venus','Mars') else 'house'
            if role=='Darakaraka': family='ul_dk'
            add(family,p,role,f"{c['kind']}:{t}",f"{p} {c['kind']} natal {t} ({role}); separation {c['separation']:.9f}°", c['orb_deviation'] is not None and (role=='Darakaraka' or (p in ('Jupiter','Saturn','Venus','Mars') and role in ('house5','house7','Venus','Jupiter'))))
    ul=RASHIS.index(meta['ul_sign'])
    for p,lon in sources.items():
        distance=(ul-rashi_index(lon))%12+1
        if distance==1 or distance in ASPECTS.get(p,()):
            add('ul_dk',p,'UL',f'sign-{distance}',f"{p} at {lon:.9f}°; UL {meta['ul_sign']}; sign count {distance}", distance==1 and p in ('Jupiter','Saturn'))
    d9=compute_navamsa_chart(chart)
    d9targets={'Lagna':d9.ascendant_rashi,'house7':meta['d9_seventh'],
               'Lagna lord':d9.planets[meta['d9_lagna_lord']].rashi,
               '7th lord':d9.planets[meta['d9_seventh_lord']].rashi,
               'Venus':d9.planets['Venus'].rashi,'Jupiter':d9.planets['Jupiter'].rashi}
    for p,lon in sources.items():
        sign=RASHIS[_navamsa_sign_index(lon)]
        for t,target_sign in d9targets.items():
            if sign==target_sign:
                add('d9',p,t,'projected-sign',f"Transit D1 {lon:.9f}° projects to D9 {sign}, sharing natal D9 {t}'s sign", p in ('Jupiter','Saturn') and t in ('house7','7th lord'))
    facts=list(facts.values())
    scores = score_activations(facts)
    ending_score, ending_evidence, ending_natal = ending_activations(
        chart, meta, periods, transit_rows, contacts, SIGN_LORDS, ASPECTS)
    scores['ending/separation'] = ending_score
    return {'at_utc':at.isoformat(),'ayanamsa':chart.ayanamsa,'rules':RULES,'orb':orb,
            'natal':meta,'natal_d1':asdict(chart),'birth_dasha_balance':birth_balance(chart.planets['Moon'].longitude),'dashas':[asdict(p) for p in periods],
            'transits':transit_rows,'contacts':contacts,
            'activations':[asdict(f) for f in facts] + ending_evidence,'scores':scores,
            'ending_natal':ending_natal}


def repeated_signatures(event_results):
    """Count distinct event IDs, not duplicate rows or selected copies of an event."""
    groups=defaultdict(dict)
    for event_id,result in event_results:
        for fact in result['activations']:
            groups[fact['signature']][event_id]=fact['detail']
    return [{'signature':s,'event_count':len(events),'event_ids':list(events),
             'evidence':events} for s,events in sorted(groups.items()) if len(events)>=2]


def scan_windows(chart,start,end,orb=3.0):
    start,end=utc(start),utc(end)
    if end<start or end-start>timedelta(days=1096):
        raise ValueError('Choose a forward interval of at most three years')
    if start<chart.birth_datetime_utc:
        raise ValueError('Scan must start after birth')
    samples=[]
    at=start
    while at<=end:
        result=analyze(chart,at,orb)
        samples.append(result)
        at+=timedelta(days=1)
    baseline_start=max(chart.birth_datetime_utc, start-timedelta(days=90))
    baseline=[]
    baseline_records=[]
    cursor=baseline_start
    while cursor<start:
        baseline_score=analyze(chart,cursor,orb)['scores']
        baseline.append(baseline_score)
        baseline_records.append({'at_utc':cursor.isoformat(),'scores':baseline_score})
        cursor+=timedelta(days=1)
    thresholds={}
    for category in samples[0]['scores']:
        values=sorted(r[category]['score'] for r in baseline)
        thresholds[category]={'median':median(values) if values else None,
                              'p75':values[ceil(.75*len(values))-1] if values else None}
    windows=[]
    for category in samples[0]['scores']:
        active=None
        for result in samples:
            score=result['scores'][category]
            threshold=thresholds[category]
            if score['flagged'] and threshold['median'] is not None and score['score']>threshold['median'] and score['score']>=threshold['p75']:
                if active is None:
                    active={'category':category,'first_sample':result['at_utc'],
                            'last_sample':result['at_utc'],'samples':[]}
                    windows.append(active)
                active['last_sample']=result['at_utc']
                active['samples'].append({'at_utc':result['at_utc'],**score,
                    'transits':result['transits'],'dashas':result['dashas'],
                    'evidence':[f for f in result['activations'] if category in f['categories']]})
            else: active=None
    isolated=[w for w in windows if len(w['samples'])==1]
    windows=[w for w in windows if len(w['samples'])>=2]
    return {'orb':orb,'natal_d1':asdict(chart),'natal_indicators':indicators(chart),
            'baseline_daily_scores':baseline_records,'daily_scores':[{'at_utc':s['at_utc'],'scores':s['scores']} for s in samples],
            'isolated_samples':isolated,'baseline_start':baseline_start.isoformat(),'baseline_samples':len(baseline),'thresholds':thresholds,'windows':windows,'sample_count':len(samples),'rules':RULES}


def analyze_event(chart, event, orb=3.0):
    result = analyze(chart, event.instant(), orb)
    result['event'] = asdict(event)
    result['input_timezone'] = event.timezone
    result['time_precision'] = 'entered event time' if event.clock else 'unknown time: local noon assumed; provisional'
    return result
