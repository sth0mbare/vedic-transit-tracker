from copy import deepcopy
from datetime import datetime,timezone

from relationship_consumer import dimension_cards, moment_summary, top_reasons
from vedic_astro.chart import compute_natal_chart
from vedic_astro.relationships import analyze
from tests.test_relationship_ui import workspace, choose


def test_consumer_copy_preserves_calculation_and_filters_evidence():
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    result=analyze(chart,datetime(2018,4,15,12,tzinfo=timezone.utc))
    before=deepcopy(result)
    cards=dimension_cards(result)
    assert [c[0] for c in cards]==['Romance / attraction','Relationship potential','Commitment potential','Ending pressure']
    assert all(c[1] in ('Low','Moderate','High') for c in cards)
    assert len(top_reasons(result))<=5
    moment_summary(result)
    assert result==before
    # No padding with non-counting facts, even if they sound like romance.
    result['activations']=[dict(family='house',source='Venus',target='house5',
        signature='house|Venus|house5|occupancy',categories=['meeting/dating'],score_eligible=False,detail='False')]
    assert top_reasons(result)==[]


def test_counted_house_and_d9_never_leak_raw_details():
    result={'dashas':[],'activations':[
        dict(family='house',source='Mars',target='house1',condition_id='house1',
             categories=['ending/separation'],counted=True,detail='degree link: False'),
        dict(family='house',source='Moon',target='house1',condition_id='house1',
             categories=['ending/separation'],counted=False,eligible=True,detail='Redundant'),
    ]}
    reasons=top_reasons(result)
    assert len(reasons)==1 and 'Mars' in reasons[0]
    assert all(term not in reasons[0] for term in ('False','degree link','Moon','house|'))


def test_summary_uses_existing_labels_without_outcomes():
    scores={key:{'score':0} for key in ('meeting/dating','relationship formation','commitment/marriage','ending/separation')}
    result={'scores':scores}
    assert 'few clear' in moment_summary(result)
    scores['ending/separation']['score']=3
    assert 'pressure or change more' in moment_summary(result)
    scores['meeting/dating']['score']=4
    assert 'Romance and attraction' in moment_summary(result)
    result['event']={'event_type':'breakup','notes':'Known outcome'}
    assert 'Romance and attraction' in moment_summary(result)


def test_default_contains_no_technical_tables_or_debug_text():
    app,chart,key=workspace()
    next(b for b in app.button if b.label=='Inspect date').click().run()
    assert not app.exception
    advanced=next(e for e in app.expander if e.label=='View astrology details')
    assert not advanced.proto.expanded
    assert len(advanced.dataframe)==len(app.dataframe)
    assert len(advanced.json)==len(app.json)
    assert len(advanced.get('download_button'))==2
    assert len(advanced.get('file_uploader'))==1
    technical_ids={id(element) for element in advanced.markdown}
    visible=' '.join(m.value for m in app.markdown if id(m) not in technical_ids and '<style>' not in m.value)
    assert 'What was this moment about?' in visible
    assert 'Romance / attraction' in visible
    for forbidden in ('eligible families','distinct source matching','stacking conditions met','counted indicator groups','False','True','degree link','|house'):
        assert forbidden.lower() not in visible.lower()
    assert app.session_state['chart']==chart
