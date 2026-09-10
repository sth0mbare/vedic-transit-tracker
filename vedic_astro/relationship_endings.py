"""Frozen v1.0 ending/separation heuristics, independent of event labels/outcomes.

Consumes already calculated positions and periods. No ephemeris calls. See
 docs/relationship-rules-v1.0.md for exact eligibility and counting conventions.
"""
from functools import lru_cache

from .constants import RASHIS
from .navamsa import _navamsa_sign_index
from .util import rashi_index, house_from_sign

CATEGORY = 'ending/separation'
FAMILIES = ('dasha', 'slow', 'house', 'd9', 'ul_dk', 'fast')
DISRUPTORS = ('Saturn', 'Ketu', 'Mars')
SLOW = ('Saturn', 'Ketu')
TRIGGERS = ('Moon', 'Mars', 'Venus')
DIFFICULT_HOUSES = (6, 8, 12)
RULE_SPEC = {
    'dasha': 'Active MD/AD/PD lord must have BOTH a disruption role (Saturn/Ketu/Mars, D1 6/8/12 lord or occupant) AND a partnership role (Venus, D1/D9 seventh lord, DK, UL lord, or D1/D9 seventh-house occupant). Repeated period lords count once.',
    'slow': 'Saturn/Ketu degree conjunction or opposition to natal Venus, D1 seventh lord or Lagna. Whole-sign-only aspects are context.',
    'house': 'Saturn/Ketu/Mars in D1 house 1 or 7. Occupancy of 6/8/12 counts only with a simultaneous degree contact to natal Venus or D1 seventh lord by the same planet; otherwise context.',
    'd9': 'Saturn/Ketu/Mars projected into the natal D9 seventh-house, seventh-lord or Venus sign. Shared target signs merge. No degree orbs or physical sky aspect claims.',
    'ul_dk': 'Saturn/Ketu/Mars co-occupy UL sign or have a degree conjunction/opposition to DK. Whole-sign-only aspects to UL/DK are context. DK aliases merge with other roles of that planet.',
    'fast': 'Mars degree conjunction/opposition to natal Venus or D1 seventh lord. Moon/Venus degree contacts to those same targets are neutral timing triggers eligible only when both dasha and slow families are eligible. Moon/Venus contacts to natal Ketu/Saturn/Mars and house occupancy are context only.',
    'counting': 'Maximum matching, one point per distinct family AND distinct source planet (0–6). One planet contributes at most one point across all families, including its dasha and transit roles. Equal-size matchings prefer dasha+slow together; remaining ties use fixed family and condition-ID order. One representative condition per matched family/source counts; all remaining evidence is supporting context.',
    'stacking': 'Flag requires at least 3 matched families/sources including matched dasha and slow. Low 0–1, Moderate 2–3, High 4–6, same numeric display bands as existing categories. Fast triggers alone cannot qualify. These are operational diversity constraints, not statistical independence.',
    'scope': 'Pressure, detachment or restructuring indicators; cannot distinguish a definitive breakup from a relationship that adapts. No label, outcome, person, date exception, benefic cancellation, automatic tuning or learning. Ayanamsha and user-selected orb are recorded inputs; compare using the same settings.',
}


def score_ending_evidence(evidence):
    """Deterministic maximum family/source matching with explicit counted records."""
    rows = {r['signature']: dict(r) for r in evidence}
    eligible = [r for r in rows.values() if r['eligible']]
    actors = sorted({r['source'] for r in eligible})
    bits = {p: 1 << i for i, p in enumerate(actors)}
    choices = {}
    for family in FAMILIES:
        by_source = {}
        for row in sorted(eligible, key=lambda r: r['signature']):
            if row['family'] == family:
                by_source.setdefault(row['source'], row['signature'])
        choices[family] = sorted(by_source.items())

    @lru_cache(None)
    def match(index, used, has_dasha=False, has_slow=False):
        if index == len(FAMILIES):
            return ()
        family = FAMILIES[index]
        options = [match(index+1, used, has_dasha, has_slow)]
        for actor, signature in choices[family]:
            if not used & bits[actor]:
                options.append((signature,) + match(index+1, used | bits[actor],
                    has_dasha or family == 'dasha', has_slow or family == 'slow'))
        # Include already selected required families when evaluating suffix ties.
        def value(selection):
            fam = {rows[s]['family'] for s in selection}
            return (len(selection), int((has_dasha or 'dasha' in fam) and
                                       (has_slow or 'slow' in fam)))
        best_rank = max(map(value, options))
        return min(s for s in options if value(s) == best_rank)

    selected = set(match(0, 0))
    families = sorted({rows[s]['family'] for s in selected})
    for signature, row in rows.items():
        row['counted'] = signature in selected
        row['score_eligible'] = row['counted']
        row['status'] = 'Counted indicator' if row['counted'] else 'Supporting context'
        row['counting_note'] = ('One independent family/source point.' if row['counted'] else
            'Eligible evidence, but no extra point: family or planet already represented.' if row['eligible'] else
            'Context only under the frozen eligibility rules.')
    return ({'score':len(selected), 'independent_source_count':len(selected),
             'eligible_family_count':len({r['family'] for r in eligible}),
             'families':families, 'source_planets':sorted({rows[s]['source'] for s in selected}),
             'flagged':len(selected)>=3 and {'dasha','slow'} <= set(families),
             'signatures':sorted(selected)}, sorted(rows.values(), key=lambda r:r['signature']))


