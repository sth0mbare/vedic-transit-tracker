"""Opt-in presentation of frozen v2 outputs; no calculation or scoring rules."""
from datetime import date, time, timedelta
import json
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st
from styling import card
from relationship_ui import instant_inputs, table, MIN_DATE, MAX_DATE, ERRORS
from vedic_astro.relationship_records import chart_key, local_instant
from vedic_astro.relationship_v2.engine import analyze_v2
from vedic_astro.relationship_v2.windows import scan_v2
from vedic_astro.relationship_v2.provenance import freeze_metadata

LABELS = {
    'romance': 'Romance / Attraction',
    'partner_entry': 'Significant Partner Entry',
    'commitment': 'Commitment / Marriage Development',
    'stress': 'Relationship Stress / Separation',
}
WINDOW_LABELS = dict(zip(LABELS, (
    'Romance-active windows', 'Significant-partner-entry windows',
    'Commitment windows', 'Relationship-stress windows')))


def summary(result):
    return ' '.join(f"{label}: {result['assessments'][key]['state']}."
                    for key, label in LABELS.items())


def local(value, zone):
    from datetime import datetime
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.astimezone(ZoneInfo(zone)).isoformat()


def evidence_rows(result, ids, category):
    return [{'Actor': e['actor'], 'Target': e['target'],
             'Reference': ', '.join(e['references']),
             'Role': ', '.join(e['roles']),
             'Use in this category': e['category_use'][category]['status'],
             'Reason': e['category_use'][category]['reason']}
            for e in result['evidence'] if e['id'] in ids]


def periods(result, zone):
    table([{'Level': p['level'], 'Lord': p['lord'],
            'Start (local)': local(p['start'], zone),
            'End (local, exclusive)': local(p['end'], zone)} for p in result['dashas']])


def category_details(result, category, zone):
    a = result['assessments'][category]
    st.write('Passed gates: ' + (', '.join(a['gates_passed']) or 'None'))
    st.write('Failed gates: ' + (', '.join(a['gates_failed']) or 'None'))
    st.markdown('**Exact missing requirements**')
    table(a['missing_requirements'])
    st.markdown('**Selected gate witnesses**')
    ids = {i for values in a['gate_witnesses'].values() for i in values}
    table(evidence_rows(result, ids, category))
    st.markdown('**Structural evidence and its category usage**')
    table(evidence_rows(result, result['layers']['structural_evidence'], category))
    st.write('Distinct gate actors: ' + (', '.join(a['distinct_gate_actors']) or 'None selected'))
    st.caption('A failed complete gate combination can leave no selected actors. Romance has no two-actor gate.')
    st.markdown('**Active MD / AD / PD**')
    periods(result, zone)
    st.markdown('**D9 corroboration candidates**')
    table(evidence_rows(result, {e['id'] for e in result['evidence']
                                if 'd9_corroboration' in e['feature_roles']}, category))
    st.markdown('**UL / DK corroboration and context**')
    table(evidence_rows(result, result['layers']['ul_dk_evidence'], category))
    st.markdown('**Moon / Chandra Lagna gochara**')
    table([{'Graha': p, 'House from Moon / Chandra Lagna': v['house_from_moon'],
            'Climate': v['status'], 'Vedha blockers': ', '.join(v['blockers']) or 'None'}
           for p, v in result['general_gochara'].items()])
    st.write(f"Fast trigger active: {a['trigger_active']}")
    table(evidence_rows(result, result['layers']['fast_evidence'], category))
    for warning in result['data_quality']['warnings']:
        st.warning(warning)


def show_snapshot(result, zone):
    st.caption(f"Evaluated instant: {local(result['at_utc'], zone)} · {result['ayanamsa']}")
    st.write(summary(result))
    categories = list(LABELS.items())
    for start in (0, 2):
        for column, (key, label) in zip(st.columns(2), categories[start:start + 2]):
            with column:
                card(escape(label), escape(result['assessments'][key]['state']))
    for key, label in LABELS.items():
        with st.expander(f'{label} — gate details'):
            category_details(result, key, zone)
    with st.expander('Advanced calculation details'):
        st.json(json.dumps(result, default=str))


