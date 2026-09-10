"""Moon-house general climate, separate from relationship eligibility."""
from ..relationships import CLASSICAL
from ..transits import transit_houses
from .spec import VEDHA, VEDHA_EXCEPTIONS


def compute_climate(chart, positions, book):
    houses={p:transit_houses(chart,v.longitude) for p,v in positions.items()}
    out={}
    for p,row in houses.items():
        h=row['house_from_moon'];blockhouse=VEDHA.get(p,{}).get(h)
        blockers=sorted(q for q in CLASSICAL if q!=p and q!=VEDHA_EXCEPTIONS.get(p)
                        and blockhouse is not None and houses[q]['house_from_moon']==blockhouse)
        status='favorable but obstructed' if blockers else 'favorable' if blockhouse is not None else 'other/non-favorable'
        reason='General Moon-based climate only; does not establish a relationship window.'
        if p not in CLASSICAL:reason='Nodes have no generic favorable relationship-house credit.'
        identifier=book.add(p,f'house:{h}','Moon / Chandra Lagna','whole_sign_occupancy',
            'climate','general_climate',reason,'obstructed' if blockers else 'contextual',
            details={**row,'climate':status,'vedha_house':blockhouse,'blockers':blockers})
        out[p]={**row,'status':status,'vedha_house':blockhouse,'blockers':blockers,'evidence_id':identifier}
    return out
