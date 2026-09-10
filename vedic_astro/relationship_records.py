"""Session records and validated JSON backups; no shared server-side personal data."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
from math import isfinite
from zoneinfo import ZoneInfo

EVENT_TYPES = ('first met', 'first date', 'relationship began', 'sexual/romantic encounter',
               'commitment/exclusivity', 'engagement', 'marriage', 'breakup', 'final contact', 'custom')


def local_instant(day, clock, zone, fold=None):
    """Resolve wall time; reject DST gaps, require an explicit choice for repeats."""
    if clock.tzinfo is not None:
        raise ValueError('Enter a wall-clock time without an offset; specify its timezone separately.')
    naive = datetime.combine(day, clock)
    tz = ZoneInfo(zone)
    candidates = {}
    for f in (0, 1):
        aware = naive.replace(tzinfo=tz, fold=f)
        candidate = aware.astimezone(timezone.utc)
        if candidate.astimezone(tz).replace(tzinfo=None) == naive:
            candidates[f] = candidate
    if not candidates:
        raise ValueError('This local time does not exist because clocks moved forward. Choose another time.')
    if len(set(candidates.values())) > 1 and fold is None:
        raise ValueError('This local time occurs twice. Select the first or second occurrence.')
    if fold not in (None, 0, 1):
        raise ValueError('Invalid clock occurrence')
    return candidates[0 if fold is None else fold]


@dataclass(frozen=True)
class RelationshipEvent:
    id: str
    person: str
    event_type: str
    day: str
    clock: str | None
    timezone: str
    notes: str = ''
    custom_type: str = ''
    fold: int | None = None

    def instant(self):
        return local_instant(date.fromisoformat(self.day),
                             time.fromisoformat(self.clock) if self.clock else time(12),
                             self.timezone, self.fold)


@dataclass(frozen=True)
class PersonProfile:
    id: str
    label: str
    day: str
    clock: str | None
    birthplace: str
    latitude: float
    longitude: float
    timezone: str
    reliable_time: bool
    fold: int | None = None

    def instant(self):
        return local_instant(date.fromisoformat(self.day),
                             time.fromisoformat(self.clock) if self.clock else time(12),
                             self.timezone, self.fold)


def chart_key(chart):
    payload = {'birth':chart.birth_datetime_utc.isoformat(), 'latitude':chart.latitude,
               'longitude':chart.longitude,'ayanamsa':chart.ayanamsa}
    return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def dump_records(chart, events, profiles):
    return json.dumps({'version':1,'chart_key':chart_key(chart),
                       'events':[asdict(e) for e in events],
                       'profiles':[asdict(p) for p in profiles]}, indent=2, ensure_ascii=False)


def load_records(payload, chart):
    if len(payload) > 2_000_000:
        raise ValueError('Backup is too large (maximum 2 MB)')
    try:
        raw=json.loads(payload)
        if raw['version'] != 1 or raw['chart_key'] != chart_key(chart):
            raise ValueError('Backup belongs to a different birth chart/ayanamsa or version')
        if len(raw['events']) > 1000 or len(raw['profiles']) > 100:
            raise ValueError('Backup has too many records')
        events=[RelationshipEvent(**e) for e in raw['events']]
        profiles=[PersonProfile(**p) for p in raw['profiles']]
        for e in events:
            if e.event_type not in EVENT_TYPES or not e.person.strip() or len(e.person)>200 or len(e.notes)>10000:
                raise ValueError('Invalid event')
            if e.event_type=='custom' and not e.custom_type.strip():
                raise ValueError('Custom events need a type label')
            e.instant()
        for p in profiles:
            if not p.label.strip() or len(p.label)>200 or type(p.reliable_time) is not bool:
                raise ValueError('Invalid profile')
            if not isfinite(p.latitude) or not -90 <= p.latitude <= 90 or not isfinite(p.longitude) or not -180 <= p.longitude <= 180:
                raise ValueError('Invalid birthplace coordinates')
            if p.reliable_time and not p.clock:
                raise ValueError('Reliable birth time is missing')
            p.instant()
        for records in (events,profiles):
            ids=[r.id for r in records]
            if any(not isinstance(i,str) or not i or len(i)>100 for i in ids) or len(ids)!=len(set(ids)):
                raise ValueError('Missing or duplicate record identifiers')
        return events, profiles
    except (TypeError, KeyError, AttributeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid relationship backup') from exc
