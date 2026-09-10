"""MD/AD/PD interpretations, no new Vimshottari calculation."""
from itertools import product


def activate_periods(natal, periods, book):
    roles=natal['roles'];rows={p.level:p for p in periods};ids={}
    for level,p in rows.items():
        ids[level]=book.add(p.lord,f'period:{level}','natal Moon nakshatra','vimshottari',
                           'period',level,'Normal Vimshottari period; roles are not separate actors.',
                           interval=[p.start.isoformat(),p.end.isoformat()],
                           details={'natal_roles':[k for k,v in roles.items() if p.lord in v]})
    def has(level,role):return level in rows and rows[level].lord in roles[role]
    def emit(name,*levels):book.feature(name,[ids[level] for level in levels])
    if has('AD','romance'):
        for other in ('MD','PD'):
            if has(other,'romance'):emit('romance_period','AD',other)
    if has('AD','partner_direct'):emit('partnership_period','AD')
    if has('AD','partner_support'):
        for other in ('MD','PD'):
            if has(other,'partner_direct'):emit('partnership_period','AD',other)
    if has('AD','partner_direct') and has('AD','difficulty'):emit('stress_period','AD')
    if has('AD','difficulty'):
        for other in ('MD','PD'):
            if has(other,'partner_direct'):emit('stress_period','AD',other)
    if has('AD','partner_direct') and has('PD','difficulty'):emit('stress_period','AD','PD')
    for level in ('AD','PD'):
        if has(level,'d9_eligible'):emit('d9_corroboration',level)
        if has(level,'continuity'):emit('continuity',level)
    return {'active':list(rows.values()),'background_md_roles':
            [role for role in roles if has('MD',role)],'evidence_ids':ids}