def show_windows(result, zone):
    st.caption(f"Scanned {local(result['start'], zone)} to {local(result['end'], zone)} (exclusive).")
    for warning in result['limitations']:
        st.caption(warning)
    by_start = {s['start']: s['result'] for s in result['segments']}
    for key, label in WINDOW_LABELS.items():
        st.subheader(label)
        windows = [w for w in result['windows'] if w['kind'] == key]
        if not windows:
            st.write('No qualifying windows in this range.')
        for w in windows:
            triggers = [t for t in result['windows'] if t['kind'] == key + '_trigger'
                        and t['start'] < w['end'] and t['end'] > w['start']]
            st.write(f"{local(w['start'], zone)} → {local(w['end'], zone)} (exclusive)")
            st.write(f"Trigger sub-intervals exist: {bool(triggers)}")
            rows = []
            for s in w['segments']:
                a = s['assessment']; snapshot = by_start[s['start']]
                ids = {i for values in a['gate_witnesses'].values() for i in values}
                witnesses = [e for e in snapshot['evidence'] if e['id'] in ids
                             and any(layer in e['layers'] for layer in ('structural', 'ul_dk'))]
                rows.append({'Start': local(s['start'], zone), 'End (exclusive)': local(s['end'], zone),
                             'AD / PD': ' / '.join(p['lord'] for p in s['dashas'] if p['level'] in ('AD','PD')),
                             'Exact state': a['state'],
                             'Key structural witnesses': '; '.join(e['actor'] + ' → ' + e['target'] for e in witnesses) or 'None'})
            table(rows)
            with st.expander(f"Window details — {label} — {local(w['start'], zone)}"):
                table([{'Trigger start': local(t['start'], zone), 'Trigger end (exclusive)': local(t['end'], zone)} for t in triggers])
                for s in w['segments']:
                    st.markdown(f"**Segment {local(s['start'], zone)}**")
                    category_details(by_start[s['start']], key, zone)
                st.json(json.dumps(w, default=str))
    with st.expander('Advanced calculation details — scan'):
        st.json(json.dumps(result, default=str))


def render_relationship_v2(chart):
    st.caption('EXPERIMENTAL / DEVELOPER · relationship_timing_v2_0 · descriptive gate states')
    integrity = freeze_metadata()
    if integrity['status'] != 'verified':
        st.error('Frozen v2 integrity check failed. Evaluation is disabled.')
        st.json(integrity)
        return
    key = chart_key(chart)
    with st.form('v2_snapshot_form'):
        day, clock, zone, fold = instant_inputs('v2_snapshot', 'America/Los_Angeles', optional=True)
        run = st.form_submit_button('Evaluate with v2')
    if run:
        st.session_state.pop('v2_snapshot_result', None)
        try:
            at = local_instant(day, clock or time(12), zone, fold)
            result = analyze_v2(chart, at)
            st.session_state['v2_snapshot_result'] = (key, zone, clock is None, result)
        except ERRORS as e:
            st.error(str(e))
    saved = st.session_state.get('v2_snapshot_result')
    if saved and saved[0] == key:
        if saved[2]:
            st.warning('Exact time unknown: local noon used. Moon and fast-trigger findings are provisional.')
        show_snapshot(saved[3], saved[1])
    elif saved:
        st.info('Natal profile changed. Evaluate again for the current chart.')
    st.divider()
    st.subheader('Date-range scan')
    st.caption('Runs only on submission. End date is included through local midnight of the following day. Long ranges may take time.')
    with st.form('v2_scan_form'):
        start = st.date_input('Start date', value=date.today(), min_value=MIN_DATE, max_value=MAX_DATE, key='v2_start')
        end = st.date_input('End date', value=date.today(), min_value=MIN_DATE, max_value=MAX_DATE, key='v2_end')
        zone = st.text_input('Scan timezone (IANA name)', value='America/Los_Angeles', key='v2_scan_zone')
        scan = st.form_submit_button('Scan date range with v2')
    if scan:
        st.session_state.pop('v2_scan_result', None)
        try:
            if end < start:
                raise ValueError('End date must be on or after start date.')
            a = local_instant(start, time(0), zone, None)
            b = local_instant(end + timedelta(days=1), time(0), zone, None)
            with st.spinner('Evaluating frozen v2 windows…'):
                result = scan_v2(chart, a, b)
            st.session_state['v2_scan_result'] = (key, zone, result)
        except ERRORS as e:
            st.error(str(e))
    saved = st.session_state.get('v2_scan_result')
    if saved and saved[0] == key:
        show_windows(saved[2], saved[1])
    elif saved:
        st.info('Natal profile changed. Submit a new scan for the current chart.')
