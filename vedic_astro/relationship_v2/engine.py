"""Read-only snapshot API. Importing this module never evaluates a chart."""
from dataclasses import asdict
from copy import deepcopy
from math import isfinite
from ..ephemeris import get_planet_positions
from ..timing import dasha_at, utc
from ..constants import GRAHAS
from .spec import VERSION, PARAMETERS, SOURCES
from .evidence import EvidenceBook
from .natal import build_natal
from .periods import activate_periods
from .climate import compute_climate
from .transits import activate_transits
from .assessment import assess
from .provenance import freeze_metadata


def analyze_v2(chart, at, *, birth_time_precision=None, position_provider=None, period_provider=None):
    """No event/outcome arguments. Providers support synthetic method tests only."""
    at=utc(at)
    if at<utc(chart.birth_datetime_utc):raise ValueError('Timing lookup requires a time at or after birth')
    book=EvidenceBook(at);natal=build_natal(chart,book)
    positions=(position_provider or get_planet_positions)(at,chart.ayanamsa)
    if set(positions)!=set(GRAHAS) or not all(isfinite(v.longitude) and isfinite(v.speed) for v in positions.values()):
        raise ValueError('Complete finite nine-graha transit positions required')
    periods=(period_provider or dasha_at)(chart.birth_datetime_utc,chart.planets['Moon'].longitude,at)
    if sorted(p.level for p in periods)!=['AD','MD','PD'] or not all(p.start<=at<p.end and p.lord in GRAHAS for p in periods):
        raise ValueError('Exactly one active MD, AD and PD is required')
    pd=activate_periods(natal,periods,book)
    climate=compute_climate(chart,positions,book)
    transit_layers=activate_transits(chart,natal,positions,climate,pd,book)
    assessments=assess(book);evidence=book.finalize(assessments)
    warnings=[]
    if birth_time_precision is None:warnings.append('Birth-time precision unspecified; D1/D9/UL-dependent outputs are provisional.')
    elif birth_time_precision!='verified':warnings.append('Birth-time-sensitive references have not been sensitivity-tested: '+str(birth_time_precision))
    if len(natal['metadata']['darakaraka'])>1:warnings.append('Exact Darakaraka tie retained; tied identities do not create independent confirmations.')
    return {'version':VERSION,'at_utc':at.isoformat(),'ayanamsa':chart.ayanamsa,
            'implementation':freeze_metadata(),
            'methodology':{'parameters':dict(PARAMETERS),'source_classifications':deepcopy(SOURCES)},
            'natal':{**natal,'roles':{k:sorted(v) for k,v in natal['roles'].items()}},
            'dashas':[asdict(p) for p in periods], 'dasha_background':pd['background_md_roles'],
            'general_gochara':climate,'positions':{p:asdict(v) for p,v in positions.items()},
            'layers':transit_layers,'assessments':assessments,'evidence':evidence,
            'evidence_deduplicated':book.redundant,'data_quality':{'birth_time_precision':birth_time_precision,'warnings':warnings},
            'broad_periods':{k:bool(book.features.get(k)) for k in ('romance_period','partnership_period','stress_period')}}
