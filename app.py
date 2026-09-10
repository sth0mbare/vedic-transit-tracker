"""Vedic Transit & Dasha Calculator -- Streamlit app.

Enter your birth details once, then switch between calculators (Sade Sati,
Sun & Venus Mahadasha, ...) via tabs. Each tab is a self-contained,
single-purpose view built on the same `vedic_astro` core library.
"""

from datetime import date, datetime, time, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from common import birth_details_form, get_chart
from styling import GRAHA_COLORS, badge, card, inject_theme
from vedic_astro.constants import SUN, VENUS
from vedic_astro.dasha import (
    DASHA_OVERVIEW_BLURB,
    current_dasha,
    full_mahadasha_sequence,
    mahadasha_periods_for_lords,
)
from vedic_astro.horoscope import compute_weekly_horoscope
from vedic_astro.divisional import compute_chaturthamsa_chart, compute_dasamsa_chart
from vedic_astro.navamsa import compute_navamsa_chart
from vedic_astro.transits import (
    COMBUST_OVERVIEW_BLURB,
    GURU_GOCHAR_OVERVIEW_BLURB,
    HOUSE_SIGNIFICATIONS_FROM_MOON,
    JUPITER_COMBUSTION_ORB_DEGREES,
    RETROGRADE_OVERVIEW_BLURB,
    SADE_SATI_OVERVIEW_BLURB,
    SADE_SATI_PHASE_BLURBS,
    compute_guru_gochar,
    compute_sade_sati,
    compute_transits,
)
from vedic_astro.util import rashi_display_name

LIVE_TRANSITS_REFRESH_MS = 30_000

st.set_page_config(page_title="Vedic Horoscope, Transit, & Dasha Calculator", page_icon="🪐", layout="centered", initial_sidebar_state="expanded")
inject_theme()


def _format_timedelta_years_months(td) -> str:
    total_days = td.days
    years, remainder_days = divmod(total_days, 365)
    months = remainder_days // 30
    if years and months:
        return f"{years}y {months}m"
    if years:
        return f"{years}y"
    return f"{months}m" if months else "< 1m"


