"""UI wiring tests use fabricated engine outputs, never real-date v2 queries."""
from datetime import date, datetime, timedelta, timezone
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from tests.test_relationship_v2 import chart, evaluate, AT
from vedic_astro.relationship_v2.windows import windows_from_segments


def launch():
    app = AppTest.from_string('from relationship_v2_ui import render_relationship_v2\nfrom tests.test_relationship_v2 import chart\nrender_relationship_v2(chart())', default_timeout=30)
    app.run()
    assert not app.exception
    return app


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_opt_in_snapshot_and_scan(monkeypatch):
    import relationship_v2_ui as ui
    result = evaluate(); original = deepcopy(result); calls = []
    def snapshot(c, at):
        calls.append(('snapshot', c, at)); return result
    def scan(c, start, end):
        calls.append(('scan', c, start, end))
        # Fabricated time interval and frozen synthetic result only.
        segments = [{'start': AT, 'end': AT+timedelta(hours=1), 'result': result}]
        return {'start': AT, 'end': AT+timedelta(hours=1), 'windows': windows_from_segments(segments),
                'segments': segments, 'limitations': []}
    monkeypatch.setattr(ui, 'analyze_v2', snapshot)
    monkeypatch.setattr(ui, 'scan_v2', scan)
    app = launch(); assert not calls
    assert app.text_input(key='v2_snapshot_zone').value == 'America/Los_Angeles'
    app.date_input(key='v2_snapshot_date').set_value(date(2000,1,1))
    button(app, 'Evaluate with v2').click().run()
    assert not app.exception
    assert calls[0][2] == datetime(2000,1,1,20,tzinfo=timezone.utc)
    assert calls[0][1] == chart()
    for a in result['assessments'].values():
        assert any(m.value == a['state'] for m in app.markdown)
    assert all(not e.proto.expanded for e in app.expander)
    app.run(); assert len(calls) == 1
    app.date_input(key='v2_start').set_value(date(2000,1,1))
    app.date_input(key='v2_end').set_value(date(2000,1,1))
    button(app, 'Scan date range with v2').click().run()
    assert not app.exception
    assert calls[-1][2] == datetime(2000,1,1,8,tzinfo=timezone.utc)
    assert calls[-1][3] == datetime(2000,1,2,8,tzinfo=timezone.utc)
    assert result == original


def test_invalid_timezone_and_range_do_not_call_engine(monkeypatch):
    import relationship_v2_ui as ui
    def forbidden(*args):
        raise AssertionError('No engine call allowed')
    monkeypatch.setattr(ui, 'analyze_v2', forbidden)
    monkeypatch.setattr(ui, 'scan_v2', forbidden)
    app = launch()
    app.text_input(key='v2_snapshot_zone').set_value('Invalid/Zone')
    button(app, 'Evaluate with v2').click().run()
    assert app.error and not app.exception
    app.date_input(key='v2_start').set_value(date(2000,1,2))
    app.date_input(key='v2_end').set_value(date(2000,1,1))
    button(app, 'Scan date range with v2').click().run()
    assert app.error and not app.exception


def test_sidebar_entry_preserves_current_chart(monkeypatch):
    import relationship_v2_ui as ui
    from vedic_astro.location import Place
    def forbidden(*args):
        raise AssertionError('Opening view must not evaluate')
    monkeypatch.setattr(ui, 'analyze_v2', forbidden)
    monkeypatch.setattr(ui, 'scan_v2', forbidden)
    app = AppTest.from_file('app.py', default_timeout=30)
    c = chart()
    app.session_state['chart'] = c
    app.session_state['place'] = Place('Synthetic', 'Synthetic', 0, 0, 'UTC')
    app.session_state['selected_chart_view'] = 'Relationship v2 — Experimental'
    app.run()
    assert not app.exception
    assert app.session_state['chart'] == c
    assert any(b.label == 'Relationships' for b in app.sidebar.button)
    assert any(b.label == 'Relationship v2 — Experimental' for b in app.sidebar.button)
