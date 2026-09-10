"""Relationship workspace. Personal records stay in this browser session unless exported."""
from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
import json
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import streamlit as st

from styling import card
from vedic_astro.dasha import DAYS_PER_YEAR
from vedic_astro.timing import birth_cycle, birth_balance, dasha_at, hierarchy_for_md, mahadasha_at
from vedic_astro.relationships import analyze, analyze_event, indicators, repeated_signatures, scan_windows, RULES
from vedic_astro.relationship_records import (
    RelationshipEvent, PersonProfile, EVENT_TYPES, chart_key, local_instant, dump_records, load_records)
from vedic_astro.location import geocode_place, LocationError
from vedic_astro.synastry import compare_profiles
from vedic_astro.util import rashi_display_name

MIN_DATE, MAX_DATE = date(1800,1,1), date(2200,12,31)
ERRORS = (ValueError, ZoneInfoNotFoundError, LocationError, OverflowError)


def table(rows):
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.caption('No matching indicators under the selected rules.')


def instant_inputs(prefix, zone, default=None, optional=False):
    day=st.date_input('Date', value=default or date.today(), min_value=MIN_DATE,max_value=MAX_DATE,key=prefix+'_date')
    known=st.checkbox('Exact time known', value=True,key=prefix+'_known') if optional else True
    clock=st.time_input('Local time (24-hour)',value=time(12),step=60,key=prefix+'_time')
    zone=st.text_input('Timezone (IANA name)', value=zone,key=prefix+'_zone',help='For example Asia/Kolkata or America/Los_Angeles. Use the event location’s timezone.')
    occurrence=st.selectbox('If clocks repeat this time',('Require clarification','First occurrence','Second occurrence'),key=prefix+'_fold')
    fold={'Require clarification':None,'First occurrence':0,'Second occurrence':1}[occurrence]
    return day,clock if known else None,zone,fold


def period_rows(rows, zone):
    tz=ZoneInfo(zone)
    return [{'Level':r['level'],'Planet':r['lord'],
             'Start (local)':r['start'].astimezone(tz).isoformat(),
             'End (local, exclusive)':r['end'].astimezone(tz).isoformat(),
             'Parent MD':r['parent_md'],'Parent AD':r['parent_ad']} for r in rows]


def show_result(result, zone):
    st.caption(f"Moment: {datetime.fromisoformat(result['at_utc']).astimezone(ZoneInfo(zone)).isoformat()} · UTC: {result['at_utc']} · {result['ayanamsa']}")
    st.markdown('**Active MD / AD / PD**')
    table(period_rows(result['dashas'],zone))
    if not result['dashas']:
        st.info('This date precedes birth. Transits are shown, but personal dashas are unavailable.')
    st.markdown('**Sidereal transit snapshot**')
    table([{**r,'sign':rashi_display_name(r['sign'])} for r in result['transits']])
    st.markdown('**Relationship indicator counts**')
    st.caption('Counts describe this rule set—not compatibility, probability, or a promise of a relationship.')
    table([{'Category':c,'Eligible families (0–6)':v['score'],
            'Distinct source matching':v['independent_source_count'],
            'Stacking conditions met':v['flagged'],'Families':', '.join(v['families'])} for c,v in result['scores'].items()])
    with st.expander('Activations and the evidence for each one'):
        table(result['activations'])
    with st.expander('Degree contacts and whole-sign aspects'):
        st.caption('Degree contacts use the selected orb. Whole-sign aspects are separate and do not imply an exact angle.')
        table(result['contacts'])
    with st.expander('Natal D1 / D9, Darakaraka and Upapada calculation details'):
        st.json(result['natal'])
        st.json(result['natal_d1'])
    with st.expander('Full calculation record / rules'):
        st.json(result)
    st.download_button('Download calculation record',json.dumps(result,default=str,indent=2),
                       'relationship-calculation.json','application/json',key='record_'+result['at_utc'])


def lookup(chart,zone,orb):
    with st.form('relationship_lookup'):
        day,clock,tz,fold=instant_inputs('lookup',zone)
        run=st.form_submit_button('Inspect date')
    if run:
        try:
            at=local_instant(day,clock,tz,fold)
            result=analyze(chart,at,orb)
            result.update(input_timezone=tz,input_local=datetime.combine(day,clock).isoformat(),input_fold=fold)
            st.session_state['relationship_lookup_result']=(chart_key(chart),orb,tz,result)
        except ERRORS as e: st.error(str(e))
    saved=st.session_state.get('relationship_lookup_result')
    if saved and saved[0]==chart_key(chart) and saved[1]==orb:
        show_result(saved[3],saved[2])
    elif saved:
        st.info('Chart or orb changed. Click Inspect date to recalculate.')


