from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import json

import pytest

from relationship_presentation import activation_level, result_heading, standout_indicators
from vedic_astro.chart import compute_natal_chart
from vedic_astro.relationships import analyze_event
from vedic_astro.relationship_records import RelationshipEvent, OUTCOME_LABELS, dump_records, load_records
from tests.test_relationship_ui import workspace, choose


@pytest.mark.parametrize('score,expected', [(0,'Low'),(1,'Low'),(2,'Moderate'),(3,'Moderate'),(4,'High'),(5,'High'),(6,'High')])
def test_display_bands(score, expected):
    assert activation_level(score) == expected


def test_outcomes_preserve_every_calculation_and_old_backups():
    chart = compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    event = RelationshipEvent('e','Example','custom','2020-08-14','23:30','America/Los_Angeles',custom_type='First contact')
    original = analyze_event(chart,event)
    before = deepcopy(original)
    assert result_heading(original,event.timezone) == 'August 14, 2020 — First contact'
    assert 3 <= len(standout_indicators(original)) <= 6
    assert original == before
    for label in OUTCOME_LABELS:
        labeled = replace(event,outcome_label=label)
        result = analyze_event(chart,labeled)
        assert {k:v for k,v in result.items() if k!='event'} == {k:v for k,v in original.items() if k!='event'}
        assert load_records(dump_records(chart,[labeled],[]),chart) == ([labeled],[])
    old = json.loads(dump_records(chart,[event],[]))
    del old['events'][0]['outcome_label']
    assert load_records(json.dumps(old),chart)[0][0].outcome_label == OUTCOME_LABELS[0]
    old['events'][0]['outcome_label'] = 'invalid'
    with pytest.raises(ValueError,match='outcome'):
        load_records(json.dumps(old),chart)


def test_explanations_rank_dedupe_and_do_not_invent():
    def fact(target, eligible, kind='conjunction:Venus'):
        return dict(family='slow',source='Jupiter',target=target,signature=f'slow|Jupiter|{target}|{kind}',score_eligible=eligible)
    result = {'dashas':[], 'activations':[fact('house1',False,'whole-sign aspect 7:Moon'),fact('house7',True),fact('Venus',True)]}
    messages = standout_indicators(result)
    assert len(messages)==2
    assert 'close to your natal Venus' in messages[0]
    assert 'not necessarily an exact angle' in messages[1]
    assert standout_indicators({'dashas':[],'activations':[]}) == []


def test_summary_and_audit_ui_are_separate():
    app,chart,key = workspace()
    app.session_state[key]['events'] = [RelationshipEvent('e','Example','custom','2020-08-14','23:30','America/Los_Angeles',custom_type='First contact')]
    choose(app,'Events')
    assert any(h.value=='August 14, 2020 — First contact' for h in app.subheader)
    advanced = next(e for e in app.expander if e.label=='Advanced calculations')
    assert not advanced.proto.expanded
    assert len(advanced.json) >= 4
    assert any('Eligible families (0–6)' in t.value.columns for t in advanced.dataframe)
    assert len(advanced.get('download_button')) == 2
    assert any('Meeting / attraction:' in m.value for m in app.markdown)
    assert next(e for e in app.expander if e.label=='Exact dasha dates').dataframe
    # Outcome can be saved without changing the natal chart or score source.
    next(s for s in app.selectbox if s.label=='Add or edit an event').select('e').run()
    next(s for s in app.selectbox if s.label=='Outcome / comparison group (optional)').select('Long-term relationship start')
    next(b for b in app.button if b.label=='Save event').click().run()
    assert not app.exception
    assert app.session_state[key]['events'][0].outcome_label=='Long-term relationship start'
    assert app.session_state['chart']==chart
