"""Unified Today/Choose Date UI. Forecast and contextual interpretation come later."""
from dataclasses import asdict
from datetime import date, datetime, time, timezone
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from vedic_astro.transit_context import compute_snapshot, TransitSnapshot
from vedic_astro.timing import HierarchyPeriod
from vedic_astro.relationship_records import local_instant
from vedic_astro.horoscope import compute_weekly_horoscope, WeeklyHoroscope, MoonDay
from vedic_astro.transits import HOUSE_SIGNIFICATIONS_FROM_MOON, RETROGRADE_OVERVIEW_BLURB, COMBUST_OVERVIEW_BLURB, TransitPlacement
from vedic_astro.util import rashi_display_name


@st.cache_data(ttl=30, show_spinner=False)
def _cached_snapshot_data(chart, at):
    # Cache data rather than module-defined instances: hot reloads can leave
    # otherwise valid dataclasses with identities that pickle cannot resolve.
    return asdict(compute_snapshot(chart, at))


def cached_snapshot(chart, at):
    data = _cached_snapshot_data(chart, at)
    return TransitSnapshot(**{**data,
        'placements': {name: TransitPlacement(**p) for name, p in data['placements'].items()},
        'periods': tuple(HierarchyPeriod(**p) for p in data['periods'])})


@st.cache_data(ttl=30, show_spinner=False)
def _cached_weekly_data(chart, placements, at):
    return asdict(compute_weekly_horoscope(chart, placements, start_dt=at, ayanamsa_name=chart.ayanamsa))


def weekly_snapshot(chart, placements, at):
    data = _cached_weekly_data(chart, placements, at)
    return WeeklyHoroscope(**{**data,
        'moon_journey': [MoonDay(**p) for p in data['moon_journey']],
        'upcoming_sign_changes': {name: TransitPlacement(**p) for name, p in data['upcoming_sign_changes'].items()}})


def local_text(at, zone):
    return at.astimezone(ZoneInfo(zone)).isoformat(sep=' ', timespec='seconds')


def transit_rows(placements, include_lagna=False):
    rows = []
    for name, p in placements.items():
        row = {'Graha': name, 'Rashi': rashi_display_name(p.rashi),
               'House from Moon / Chandra Lagna': p.house_from_moon,
               'Sidereal longitude': f'{p.longitude:.4f}°',
               'Motion': 'Retrograde' if p.retrograde else 'Direct',
               'Separation from Sun': f'{p.separation_from_sun_degrees:.1f}°' if p.separation_from_sun_degrees is not None else '—',
               'Combust': '—' if p.combust is None else 'Yes' if p.combust else 'No'}
        if include_lagna:
            row['House from natal Lagna (secondary)'] = p.house_from_lagna
        rows.append(row)
    return rows


def show_snapshot(snapshot, zone):
    st.caption(f"Calculated for {local_text(snapshot.at_utc, zone)} · {zone} · Ayanamsa: {snapshot.ayanamsa}")
    st.subheader('Calculated — transit snapshot')
    st.caption('Transit houses primarily use natal Moon / Chandra Lagna. Natal chart calculations remain Lagna-based.')
    for warning in snapshot.warnings:
        st.warning(warning)
    st.markdown('**Active MD → AD → PD**')
    if snapshot.periods:
        st.write(' → '.join(p.lord for p in snapshot.periods))
        with st.expander('Exact dasha dates'):
            st.dataframe(pd.DataFrame([{'Level': p.level, 'Lord': p.lord,
                'Start (local)': local_text(p.start, zone),
                'End (local, exclusive)': local_text(p.end, zone)} for p in snapshot.periods]), hide_index=True)
    else:
        st.write('Unavailable before birth.')
    lagna = st.checkbox('Show houses from natal Lagna (secondary context)', key='transits_lagna')
    st.dataframe(pd.DataFrame(transit_rows(snapshot.placements, lagna)), hide_index=True)
    retro = [n for n,p in snapshot.placements.items() if p.retrograde]
    combust = [n for n,p in snapshot.placements.items() if p.combust]
    st.write('Retrograde: ' + (', '.join(retro) or 'None'))
    st.write('Combust: ' + (', '.join(combust) or 'None'))
    with st.expander('Interpretation — existing general reference notes'):
        st.caption('Traditional thematic descriptions, separate from the calculated positions. Personalized contextual interpretation is planned for Phase 3.')
        st.write(RETROGRADE_OVERVIEW_BLURB)
        st.write(COMBUST_OVERVIEW_BLURB)
        for h, text in HOUSE_SIGNIFICATIONS_FROM_MOON.items():
            st.markdown(f'**House {h} from Moon / Chandra Lagna** — {text}')
    with st.expander('Advanced calculation details'):
        st.json(json.dumps(asdict(snapshot), default=str))
        st.caption('Legacy next-sign-change estimates are retained unchanged. Five-day bracketing can skip crossings; these are not an exhaustive event timeline.')
        st.dataframe(pd.DataFrame([{'Graha': n, 'Legacy next-change estimate (local)': local_text(p.next_sign_change, zone) if p.next_sign_change else '—'}
                                   for n,p in snapshot.placements.items()]), hide_index=True)


