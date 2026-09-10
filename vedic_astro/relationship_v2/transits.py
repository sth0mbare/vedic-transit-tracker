"""Personalized natal transits, separate UL/DK operators and fast refinements."""
from ..util import rashi_index
from ..relationships import contact_rows
from .geometry import sign_operators, jaimini_operators
from .spec import PARAMETERS


def activate_transits(chart, natal, positions, climate, period_data, book):
    signs={p:rashi_index(v.longitude) for p,v in positions.items()}
    targets=list(zip(natal['partnership_targets'],natal['partnership_target_roles']))
    clear=lambda p:climate[p]['status']=='favorable'
    structural=[];ul_dk=[];trigger_ids=[]
    for p in ('Jupiter','Saturn'):
        for target,role in targets:
            for operator in sign_operators(p,signs[p],target):
                i=book.add(p,f'sign:{target}','natal D1',operator,'structural',role,
                    'Personalized natal-target activation; climate is a separate qualification.',
                    details={'climate_qualification':'supportive' if p=='Jupiter' and clear(p) else 'mixed' if p=='Jupiter' else 'activation/pressure'})
                structural.append(i)
                if p=='Jupiter' and clear(p):book.feature('jupiter_support',[i,climate[p]['evidence_id']])
                if p=='Saturn':book.feature('saturn_stress',[i])
    u_targets=[(natal['ul_sign'],'UL'),(natal['ul_second_sign'],'second from UL')]
    k_targets=[(s,'DK') for s in natal['dk_signs']]
    for p in positions:
        for target,role in u_targets+k_targets:
            operators=jaimini_operators(p,signs[p],target) if p in ('Jupiter','Saturn') else (
                ('sign_conjunction',) if signs[p]==target else ())
            for operator in operators:
                i=book.add(p,f'sign:{target}','natal UL/DK',operator,'ul_dk',role,
                    'Actor restrictions and polarity govern eligibility; not a generic aspect.',
                    details={'actor_policy':'structural' if p in ('Jupiter','Saturn') else 'secondary/fast/context'})
                ul_dk.append(i)
                if p=='Jupiter' and clear(p):book.feature('positive_ul_dk',[i,climate[p]['evidence_id']])
                if p=='Saturn':book.feature('saturn_stress',[i])
                if p in ('Rahu','Ketu') and role in ('UL','DK'):
                    book.feature('stress_reinforcement',[i])
                if p in ('Moon','Venus') and role in ('UL','DK'):
                    if p=='Moon' or clear('Venus'):
                        book.feature('partner_trigger',[i]);book.feature('stress_trigger',[i]);trigger_ids.append(i)
                    # UL/DK alone is not a Romance trigger unless its own specified rule also holds.
                if p=='Mars':
                    book.feature('stress_reinforcement',[i]);book.feature('stress_trigger',[i]);trigger_ids.append(i)
    # Nodes: occupancy only, one shared source group, never positive structural credit.
    for p in ('Rahu','Ketu'):
        for target,role in targets:
            if signs[p]==target:
                i=book.add(p,f'sign:{target}','natal D1','sign_conjunction','structural',role,
                           'Nodal change/intensity context; cannot establish positive structure.')
                book.feature('stress_reinforcement',[i]);structural.append(i)
    def trigger(p,target,reference,role,features,eligible=True):
        i=book.add(p,target,reference,'whole_sign_occupancy' if reference=='Moon / Chandra Lagna' else 'sign_conjunction',
                   'trigger',role,'Timing refinement only; category structure must independently qualify.',
                   status='contextual' if eligible else 'obstructed')
        if eligible:
            for f in features:book.feature(f,[i])
        trigger_ids.append(i)
    # Moon's seventh-house trigger is specified independently of general-climate vedha.
    if climate['Moon']['house_from_moon']==7:
        trigger('Moon','house:7','Moon / Chandra Lagna','T-Moon',('romance_trigger','partner_trigger','stress_trigger'))
    moon_targets={natal['d1_signs'][natal['d1_lords'][7]],natal['d1_signs']['Venus'],natal['ul_sign'],*natal['dk_signs']}
    if signs['Moon'] in moon_targets:
        trigger('Moon',f"sign:{signs['Moon']}",'natal D1','T-Moon',('romance_trigger','partner_trigger','stress_trigger'))
    if climate['Venus']['house_from_moon'] in (1,5,11):
        trigger('Venus',f"house:{climate['Venus']['house_from_moon']}",'Moon / Chandra Lagna','T-Venus-R',('romance_trigger',),clear('Venus'))
    rtargets={natal['d1_signs'][natal['d1_lords'][5]],natal['d1_signs']['Venus']}
    if signs['Venus'] in rtargets:
        trigger('Venus',f"sign:{signs['Venus']}",'natal D1','T-Venus-R',('romance_trigger',),clear('Venus'))
    ptargets={natal['d1_signs'][natal['d1_lords'][7]],natal['ul_sign'],*natal['dk_signs']}
    if signs['Venus'] in ptargets:
        trigger('Venus',f"sign:{signs['Venus']}",'natal D1','T-Venus-P',('partner_trigger','stress_trigger'),clear('Venus'))
    marstargets=rtargets|ptargets
    stress_targets=ptargets|{natal['d1_signs']['Venus'],natal['ul_second_sign']}
    if signs['Mars'] in marstargets|stress_targets:
        features=('stress_reinforcement','stress_trigger') if signs['Mars'] in stress_targets else ()
        trigger('Mars',f"sign:{signs['Mars']}",'natal D1','T-Mars',features)
    sun_levels=[p.level for p in period_data['active'] if p.level in ('AD','PD') and p.lord=='Sun']
    relevant_sun='Sun' in (natal['roles']['romance']|natal['roles']['partner_direct']|natal['roles']['partner_support'])
    if sun_levels and relevant_sun and signs['Sun'] in marstargets:
        trigger('Sun',f"sign:{signs['Sun']}",'natal D1','T-Sun contextual',())
    diagnostics=contact_rows({p:v.longitude for p,v in positions.items()},
                             {p:v.longitude for p,v in chart.planets.items()},PARAMETERS['degree_orb'])
    for c in diagnostics:
        if c['orb_deviation'] is None:
            continue
        book.add(c['source'],f"longitude:{c['target_longitude']:.17g}",'natal planetary longitude',
                 'diagnostic_degree_'+c['kind'],'diagnostic',c['target'],
                 'Degree diagnostics never qualify structural or trigger gates.',status='excluded',details=c)
    return {'structural_evidence':sorted(set(structural)), 'ul_dk_evidence':sorted(set(ul_dk)),
            'fast_evidence':sorted(set(trigger_ids))}
