from datetime import datetime, timedelta, timezone
from math import nextafter, inf

import pytest

from vedic_astro.constants import DASHA_LORD_CYCLE, DASHA_YEARS
from vedic_astro.dasha import DAYS_PER_YEAR, current_dasha
from vedic_astro.timing import birth_balance, dasha_at, hierarchy_for_md, mahadasha_at

BIRTH=datetime(2000,1,1,tzinfo=timezone.utc)

@pytest.mark.parametrize('i',range(1,27))
def test_exact_nakshatra_boundaries(i):
    boundary=i*40/3
    for lon,index in ((nextafter(boundary,-inf),i-1),(boundary,i),(nextafter(boundary,inf),i)):
        result=birth_balance(lon)
        assert result['nakshatra_index']==index
        assert result['birth_lord']==DASHA_LORD_CYCLE[index%9]
        assert 0<=result['fraction_elapsed']<1
    assert birth_balance(boundary)['fraction_elapsed']==0


def test_birth_balance_not_rounded():
    assert birth_balance(0)['remaining_years']==7
    assert birth_balance(20)['birth_lord']=='Venus'
    assert birth_balance(20)['remaining_years']==pytest.approx(10)
    assert birth_balance(360)==birth_balance(0)


def test_md_ad_pd_all_boundaries_and_parents():
    md=mahadasha_at(BIRTH,0,BIRTH)
    assert md.lord=='Ketu'
    assert md.end==BIRTH+timedelta(days=7*DAYS_PER_YEAR)
    rows=hierarchy_for_md(md)
    assert len(rows)==91
    ads=[r for r in rows if r.level=='AD']
    assert [p.lord for p in ads]==DASHA_LORD_CYCLE
    for level in ('AD','PD'):
        periods=[r for r in rows if r.level==level]
        assert periods[0].start==md.start and periods[-1].end==md.end
        for i,p in enumerate(periods):
            assert p.parent_md=='Ketu'
            result=dasha_at(BIRTH,0,p.start)
            active=next(r for r in result if r.level==level)
            assert active==p
            assert next(r for r in dasha_at(BIRTH,0,p.end-timedelta(microseconds=1)) if r.level==level)==p
            if i: assert periods[i-1].end==p.start
            if level=='PD':
                parent=next(a for a in ads if a.start<=p.start<a.end)
                assert p.parent_ad==parent.lord
                assert parent.start<=p.start<p.end<=parent.end
                assert (p.end-p.start).total_seconds()==pytest.approx(
                    (parent.end-parent.start).total_seconds()*DASHA_YEARS[p.lord]/120,abs=2e-6)
    assert dasha_at(BIRTH,0,md.end)[0].lord=='Venus'


@pytest.mark.parametrize('year',[2000,2005,2010,2030,2099,2200,2400])
def test_historical_future_lookup_and_cycle(year):
    at=datetime(year,6,1,tzinfo=timezone.utc)
    active=dasha_at(BIRTH,0,at)
    assert [p.level for p in active]==['MD','AD','PD']
    assert all(p.contains(at) for p in active)


def test_existing_reference_md_ad_unchanged():
    birth=datetime(1990,5,15,9,tzinfo=timezone.utc)
    moon=271.893544051776
    for year in (1990,1994,2000,2026,2050,2100):
        at=max(birth,datetime(year,6,1,tzinfo=timezone.utc))
        old=current_dasha(birth,moon,at)
        new=dasha_at(birth,moon,at)
        assert new[0].lord==old.mahadasha.lord and new[1].lord==old.antardasha.lord
        for n,o in zip(new,(old.mahadasha,old.antardasha)):
            assert abs((n.start-o.start).total_seconds())<.00001
            assert abs((n.end-o.end).total_seconds())<.00001


def test_invalid_and_timezone_equivalence():
    with pytest.raises(ValueError): dasha_at(BIRTH,0,BIRTH-timedelta(seconds=1))
    with pytest.raises(ValueError): dasha_at(BIRTH,0,BIRTH.replace(tzinfo=None))
    for lon in (inf,-inf,float('nan')):
        with pytest.raises(ValueError): birth_balance(lon)
    assert dasha_at(BIRTH,0,BIRTH)==dasha_at(BIRTH,0,BIRTH.astimezone(timezone(timedelta(hours=5,minutes=30))))


@pytest.mark.parametrize('index',range(9))
def test_every_lords_pd_boundaries(index):
    moon=index*40/3
    md=mahadasha_at(BIRTH,moon,BIRTH)
    assert md.lord==DASHA_LORD_CYCLE[index]
    rows=hierarchy_for_md(md)
    for period in rows:
        assert next(p for p in dasha_at(BIRTH,moon,period.start) if p.level==period.level)==period
        assert next(p for p in dasha_at(BIRTH,moon,period.end-timedelta(microseconds=1)) if p.level==period.level)==period
    assert dasha_at(BIRTH,moon,md.end)[0].lord==DASHA_LORD_CYCLE[(index+1)%9]