def ending_activations(chart, meta, periods, transits, contacts, sign_lords, aspects):
    """Generate candidates from astronomy only, then assign independent points."""
    facts = {}
    def add(family, source, condition, target, detail, eligible):
        signature = f'ending|{family}|{source}|{condition}'
        facts[signature] = dict(signature=signature, condition_id=condition,
            family=family, source=source, target=target, categories=(CATEGORY,),
            detail=detail, eligible=eligible)

    lagna = rashi_index(chart.ascendant_longitude)
    lords = {h:sign_lords[(lagna+h-1)%12] for h in (1,6,7,8,12)}
    partner_roles = {'Venus', lords[7], meta['d9_seventh_lord'],
                     sign_lords[RASHIS.index(meta['ul_sign'])], *meta['darakaraka']}
    for period in periods:
        p = period.lord
        natal_house = house_from_sign(chart.planets[p].longitude, chart.ascendant_longitude)
        disruption = p in DISRUPTORS or p in {lords[h] for h in DIFFICULT_HOUSES} or natal_house in DIFFICULT_HOUSES
        partnership = p in partner_roles or natal_house == 7 or meta['d9_placements'][p]['house'] == 7
        add('dasha',p,period.level,'dasha',
            f'{period.level} lord {p}: {period.start.isoformat()} to {period.end.isoformat()}; '
            f'D1 house {natal_house}; D1 lordships {[h for h,lord in lords.items() if lord==p]}; '
            f'partnership role {partnership}; disruption role {disruption}.', disruption and partnership)

    core = {'Venus', lords[7]}
    # One actual contacted planet is one target, even when it has several roles.
    for c in contacts:
        source, target = c['source'], c['target']
        degree = c['orb_deviation'] is not None
        family = None
        if source in SLOW and target in core | {'Lagna'}:
            family = 'slow'
        elif source in TRIGGERS and target in core:
            family = 'fast'
        elif source in DISRUPTORS and target in meta['darakaraka']:
            family = 'ul_dk'
        elif source in ('Moon','Venus') and target in DISRUPTORS:
            family = 'fast'  # context, never a stand-alone ending signal
        if family:
            eligible = degree and (source in DISRUPTORS or target in core)
            add(family,source,f"{c['kind']}:{target}",target,
                f"Transiting {source}: {c['kind']} to natal {target}; separation {c['separation']:.9f}°. "
                + ('Degree contact.' if degree else 'Whole-sign connection, not necessarily an exact angle.'), eligible)

    for row in transits:
        p, lon, h = row['planet'], row['longitude'], row['natal_house']
        linked = any(c['source']==p and c['target'] in core and c['orb_deviation'] is not None for c in contacts)
        if p in DISRUPTORS + ('Moon','Venus') and h in (1,7,6,8,12):
            add('house',p,f'house{h}',f'house{h}',
                f'{p} was transiting natal house {h} at {lon:.9f}°; degree link to Venus/seventh lord: {linked}.',
                p in DISRUPTORS and (h in (1,7) or linked))
        if p not in DISRUPTORS:
            continue
        sign = RASHIS[_navamsa_sign_index(lon)]
        targets = {'7th house':meta['d9_seventh'],
                   '7th lord':meta['d9_placements'][meta['d9_seventh_lord']]['rashi'],
                   'Venus':meta['d9_placements']['Venus']['rashi']}
        roles = sorted(t for t,s in targets.items() if s == sign)
        if roles:
            add('d9',p,f'sign:{sign}','D9',
                f'{p}’s transit projects to D9 {sign}, sharing the natal D9 sign of {", ".join(roles)}. Divisional sign connection, not a physical sky contact.',True)
        distance = (RASHIS.index(meta['ul_sign']) - rashi_index(lon)) % 12 + 1
        if distance == 1 or distance in aspects.get(p,()):
            add('ul_dk',p,f'UL:sign-{distance}','UL',
                f'{p} at {lon:.9f}° {"co-occupies" if distance==1 else "casts a whole-sign aspect on"} Upapada Lagna in {meta["ul_sign"]}.',distance==1)

    background = all(any(f['family']==family and f['eligible'] for f in facts.values()) for family in ('dasha','slow'))
    for fact in facts.values():
        if fact['family']=='fast' and fact['source'] in ('Moon','Venus'):
            fact['eligible'] = fact['eligible'] and background
            fact['detail'] += f' Neutral timing trigger only; dasha-plus-slow background present: {background}.'
    score, evidence = score_ending_evidence(facts.values())
    return score, evidence, {'d1_lords':lords, 'difficult_houses':DIFFICULT_HOUSES,
                            'partnership_role_planets':sorted(partner_roles)}