def hierarchy(chart,zone):
    st.caption(f'Vimshottari uses the stored Moon longitude, {chart.planets["Moon"].longitude:.12f}°, and a {DAYS_PER_YEAR}-day year. Intervals include their start and exclude their end.')
    with st.form('hierarchy_lookup'):
        day,clock,tz,fold=instant_inputs('hierarchy',zone)
        run=st.form_submit_button('Find MD / AD / PD')
    if run:
        try:
            at=local_instant(day,clock,tz,fold)
            active=dasha_at(chart.birth_datetime_utc,chart.planets['Moon'].longitude,at)
            table(period_rows([asdict(p) for p in active],tz))
            st.markdown('**Every AD and PD in that Mahadasha**')
            rows=hierarchy_for_md(mahadasha_at(chart.birth_datetime_utc,chart.planets['Moon'].longitude,at))
            table(period_rows([asdict(p) for p in rows],tz))
        except ERRORS as e: st.error(str(e))
    with st.expander('Exact birth Moon / nakshatra balance'):
        st.json(birth_balance(chart.planets['Moon'].longitude))
    sequence=birth_cycle(chart.birth_datetime_utc,chart.planets['Moon'].longitude)
    index=st.selectbox('Browse the first complete 120-year cycle',range(9),
        format_func=lambda i:f'{sequence[i].lord}: {sequence[i].start.date()} → {sequence[i].end.date()}',key='browse_md')
    rows=[asdict(p) for p in hierarchy_for_md(sequence[index])]
    table(period_rows(rows,zone))
    st.download_button('Download MD / AD / PD hierarchy',pd.DataFrame(rows).to_csv(index=False),
                       'vimshottari-hierarchy.csv','text/csv')


def event_editor(events,zone):
    message=st.session_state.pop('relationship_event_message',None)
    if message: st.success(message)
    existing=st.selectbox('Add or edit an event',['new']+[e.id for e in events],
                          format_func=lambda v:'New event' if v=='new' else next(f'{e.day} · {e.person} · {e.event_type}' for e in events if e.id==v),key='event_edit')
    current=next((e for e in events if e.id==existing),None)
    with st.form('event_form_'+existing):
        person=st.text_input('Person / label',value=current.person if current else '',max_chars=200)
        event_type=st.selectbox('Event type',EVENT_TYPES,index=EVENT_TYPES.index(current.event_type) if current else 0)
        custom=st.text_input('Custom event type (when Custom is selected)',value=current.custom_type if current else '',max_chars=200)
        day=st.date_input('Event date',value=date.fromisoformat(current.day) if current else date.today(),min_value=MIN_DATE,max_value=MAX_DATE)
        known=st.checkbox('Exact event time known',value=bool(current and current.clock))
        clock=st.time_input('Event local time',value=time.fromisoformat(current.clock) if current and current.clock else time(12),step=60)
        tz=st.text_input('Event timezone',value=current.timezone if current else zone)
        fold=st.selectbox('Repeated clock time',('Require clarification','First occurrence','Second occurrence'),
                          index=(current.fold+1) if current and current.fold is not None else 0)
        notes=st.text_area('Notes (optional)',value=current.notes if current else '',max_chars=10000)
        save=st.form_submit_button('Save event')
    if save:
        try:
            if not person.strip(): raise ValueError('Enter a person or label.')
            if event_type=='custom' and not custom.strip(): raise ValueError('Enter a custom event type.')
            event=RelationshipEvent(existing if current else str(uuid4()),person.strip(),event_type,day.isoformat(),
                clock.isoformat() if known else None,tz,notes,custom,None if fold=='Require clarification' else 0 if fold=='First occurrence' else 1)
            event.instant()
            if current: events[events.index(current)]=event
            else: events.append(event)
            st.session_state['relationship_event_message']='Event saved in this session. Export a backup below to keep it.'
            st.rerun()
        except ERRORS as e: st.error(str(e))
    if current and st.button('Delete this event',key='delete_'+existing):
        events.remove(current)
        st.rerun()


