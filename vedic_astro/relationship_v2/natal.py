"""Natal role interpretation; consumes normal D1 and shared UL/DK/D9 metadata."""
from math import isfinite
from ..constants import GRAHAS, RASHIS
from ..relationships import indicators, SIGN_LORDS
from ..util import rashi_index
from .geometry import sign_operators


def build_natal(chart, book):
    if set(chart.planets) != set(GRAHAS):
        raise ValueError('A complete nine-graha natal chart is required')
    if not all(isfinite(v.longitude) for v in chart.planets.values()) or not isfinite(chart.ascendant_longitude):
        raise ValueError('Natal longitudes must be finite')
    meta = indicators(chart)  # Shared natal-only UL/DK/D9; never legacy scoring.
    lagna = rashi_index(chart.ascendant_longitude)
    signs = {p:rashi_index(v.longitude) for p,v in chart.planets.items()}
    lords = {h:SIGN_LORDS[(lagna+h-1)%12] for h in range(1,13)}
    d9signs = {p:RASHIS.index(v['rashi']) for p,v in meta['d9_placements'].items()}
    def house_set(h, reference_signs, root, ruler):
        target=(root+h-1)%12
        return {ruler} | {p for p,s in reference_signs.items() if sign_operators(p,s,target)}
    partner = house_set(7,signs,lagna,lords[7])
    romance = house_set(5,signs,lagna,lords[5]) | {'Venus'}
    def connected(p,q):
        return bool(sign_operators(p,signs[p],signs[q])) or (
            SIGN_LORDS[signs[p]]==q and SIGN_LORDS[signs[q]]==p)
    support = {'Venus',*meta['darakaraka'],SIGN_LORDS[RASHIS.index(meta['ul_sign'])]}
    support |= {p for p in signs if connected(p,lords[7])}
    # Jupiter is not added merely because it is a natural benefic.
    difficulty = {'Saturn','Mars','Ketu',lords[6],lords[8],lords[12]}
    d9partner = house_set(7,d9signs,RASHIS.index(meta['d9_lagna']),meta['d9_seventh_lord'])
    d9eligible = d9partner | {p for p,s in d9signs.items() if s in (
        d9signs['Venus'],d9signs[meta['d9_seventh_lord']])}
    ul=RASHIS.index(meta['ul_sign']);ul2=(ul+1)%12
    continuity={SIGN_LORDS[ul],SIGN_LORDS[ul2]}
    if lords[2] in partner or any(connected(lords[2],q) for q in partner):
        continuity.add(lords[2])
    def explanations(role,p):
        if role in ('romance','partner_direct'):
            h=5 if role=='romance' else 7;target=(lagna+h-1)%12
            why=[]
            if p==lords[h]:why.append(f'D1 house {h} lord')
            if p=='Venus' and role=='romance':why.append('Venus natural romance role')
            why.extend(f'{operator} to D1 house {h}' for operator in sign_operators(p,signs[p],target))
            return why
        if role=='partner_support':
            why=[]
            if p=='Venus':why.append('Venus partnership support')
            if p in meta['darakaraka']:why.append('Natal Darakaraka')
            if p==SIGN_LORDS[ul]:why.append('Natal UL lord')
            if connected(p,lords[7]):why.append('One-step natal connection to D1 seventh lord')
            return why
        if role=='difficulty':return (['Named difficulty actor'] if p in ('Saturn','Mars','Ketu') else [])+[f'D1 house {h} lord' for h in (6,8,12) if p==lords[h]]
        if role=='d9_eligible':
            why=[]
            if p in d9partner:why.append('D9 seventh lord, occupant or full aspect to D9 seventh')
            if d9signs[p]==d9signs['Venus']:why.append('Shares natal D9 Venus sign')
            if d9signs[p]==d9signs[meta['d9_seventh_lord']]:why.append('Shares natal D9 seventh-lord sign')
            return why
        return (['UL lord'] if p==SIGN_LORDS[ul] else [])+(['Second-from-UL lord'] if p==SIGN_LORDS[ul2] else [])+(['D1 second lord connected to N-P'] if p==lords[2] and p in continuity else [])
    sets={'romance':romance,'partner_direct':partner,'partner_support':support,
          'difficulty':difficulty,'d9_eligible':d9eligible,'continuity':continuity}
    for role,actors in sets.items():
        for p in sorted(actors):
            book.add(p,f'planet:{p}', 'natal D9' if role=='d9_eligible' else 'natal D1',
                     'natal_role_membership','natal',role,'Natal eligibility annotation, not an independent timing witness.',
                     details={'d1_sign':signs[p],'d9_sign':d9signs[p],'eligibility_reasons':explanations(role,p)})
    return {'metadata':meta,'d1_signs':signs,'d1_lords':lords,'d9_signs':d9signs,
            'roles':sets,'ul_sign':ul,'ul_second_sign':ul2,
            'partnership_targets':[(lagna+6)%12,signs[lords[7]],signs['Venus']],
            'partnership_target_roles':['D1 seventh house','D1 seventh lord','natal Venus'],
            'dk_signs':sorted({signs[p] for p in meta['darakaraka']})}
