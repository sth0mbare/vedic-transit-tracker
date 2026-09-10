"""Core-page smoke tests and protection against relationship UI re-entry."""
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
import ast

import pytest
from streamlit.testing.v1 import AppTest
from vedic_astro.chart import compute_natal_chart
from vedic_astro.location import Place

VIEWS = ['D1 · Natal Chart', 'D2 · Hora', 'D4 · Chaturthamsa', 'D9 · Navamsa',
         'D10 · Dasamsa', 'Live Transits', 'Past Transits', 'Sade Sati',
         'Guru Gochar', 'Current Dasha', 'Sun & Venus Mahadasha']


@pytest.mark.parametrize('view', VIEWS)
def test_core_page_renders_without_relationship_analysis(view, monkeypatch):
    import vedic_astro.relationships as legacy
    import vedic_astro.relationship_v2.engine as v2
    import vedic_astro.relationship_v2.windows as windows
    def forbidden(*args, **kwargs):
        raise AssertionError('Visible pages must not call relationship analysis')
    for module, names in [(legacy, ('analyze', 'analyze_event', 'scan_windows', 'repeated_signatures')),
                          (v2, ('analyze_v2',)), (windows, ('scan_v2',))]:
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    c = compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    before = deepcopy(c)
    app = AppTest.from_file('app.py', default_timeout=60)
    app.session_state['chart'] = c
    app.session_state['place'] = Place('Pune','Pune',18.5213738,73.8545071,'Asia/Kolkata')
    app.session_state['selected_chart_view'] = view
    app.session_state['past_transits_date'] = date(2000,1,1)
    app.run()
    assert not app.exception
    assert not app.error
    assert [b.label for b in app.sidebar.button] == VIEWS
    assert app.session_state['chart'] == before
    assert any(h.value == view for h in app.subheader)
    assert app.dataframe or app.markdown


@pytest.mark.parametrize('retired', ['Relationships', 'Relationship v2 — Experimental'])
def test_old_session_navigation_falls_back_to_d1(retired):
    app = AppTest.from_file('app.py', default_timeout=30)
    app.session_state['chart'] = compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    app.session_state['place'] = Place('Pune','Pune',18.5213738,73.8545071,'Asia/Kolkata')
    app.session_state['selected_chart_view'] = retired
    app.run()
    assert not app.exception
    assert app.session_state['selected_chart_view'] == VIEWS[0]
    assert all(b.label not in ('Relationships','Relationship v2 — Experimental') for b in app.sidebar.button)


def test_app_import_tree_excludes_relationship_modules():
    seen = set()
    def visit(path):
        if path in seen: return
        seen.add(path)
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import): modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.level:
                    base = path.parent
                    for _ in range(node.level-1): base = base.parent
                    candidate = base.joinpath(*node.module.split('.')).with_suffix('.py')
                    assert 'relationship' not in str(candidate)
                    if candidate.exists(): visit(candidate)
                    continue
                modules = [node.module]
            for module in modules:
                assert 'relationship' not in module
                candidate = Path(*module.split('.')).with_suffix('.py')
                if candidate.exists(): visit(candidate)
    visit(Path('app.py'))