def events_view(chart,zone,orb,events):
    event_editor(events,zone)
    if not events: return
    st.divider()
    selected=st.selectbox('Open an event',events,format_func=lambda e:f'{e.day} · {e.person} · {e.event_type}',key='open_event')
    st.write(selected.notes)
    if not selected.clock:
        st.warning('Exact time unknown: this is a local-noon reference snapshot, not an exact event time. PD and fast-moving contacts can change during the day. Repetitions from this event are provisional.')
    try:
        show_result(analyze_event(chart,selected,orb),selected.timezone)
    except ERRORS as e: st.error(str(e))


def comparison(chart,orb,events):
    now=datetime.now(timezone.utc)
    historical=[e for e in events if e.instant()<=now]
    selected=st.multiselect('Historical events to compare',historical,
                format_func=lambda e:f'{e.day} · {e.person} · {e.event_type}',key='compare_events')
    if len(selected)<2:
        st.info('Select at least two saved historical events.'); return
    results=[(e.id,analyze_event(chart,e,orb)) for e in selected]
    summaries={}
    for event,(_,result) in zip(selected,results):
        summaries[f'{event.day} · {event.person} · {event.id[:8]}']={
            'Type':event.custom_type if event.event_type=='custom' else event.event_type,
            'Time':event.clock or 'Noon assumed', 'Timezone':event.timezone,
            'MD / AD / PD':' / '.join(p['lord'] for p in result['dashas']),
            **{c:v['score'] for c,v in result['scores'].items()}}
    st.dataframe(pd.DataFrame(summaries).astype(str),use_container_width=True)
    st.markdown('**Repeated Signatures**')
    st.caption('A signature must occur in at least two distinct selected events. These are descriptive repetitions, not proof of a cause or predictive accuracy.')
    repeated=repeated_signatures(results)
    table(repeated)
    if any(not e.clock for e in selected):
        st.warning('Some events use assumed noon. Repetitions involving those events are provisional.')
    with st.expander('Underlying event records and evidence'):
        st.json({e.id:{'event':asdict(e),'calculation':r} for e,(_,r) in zip(selected,results)})


def future_view(chart,orb):
    st.caption('Daily snapshots at 12:00 UTC; maximum three years per scan. Windows are sampled intervals, not exact crossing times. No window is a prediction of marriage or a specific person.')
    today=datetime.now(timezone.utc).date()
    with st.form('future_scan'):
        start=st.date_input('Start date (UTC)',value=today+timedelta(days=1),min_value=today,max_value=MAX_DATE)
        end=st.date_input('End date (UTC)',value=today+timedelta(days=180),min_value=today,max_value=MAX_DATE)
        run=st.form_submit_button('Scan relationship windows')
    if run:
        try:
            if datetime.combine(start,time(12),timezone.utc)<=datetime.now(timezone.utc):
                raise ValueError('Choose a future start date; the scan samples at 12:00 UTC.')
            with st.spinner('Calculating daily indicators and the preceding 90-day baseline...'):
                result=scan_windows(chart,datetime.combine(start,time(12),timezone.utc),datetime.combine(end,time(12),timezone.utc),orb)
            st.session_state['relationship_scan']=(chart_key(chart),orb,start,end,result)
        except ERRORS as e: st.error(str(e))
    saved=st.session_state.get('relationship_scan')
    if not saved or saved[0]!=chart_key(chart) or saved[1]!=orb: return
    result=saved[4]
    st.caption(f'Saved scan: {saved[2]} → {saved[3]} · {result["sample_count"]} daily samples · orb {saved[1]}°')
    st.json({'baseline_start':result['baseline_start'],'baseline_samples':result['baseline_samples'],'thresholds':result['thresholds']})
    table([{'Category':w['category'],'First qualifying sample':w['first_sample'],
            'Last qualifying sample':w['last_sample'],'Days sampled':len(w['samples']),
            'Peak family count':max(s['score'] for s in w['samples'])} for w in result['windows']])
    for i,w in enumerate(result['windows']):
        with st.expander(f'{w["category"]}: {w["first_sample"][:10]} → {w["last_sample"][:10]}'):
            st.json(w)
    if result['isolated_samples']:
        with st.expander('Isolated daily spikes (not sustained windows)'):
            st.json(result['isolated_samples'])
    st.download_button('Download windows and daily evidence',json.dumps(result,default=str,indent=2),
                       'relationship-windows.json','application/json')


