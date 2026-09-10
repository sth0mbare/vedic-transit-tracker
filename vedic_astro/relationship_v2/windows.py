"""Opt-in boundary/window API. Never run automatically or by the debug viewer."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from math import ceil
from ..ephemeris import get_planet_positions
from ..timing import dasha_at, utc
from ..util import rashi_index
from .engine import analyze_v2
from .spec import PARAMETERS, VERSION


def discover_boundaries(chart, start, end, *, position_provider=None, period_provider=None):
    start,end=utc(start),utc(end)
    if end<=start or start<utc(chart.birth_datetime_utc):raise ValueError('Require birth <= start < end')
    positions=position_provider or get_planet_positions
    periods=period_provider or dasha_at
    @lru_cache(maxsize=8192)
    def at(t):return positions(t,chart.ayanamsa)
    boundaries={start,end}
    def refine(a,b,p,station=False):
        value=lambda t:at(t)[p].speed<0 if station else rashi_index(at(t)[p].longitude)
        initial=value(a)
        while (b-a).total_seconds()>PARAMETERS['boundary_precision_seconds']:
            m=a+(b-a)/2
            if value(m)==initial:a=m
            else:b=m
        return min(end,datetime.fromtimestamp(ceil(b.timestamp()),timezone.utc))
    cursor=start
    while cursor<end:
        nxt=min(cursor+timedelta(seconds=PARAMETERS['ingress_bracket_seconds']),end)
        left,right=at(cursor),at(nxt)
        for p in left:
            pieces=[cursor,nxt]
            if (left[p].speed<0)!=(right[p].speed<0):
                station=refine(cursor,nxt,p,True)
                if cursor<station<nxt:pieces.insert(1,station)
            for a,b in zip(pieces,pieces[1:]):
                if rashi_index(at(a)[p].longitude)!=rashi_index(at(b)[p].longitude):
                    boundaries.add(refine(a,b,p))
        cursor=nxt
    cursor=start
    while cursor<end:
        rows=periods(chart.birth_datetime_utc,chart.planets['Moon'].longitude,cursor)
        ends=[utc(p.end) for p in rows]
        if not ends or any(t<=cursor for t in ends):raise ValueError('Non-advancing dasha boundaries')
        nxt=min(ends)
        if nxt<end:boundaries.add(nxt)
        cursor=nxt
    return sorted(boundaries)


def windows_from_segments(segments):
    """Aggregate maximal active intervals without gap filling/minimum duration."""
    windows=[];active={};previous=None
    for segment in segments:
        start,end=segment['start'],segment['end'];r=segment['result']
        if end<=start or (previous is not None and start!=previous):
            raise ValueError('Segments must be ordered, contiguous, nonempty intervals')
        previous=end
        flags={f'broad_{k}':v for k,v in r['broad_periods'].items()}
        for k,a in r['assessments'].items():
            flags[k]=a['architecture_active']
            flags[k+'_trigger']=a['architecture_active'] and a['trigger_active']
        for key in list(active):
            if not flags.get(key):windows.append(active.pop(key))
        for key,is_active in flags.items():
            if not is_active:continue
            if key not in active:active[key]={'kind':key,'start':start,'end':end,'segments':[]}
            active[key]['end']=end
            active[key]['segments'].append({'start':start,'end':end,'at_utc':r['at_utc'],
                'dashas':r['dashas'],'assessment':r['assessments'].get(key.removesuffix('_trigger'))})
    windows.extend(active.values())
    return sorted(windows,key=lambda w:(w['start'],w['kind']))


def scan_v2(chart, start, end, *, position_provider=None, period_provider=None, birth_time_precision=None):
    """Explicitly requested scans only. No default dates, ranking or outcome inputs."""
    boundaries=discover_boundaries(chart,start,end,position_provider=position_provider,period_provider=period_provider)
    segments=[]
    for a,b in zip(boundaries,boundaries[1:]):
        # Half-open intervals evaluated on their included start, preserving exact PD boundaries.
        r=analyze_v2(chart,a,position_provider=position_provider,period_provider=period_provider,
                     birth_time_precision=birth_time_precision)
        segments.append({'start':a,'end':b,'result':r})
    return {'version':VERSION,'start':utc(start),'end':utc(end),'boundaries':boundaries,
            'windows':windows_from_segments(segments),'segments':segments,
            'precision_seconds':PARAMETERS['boundary_precision_seconds'],
            'limitations':['Hourly ingress brackets, station splitting, one-second detected-boundary precision; no proof against arbitrary sub-hour oscillations.',
                           'Degree diagnostics are snapshot context only, not exhaustive interval contact searches.']}