def render_transits(chart):
    mode = st.radio('Transit view', ('Today', 'Choose Date'), horizontal=True, key='transits_mode')
    zone = st.text_input('Display timezone (IANA name)', value='America/Los_Angeles', key='transits_zone')
    try:
        tz = ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        st.error('Enter a valid IANA timezone, for example America/Los_Angeles.')
        return
    if mode == 'Today':
        live = st.checkbox('Refresh every 30 seconds', value=True, key='transits_live')
        if live:
            st_autorefresh(interval=30_000, key='transits_autorefresh')
        now = datetime.now(timezone.utc)
        # Match each displayed timestamp to its actual 30-second snapshot instant.
        at = datetime.fromtimestamp(int(now.timestamp()) // 30 * 30, timezone.utc)
        with st.spinner('Calculating transits…'):
            snapshot = cached_snapshot(chart, at)
        show_snapshot(snapshot, zone)
        st.subheader('Upcoming changes — legacy weekly preview')
        st.caption('Phase 1 retains the existing approximate preview. Complete event detection and Forecast arrive in Phase 2.')
        weekly = weekly_snapshot(chart, snapshot.placements, at)
        sun = weekly.upcoming_sign_changes.get('Sun')
        if sun:
            st.write(f'Sun: next sign-change estimate {local_text(sun.next_sign_change, zone)}.')
        else:
            st.write('No Sun sign change returned by the legacy preview for the next seven days.')
        with st.expander('Short-term Moon activity — daily samples'):
            st.write(' → '.join(rashi_display_name(p.rashi) for p in weekly.moon_journey))
            st.caption('Signs sampled once per day over the next seven days; not exact lunar ingress times.')
    else:
        with st.form('transits_choose_form'):
            day = st.date_input('Date', value=datetime.now(tz).date(), min_value=date(1900,1,1), max_value=date(2200,12,31), key='transits_day')
            exact = st.checkbox('Exact time known', value=True, key='transits_exact')
            clock = st.time_input('Local time (24-hour)', value=time(12), key='transits_clock')
            occurrence = st.selectbox('If clocks repeat this time', ('Require clarification', 'First occurrence', 'Second occurrence'), key='transits_fold')
            submit = st.form_submit_button('Show transits')
        if submit:
            st.session_state.pop('transits_chosen', None)
            try:
                fold = {'Require clarification': None, 'First occurrence': 0, 'Second occurrence': 1}[occurrence]
                at = local_instant(day, clock if exact else time(12), zone, fold)
                # Save input only: current profile always determines displayed calculations.
                st.session_state['transits_chosen'] = (at, zone, exact)
            except (ValueError, OverflowError) as e:
                st.error(str(e))
        saved = st.session_state.get('transits_chosen')
        if saved:
            at, input_zone, exact = saved
            st.caption(f'Entered in {input_zone}; displayed in {zone}. Submit again to interpret the entered wall time in a different timezone.')
            if not exact:
                st.warning('Exact time unknown: local noon was used. Time-sensitive findings are provisional.')
            with st.spinner('Calculating transits…'):
                show_snapshot(cached_snapshot(chart, at), zone)
