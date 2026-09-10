from datetime import date, time, datetime, timezone
import json

import pytest

from tests.test_navamsa import synthetic_chart
from vedic_astro.relationship_records import (RelationshipEvent, PersonProfile,
    local_instant, dump_records, load_records)
from vedic_astro.synastry import compare_profiles


def test_historical_timezone_and_dst():
    assert local_instant(date(1990,5,15),time(14,30),'Asia/Kolkata')==datetime(1990,5,15,9,tzinfo=timezone.utc)
    with pytest.raises(ValueError, match='does not exist'):
        local_instant(date(2026,3,8),time(2,30),'America/Los_Angeles')
    with pytest.raises(ValueError, match='occurs twice'):
        local_instant(date(2026,11,1),time(1,30),'America/Los_Angeles')
    a=local_instant(date(2026,11,1),time(1,30),'America/Los_Angeles',0)
    b=local_instant(date(2026,11,1),time(1,30),'America/Los_Angeles',1)
    assert (b-a).total_seconds()==3600


def records():
    return ([RelationshipEvent('e','Example','first met','2020-05-15',None,'Asia/Kolkata','note')],
            [PersonProfile('p','Example','1990-05-15',None,'Pune',18.5,73.8,'Asia/Kolkata',False)])


def test_backup_roundtrip_and_chart_binding():
    c=synthetic_chart();events,profiles=records()
    text=dump_records(c,events,profiles)
    assert load_records(text,c)==(events,profiles)
    c.ayanamsa='Raman'
    with pytest.raises(ValueError, match='different'): load_records(text,c)


def test_bad_records_rejected():
    c=synthetic_chart();events,profiles=records()
    data=json.loads(dump_records(c,events,profiles))
    data['events'].append(data['events'][0])
    with pytest.raises(ValueError, match='duplicate'): load_records(json.dumps(data),c)
    for bad in ('[]','null','{}','not-json'):
        with pytest.raises(ValueError): load_records(bad,c)


def test_unknown_time_never_calculates_lagna_or_d9(monkeypatch):
    import vedic_astro.synastry as syn
    def forbidden(*args, **kwargs): pytest.fail('Unknown time must not generate a natal house/D9 chart')
    monkeypatch.setattr(syn,'compute_natal_chart',forbidden)
    monkeypatch.setattr(syn,'indicators',forbidden)
    _,profiles=records()
    result=compare_profiles(synthetic_chart(),profiles[0])
    assert not result['reliable_time']
    assert 'D9' in result['unavailable']
    assert len(result['provisional_planets'])==9
    assert 'partner_d1' not in result and 'partner_indicators' not in result


def test_reliable_profile_has_natal_data():
    p=PersonProfile('p','Example','1990-05-15','14:30:00','Pune',18.5213738,73.8545071,'Asia/Kolkata',True)
    result=compare_profiles(synthetic_chart(),p)
    assert result['reliable_time']
    assert result['partner_lagna']=='Simha'
    assert len(result['partner_d1'])==9 and len(result['partner_indicators']['d9_placements'])==9
    assert result['partner_indicators']['darakaraka']==['Sun']
    assert len(result['house_overlays'])==9
