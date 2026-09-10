"""Reuse trusted Parashari geometry; explicitly separate new Jaimini operator."""
from ..relationships import contact_rows


def sign_operators(actor, source_sign, target_sign):
    if source_sign == target_sign:
        return ('sign_conjunction',)
    # Representative sign origins only: no physical degree contact is asserted.
    rows = contact_rows({actor:source_sign*30}, {'sign':target_sign*30}, 0)
    return tuple('parashari_graha_drishti' for r in rows if r['orb_deviation'] is None)


def rashi_aspect(source, target):
    if source == target:
        return False
    a,b = source % 3, target % 3
    if a == 2:
        return b == 2
    if a == 0:
        return b == 1 and target != (source+1)%12
    return b == 0 and target != (source-1)%12


def jaimini_operators(actor, source, target):
    if source == target:
        return ('sign_conjunction',)
    if actor not in ('Rahu','Ketu') and rashi_aspect(source,target):
        return ('jaimini_rashi_drishti',)
    return ()
