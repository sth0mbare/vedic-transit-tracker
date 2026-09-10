"""Exercise the actual sidebar workspace with a synthetic session, no geocoding network."""
from datetime import date, datetime, timezone

from streamlit.testing.v1 import AppTest

from vedic_astro.chart import compute_natal_chart
from vedic_astro.location import Place
from vedic_astro.relationship_records import chart_key, RelationshipEvent, PersonProfile


def workspace():
    chart=compute_natal_chart(datetime(1990,5,15,9,tzinfo=timezone.utc),18.5213738,73.8545071)
    app=AppTest.from_file('app.py',default_timeout=30)
    app.session_state['chart']=chart
    app.session_state['place']=Place('Pune','Pune',18.5213738,73.8545071,'Asia/Kolkata')
    app.run()
    next(b for b in app.sidebar.button if b.label=='Relationships').click().run()
    assert not app.exception
    return app,chart,'relationship_workspace_'+chart_key(chart)


def choose(app,label):
    next(s for s in app.selectbox if s.label=='Relationship workspace').select(label).run()
    assert not app.exception


def test_create_edit_delete_event_preserves_d1():
    app,chart,key=workspace()
    choose(app,'Events')
    next(t for t in app.text_input if t.label=='Person / label').set_value('Test event')
    next(d for d in app.date_input if d.label=='Event date').set_value(date(2020,5,15))
    next(b for b in app.button if b.label=='Save event').click().run()
    assert not app.exception
    events=app.session_state[key]['events']
    assert len(events)==1 and events[0].clock is None
    next(s for s in app.selectbox if s.label=='Add or edit an event').select(events[0].id).run()
    app.text_area[0].set_value('Edited note')
    next(b for b in app.button if b.label=='Save event').click().run()
    assert not app.exception
    assert len(app.session_state[key]['events'])==1
    assert app.session_state[key]['events'][0].notes=='Edited note'
    next(b for b in app.button if b.label=='Delete this event').click().run()
    assert not app.exception
    assert not app.session_state[key]['events']
    assert app.session_state['chart']==chart


def test_lookup_hierarchy_comparison_and_unknown_synastry():
    app,chart,key=workspace()
    next(b for b in app.button if b.label=='Inspect date').click().run()
    assert not app.exception
    assert len(app.dataframe[0].value)==3
    choose(app,'MD / AD / PD hierarchy')
    next(b for b in app.button if b.label=='Find MD / AD / PD').click().run()
    assert not app.exception
    assert any(len(t.value)==91 for t in app.dataframe)
    events=[RelationshipEvent('a','A','first met','2020-05-15','12:00:00','UTC'),
            RelationshipEvent('b','B','first date','2021-05-15',None,'UTC')]
    app.session_state[key]['events']=events
    choose(app,'Compare events')
    app.multiselect[0].set_value(events).run()
    assert not app.exception
    assert len(app.dataframe[0].value.columns)==2
    app.session_state[key]['profiles']=[PersonProfile('p','Unknown','1990-05-15',None,'Pune',18.5,73.8,'Asia/Kolkata',False)]
    choose(app,'Natal synastry')
    assert not app.exception
    assert any('Birth time unknown' in w.value for w in app.warning)
    assert app.session_state['chart']==chart
