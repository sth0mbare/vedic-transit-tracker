from copy import deepcopy
from datetime import date, datetime, time, timezone

import pytest
from streamlit.testing.v1 import AppTest
from vedic_astro.chart import compute_natal_chart
from vedic_astro.transit_context import compute_snapshot
from vedic_astro.transits import compute_transits
from vedic_astro.timing import dasha_at
from vedic_astro.relationship_records import local_instant

BIRTH = datetime(1990,5,15,9,tzinfo=timezone.utc)
AT = datetime(2000,1,1,20,tzinfo=timezone.utc)


def chart():
    return compute_natal_chart(BIRTH,18.5213738,73.8545071)


def test_snapshot_preserves_existing_calculations_and_chart():
    c=chart(); before=deepcopy(c)
    s=compute_snapshot(c,AT)
    assert s.placements==compute_transits(c,AT,c.ayanamsa)
    assert s.periods==dasha_at(BIRTH,c.planets['Moon'].longitude,AT)
    assert c==before
    early=compute_snapshot(c,datetime(1980,1,1,tzinfo=timezone.utc))
    assert early.placements and not early.periods and early.warnings


def test_shared_timezone_edges():
    with pytest.raises(ValueError,match='does not exist'):
        local_instant(date(2024,3,10),time(2,30),'America/Los_Angeles')
    with pytest.raises(ValueError,match='occurs twice'):
        local_instant(date(2024,11,3),time(1,30),'America/Los_Angeles')
    a=local_instant(date(2024,11,3),time(1,30),'America/Los_Angeles',0)
    b=local_instant(date(2024,11,3),time(1,30),'America/Los_Angeles',1)
    assert (b-a).total_seconds()==3600


def launch():
    app=AppTest.from_string('from transits_ui import render_transits\nfrom tests.test_transits_phase1 import chart\nrender_transits(chart())',default_timeout=30)
    app.session_state['transits_mode']='Choose Date'
    return app.run()


def test_choose_date_local_noon_and_secondary_houses():
    app=launch();assert not app.exception
    assert not app.dataframe
    app.date_input(key='transits_day').set_value(date(2000,1,1))
    next(b for b in app.button if b.label=='Show transits').click().run()
    assert not app.exception
    assert app.session_state['transits_chosen'][0]==AT
    tables=[d.value for d in app.dataframe if 'Graha' in d.value.columns and 'Rashi' in d.value.columns]
    assert len(tables)==1 and len(tables[0])==9
    assert 'House from natal Lagna (secondary)' not in tables[0]
    app.checkbox(key='transits_lagna').check().run()
    assert any('House from natal Lagna (secondary)' in d.value.columns for d in app.dataframe)
    assert all(not e.proto.expanded for e in app.expander)
    app.checkbox(key='transits_exact').uncheck()
    next(b for b in app.button if b.label=='Show transits').click().run()
    assert any('noon' in w.value for w in app.warning)


def test_bad_timezone_and_dst_gap():
    app=launch()
    app.text_input(key='transits_zone').set_value('invalid').run()
    assert app.error and not app.exception
    app.text_input(key='transits_zone').set_value('America/Los_Angeles').run()
    app.date_input(key='transits_day').set_value(date(2024,3,10))
    app.time_input(key='transits_clock').set_value(time(2,30))
    next(b for b in app.button if b.label=='Show transits').click().run()
    assert app.error and not app.exception


def test_future_selection_allowed_without_future_calculation(monkeypatch):
    import transits_ui
    calls=[]
    def snapshot(c,at):
        calls.append(at)
        return compute_snapshot(c,AT)  # Fixture instant only; verifies UI accepts input.
    monkeypatch.setattr(transits_ui,'cached_snapshot',snapshot)
    app=launch()
    app.date_input(key='transits_day').set_value(date(2090,1,1))
    next(b for b in app.button if b.label=='Show transits').click().run()
    assert not app.exception and not app.error
    assert calls[-1].year==2090


def test_cache_survives_unpicklable_dataclass_identity(monkeypatch):
    """Reproduce the serialization failure seen when a module class is stale."""
    from dataclasses import asdict, make_dataclass
    import pickle
    import transits_ui as ui
    from vedic_astro.horoscope import compute_weekly_horoscope
    c = chart()
    expected = compute_snapshot(c, AT)
    weekly = compute_weekly_horoscope(c, expected.placements, start_dt=AT, ayanamsa_name=c.ayanamsa)
    # Local classes reproduce pickle's inability to locate a returned class.
    Stale = make_dataclass('StaleSnapshot', [(k, object) for k in asdict(expected)])
    stale = Stale(**{k: getattr(expected, k) for k in asdict(expected)})
    with pytest.raises((pickle.PicklingError, AttributeError)):
        pickle.dumps(stale)
    calls=[]
    def compute(*args):
        calls.append(1)
        return stale
    monkeypatch.setattr(ui, 'compute_snapshot', compute)
    monkeypatch.setattr(ui, 'compute_weekly_horoscope', lambda *a, **kw: weekly)
    ui._cached_snapshot_data.clear()
    ui._cached_weekly_data.clear()
    try:
        first=ui.cached_snapshot(c, AT)
        second=ui.cached_snapshot(c, AT)
        assert first==second==expected
        assert len(calls)==1
        assert ui.weekly_snapshot(c, expected.placements, AT)==weekly
        assert ui.weekly_snapshot(c, expected.placements, AT)==weekly
        first.warnings.append('test mutation')
        assert ui.cached_snapshot(c, AT)==expected
    finally:
        ui._cached_snapshot_data.clear()
        ui._cached_weekly_data.clear()