def _render_natal_chart(chart) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        card("Lagna (Ascendant)", rashi_display_name(chart.ascendant_rashi))
    with col2:
        card("Moon Rashi", rashi_display_name(chart.moon_rashi))
    with col3:
        card("Moon Nakshatra", f"{chart.moon_nakshatra} (pada {chart.moon_pada})")

    st.caption(f"Moon's nakshatra lord: {chart.moon_nakshatra_lord}")

    rows = [
        {
            "Graha": name,
            "Rashi": rashi_display_name(p.rashi),
            "House (from Lagna)": p.house,
            "Retrograde": "Yes" if p.retrograde else "",
        }
        for name, p in chart.planets.items()
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_navamsa_chart(chart) -> None:
    navamsa = compute_navamsa_chart(chart)
    card("Navamsa Lagna (D9 Ascendant)", rashi_display_name(navamsa.ascendant_rashi))
    st.caption(f"Derived from your natal sidereal positions · Ayanamsa: {navamsa.ayanamsa}")
    rows = [
        {
            "Graha": name,
            "D9 Rashi": rashi_display_name(p.rashi),
            "D9 House": p.house,
            "Retrograde (natal)": "Yes" if p.natal_retrograde else "No",
        }
        for name, p in navamsa.planets.items()
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption(
        "D9 houses are counted from the Navamsa Lagna. Retrograde status comes "
        "from the natal planetary calculation; it is not calculated independently for D9."
    )


def _render_divisional_chart(chart, name, compute) -> None:
    result = compute(chart)
    label = f"D{result.division}"
    card(f"{name} Lagna ({label} Ascendant)", rashi_display_name(result.ascendant_rashi))
    st.caption(f"Derived from your natal sidereal positions · Ayanamsa: {result.ayanamsa}")
    st.dataframe(pd.DataFrame([
        {"Graha": p.name, f"{label} Rashi": rashi_display_name(p.rashi),
         f"{label} House": p.house,
         "Retrograde (natal)": "Yes" if p.natal_retrograde else "No"}
        for p in result.planets.values()
    ]), hide_index=True, use_container_width=True)
    st.caption(
        f"{label} houses are counted from the {name} Lagna. Retrograde status comes "
        f"from the natal planetary calculation; it is not calculated independently for {label}."
    )


def _transit_rows(transits) -> list[dict]:
    return [
        {
            "Graha": name,
            "Rashi": rashi_display_name(t.rashi),
            "House (Moon)": t.house_from_moon,
            "House (Lagna)": t.house_from_lagna,
            "Retro": "Yes" if t.retrograde else "",
            "Sep. from Sun": (
                f"{t.separation_from_sun_degrees:.1f}°" if t.separation_from_sun_degrees is not None else "—"
            ),
            "Combust": "Yes" if t.combust else ("—" if t.combust is None else ""),
            "Next Change": t.next_sign_change.date().isoformat() if t.next_sign_change else "—",
        }
        for name, t in transits.items()
    ]


def _render_live_transits(chart) -> None:
    st_autorefresh(interval=LIVE_TRANSITS_REFRESH_MS, key="live_transits_autorefresh")

    now = datetime.now(timezone.utc)
    st.caption(f"Live · last updated {now.strftime('%H:%M:%S')} UTC · refreshes every 30s")

    transits = compute_transits(chart, at_dt=now, ayanamsa_name=chart.ayanamsa)
    st.dataframe(pd.DataFrame(_transit_rows(transits)), hide_index=True, use_container_width=True)

    retrograde_names = [name for name, t in transits.items() if t.retrograde]
    if retrograde_names:
        st.warning(f"Currently retrograde: {', '.join(retrograde_names)}")
        st.caption(RETROGRADE_OVERVIEW_BLURB)

    combust_names = [name for name, t in transits.items() if t.combust]
    if combust_names:
        st.warning(f"Currently combust: {', '.join(combust_names)}")
        st.caption(COMBUST_OVERVIEW_BLURB)

    st.divider()
    st.subheader("Notable Weekly Transits")
    horoscope = compute_weekly_horoscope(chart, transits, start_dt=now, ayanamsa_name=chart.ayanamsa)
    st.caption(f"{horoscope.start} to {horoscope.end}")

    moon_text = " → ".join(rashi_display_name(m.rashi) for m in horoscope.moon_journey)
    card("Moon's Journey This Week", moon_text)

    # Only Sun and Moon for now; other grahas can be added once we decide
    # what's worth surfacing at a weekly cadence.
    sun_change = horoscope.upcoming_sign_changes.get("Sun")
    if sun_change:
        st.markdown("**Other notable transits this week:**")
        st.markdown(f"- **Sun** moves into a new sign around {sun_change.next_sign_change.date()}")

    with st.expander("What do these houses mean?"):
        st.caption("Houses are counted from your natal Moon -- the traditional Vedic reference point for gochara.")
        for house_num, signification in HOUSE_SIGNIFICATIONS_FROM_MOON.items():
            st.markdown(f"**House {house_num}** — {signification}")


def _render_past_transits(chart) -> None:
    st.caption("Look up where the grahas were, relative to your natal chart, on any date in the past.")

    today = datetime.now(timezone.utc).date()
    col1, col2 = st.columns(2)
    with col1:
        query_date = st.date_input(
            "Date", value=today, min_value=date(1900, 1, 1), max_value=today, key="past_transits_date"
        )
    with col2:
        query_time = st.time_input("Time (UTC)", value=time(12, 0), key="past_transits_time")

    at_dt = datetime.combine(query_date, query_time, tzinfo=timezone.utc)
    if at_dt > datetime.now(timezone.utc):
        st.error("Please pick a date/time in the past.")
        return

    transits = compute_transits(chart, at_dt=at_dt, ayanamsa_name=chart.ayanamsa)
    st.caption(f"Transits as of {at_dt.strftime('%Y-%m-%d %H:%M')} UTC")
    st.dataframe(pd.DataFrame(_transit_rows(transits)), hide_index=True, use_container_width=True)

    retrograde_names = [name for name, t in transits.items() if t.retrograde]
    if retrograde_names:
        st.warning(f"Retrograde on this date: {', '.join(retrograde_names)}")
        st.caption(RETROGRADE_OVERVIEW_BLURB)

    combust_names = [name for name, t in transits.items() if t.combust]
    if combust_names:
        st.warning(f"Combust on this date: {', '.join(combust_names)}")
        st.caption(COMBUST_OVERVIEW_BLURB)


def _render_sade_sati(chart) -> None:
    card("Natal Moon Rashi", rashi_display_name(chart.moon_rashi))

    with st.spinner("Checking Saturn's transit..."):
        sade_sati = compute_sade_sati(chart)

    if sade_sati.active:
        status_badge = badge(f"Active — {sade_sati.phase}", "upcoming")
        blurb = SADE_SATI_PHASE_BLURBS[sade_sati.phase]
    else:
        status_badge = badge("Not active", "active")
        blurb = SADE_SATI_OVERVIEW_BLURB

    card("Sade Sati Status", f"Saturn transiting {rashi_display_name(sade_sati.saturn_rashi)}", status_badge)
    st.caption(blurb)

    if sade_sati.next_transition:
        remaining = sade_sati.next_transition - datetime.now(timezone.utc)
        st.caption(
            f"Saturn moves to the next sign around {sade_sati.next_transition.date()} "
            f"(~{_format_timedelta_years_months(remaining)} from now)"
        )


def _render_guru_gochar(chart) -> None:
    card("Natal Moon Rashi", rashi_display_name(chart.moon_rashi))

    with st.spinner("Checking Jupiter's transit..."):
        guru_gochar = compute_guru_gochar(chart)

    house_label = f"house {guru_gochar.house_from_moon} from Moon"
    if guru_gochar.favorable:
        status_badge = badge(f"Favorable — {house_label}", "active")
    else:
        status_badge = badge(f"Challenging — {house_label}", "upcoming")

    card(
        "Guru Gochar Status",
        f"Jupiter transiting {rashi_display_name(guru_gochar.jupiter_rashi)}",
        status_badge,
    )
    st.caption(GURU_GOCHAR_OVERVIEW_BLURB)

    if guru_gochar.retrograde:
        st.warning("Jupiter is currently retrograde")
        st.caption(RETROGRADE_OVERVIEW_BLURB)

    if guru_gochar.combust:
        st.warning("Jupiter is currently combust (close to the Sun)")
        st.caption(COMBUST_OVERVIEW_BLURB)

    proximity_note = ""
    if abs(guru_gochar.separation_from_sun_degrees - JUPITER_COMBUSTION_ORB_DEGREES) <= 2.0:
        proximity_note = " — close to the edge of the combustion orb"
    st.caption(
        f"{guru_gochar.separation_from_sun_degrees:.1f}° from the Sun "
        f"(combustion orb is {JUPITER_COMBUSTION_ORB_DEGREES:.0f}°){proximity_note}"
    )

    if guru_gochar.next_transition:
        remaining = guru_gochar.next_transition - datetime.now(timezone.utc)
        st.caption(
            f"Jupiter moves to the next sign around {guru_gochar.next_transition.date()} "
            f"(~{_format_timedelta_years_months(remaining)} from now)"
        )


def _render_current_dasha(chart) -> None:
    moon_longitude = chart.planets["Moon"].longitude
    status = current_dasha(chart.birth_datetime_utc, moon_longitude)
    now = datetime.now(timezone.utc)

    col1, col2 = st.columns(2)
    with col1:
        card("Mahadasha", status.mahadasha.lord)
        st.caption(f"{status.mahadasha.start.date()} → {status.mahadasha.end.date()}")
    with col2:
        card("Antardasha", status.antardasha.lord)
        st.caption(f"{status.antardasha.start.date()} → {status.antardasha.end.date()}")

    st.caption(DASHA_OVERVIEW_BLURB)

    remaining = status.antardasha.end - now
    st.caption(
        f"Current antardasha ends around {status.antardasha.end.date()} "
        f"(~{_format_timedelta_years_months(remaining)} from now)"
    )

    st.divider()
    st.caption("Coming up next")

    col3, col4 = st.columns(2)
    with col3:
        card("Next Mahadasha", status.next_mahadasha.lord)
        st.caption(f"{status.next_mahadasha.start.date()} → {status.next_mahadasha.end.date()}")
    with col4:
        card("Next Antardasha", status.next_antardasha.lord)
        st.caption(f"{status.next_antardasha.start.date()} → {status.next_antardasha.end.date()}")

    st.divider()
    st.caption("Full mahadasha timeline (whole 120-year cycle)")

    sequence = full_mahadasha_sequence(chart.birth_datetime_utc, moon_longitude)
    timeline_df = pd.DataFrame(
        {"Dasha": "Mahadasha", "Lord": p.lord, "Start": p.start, "End": p.end} for p in sequence
    )
    fig = px.timeline(
        timeline_df,
        x_start="Start",
        x_end="End",
        y="Dasha",
        color="Lord",
        category_orders={"Lord": [p.lord for p in sequence]},
        color_discrete_map=GRAHA_COLORS,
    )
    fig.add_vline(x=now, line_width=2, line_dash="dash", line_color="#B8860B")
    fig.update_yaxes(visible=False, title=None)
    fig.update_xaxes(showgrid=False, color="#1F2A37")
    fig.update_layout(
        height=180,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1F2A37", family="Times New Roman, Times, serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The gold dashed line marks today.")


def _render_mahadasha(chart) -> None:
    moon_longitude = chart.planets["Moon"].longitude
    periods = mahadasha_periods_for_lords(chart.birth_datetime_utc, moon_longitude, [SUN, VENUS])
    now = datetime.now(timezone.utc)

    col1, col2 = st.columns(2)
    for col, lord in zip((col1, col2), (SUN, VENUS)):
        period = periods[lord]
        if period.contains(now):
            status_badge = badge("Currently active", "active")
        elif now < period.start:
            status_badge = badge("Upcoming", "upcoming")
        else:
            status_badge = badge("Already passed", "neutral")
        with col:
            card(f"{lord} Mahadasha", f"{period.start.date()} → {period.end.date()}", status_badge)


st.title("🪐 Vedic Horoscope, Transit, & Dasha Calculator")
st.caption("Sidereal (Lahiri) Vedic astrology.")

birth_details_form()
chart, place = get_chart()

if chart:
    st.divider()
    st.caption(f"{place.address} · {place.timezone} · Ayanamsa: {chart.ayanamsa}")

    views = {
        "D1 · Natal Chart": lambda: _render_natal_chart(chart),
        "D4 · Chaturthamsa": lambda: _render_divisional_chart(chart, "Chaturthamsa", compute_chaturthamsa_chart),
        "D9 · Navamsa": lambda: _render_navamsa_chart(chart),
        "D10 · Dasamsa": lambda: _render_divisional_chart(chart, "Dasamsa", compute_dasamsa_chart),
        "Live Transits": lambda: _render_live_transits(chart),
        "Past Transits": lambda: _render_past_transits(chart),
        "Sade Sati": lambda: _render_sade_sati(chart),
        "Guru Gochar": lambda: _render_guru_gochar(chart),
        "Current Dasha": lambda: _render_current_dasha(chart),
        "Sun & Venus Mahadasha": lambda: _render_mahadasha(chart),
    }
    if st.session_state.get("selected_chart_view") not in views:
        st.session_state["selected_chart_view"] = next(iter(views))

    def select_view(view):
        st.session_state["selected_chart_view"] = view

    selected_view = st.session_state["selected_chart_view"]
    with st.sidebar:
        st.subheader("Charts & Calculators")
        for view in views:
            st.button(
                view,
                key=f"nav_{view}",
                type="primary" if view == selected_view else "secondary",
                use_container_width=True,
                on_click=select_view,
                args=(view,),
            )
    st.subheader(selected_view)
    views[selected_view]()

else:
    st.info("Enter your birth details above and click **Compute chart** to get started.")

st.divider()
st.markdown(
    '<div class="vt-footer">© 2026 Shivani Thombare</div>',
    unsafe_allow_html=True,
)