def profiles_view(chart,profiles,orb):
    with st.form('partner_profile'):
        label=st.text_input('Person’s name / label',max_chars=200)
        day=st.date_input('Birth date',value=date(1990,1,1),min_value=MIN_DATE,max_value=date.today())
        reliable=st.checkbox('Birth time is known and reliable',value=False)
        clock=st.time_input('Birth time (used only if reliable)',value=time(12),step=60)
        place_name=st.text_input('Birthplace',placeholder='City, region, country')
        occurrence=st.selectbox('If birth time occurs twice during a clock change',('Require clarification','First occurrence','Second occurrence'))
        add=st.form_submit_button('Create profile')
    if add:
        try:
            if not label.strip() or not place_name.strip(): raise ValueError('Enter a label and birthplace.')
            with st.spinner('Resolving birthplace and historical timezone...'):
                place=geocode_place(place_name)
            profile=PersonProfile(str(uuid4()),label.strip(),day.isoformat(),clock.isoformat() if reliable else None,
                                   place.address,place.latitude,place.longitude,place.timezone,reliable,
                                   None if occurrence=='Require clarification' else 0 if occurrence=='First occurrence' else 1)
            profile.instant()
            profiles.append(profile)
            st.success('Profile saved in this session.')
        except ERRORS as e: st.error(str(e))
    if not profiles: return
    profile=st.selectbox('Compare a natal profile',profiles,format_func=lambda p:p.label,key='synastry_profile')
    st.caption(f'{profile.birthplace} · {profile.timezone} · {profile.day} · {profile.clock or "birth time unknown"}')
    if st.button('Delete selected profile'):
        profiles.remove(profile); st.rerun()
    try: result=compare_profiles(chart,profile,orb)
    except ERRORS as e: st.error(str(e)); return
    st.caption('Natal synastry only. No event timing or relationship outcome score is assigned.')
    if result['reliable_time']:
        card('Partner Lagna',rashi_display_name(result['partner_lagna']))
        st.caption(f'Moon: {result["partner_moon_nakshatra"]}, pada {result["partner_moon_pada"]}')
        table(list(result['partner_d1'].values()))
        st.markdown('**D9 placements**'); table(list(result['partner_indicators']['d9_placements'].values()))
        st.markdown('**House overlays**'); table(result['house_overlays'])
        st.markdown('**Directed natal contacts**'); table(result['contacts'])
        st.markdown('**D9 sign connections**'); table(result['d9_contacts'])
    else:
        st.warning('Birth time unknown/unreliable. Lagna, houses, D9 and Upapada are unavailable. The following noon positions and contacts are provisional.')
        table(result['provisional_planets']); table(result['provisional_contacts'])
    with st.expander('Full synastry calculation, seventh lords, Darakaraka and UL details'):
        st.json(result)


def render_relationships(chart,place):
    st.caption('Relationship Timing & Retrospective · indicators, not promises')
    st.info('Events and profiles are stored only in this browser session. Export a backup before closing or rebooting the app. No account or shared database is used.')
    key='relationship_workspace_'+chart_key(chart)
    workspace=st.session_state.setdefault(key,{'events':[],'profiles':[]})
    orb=st.number_input('Close-contact orb (degrees)',min_value=0.0,max_value=10.0,value=3.0,step=0.5,key='relationship_orb')
    with st.expander('Calculation methods and scoring rules'):
        st.json(RULES)
        st.caption('Default birth-chart ayanamsha is Lahiri. This workspace inherits your selected natal ayanamsha. All positions and periods are calculated in Python; no LLM calculations are used.')
    section=st.selectbox('Relationship workspace',('Date snapshot','MD / AD / PD hierarchy','Events','Compare events','Future windows','Natal synastry'),key='relationship_section')
    if section=='Date snapshot': lookup(chart,place.timezone,orb)
    elif section=='MD / AD / PD hierarchy': hierarchy(chart,place.timezone)
    elif section=='Events': events_view(chart,place.timezone,orb,workspace['events'])
    elif section=='Compare events': comparison(chart,orb,workspace['events'])
    elif section=='Future windows': future_view(chart,orb)
    elif section=='Natal synastry': profiles_view(chart,workspace['profiles'],orb)
    st.divider()
    with st.expander('Export / restore events and profiles'):
        st.download_button('Export private backup',dump_records(chart,workspace['events'],workspace['profiles']),
                           'relationship-backup.json','application/json')
        uploaded=st.file_uploader('Restore a backup for this birth chart (replaces session records)',type=['json'])
        if uploaded and st.button('Restore backup'):
            try:
                events,profiles=load_records(uploaded.getvalue(),chart)
                workspace['events'],workspace['profiles']=events,profiles
                st.success('Backup restored.'); st.rerun()
            except ERRORS as e: st.error(str(e))
