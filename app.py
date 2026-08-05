"""Vedic Transit & Dasha Calculator -- Streamlit app.

Enter your birth details once, then switch between calculators (Sade Sati,
Sun & Venus Mahadasha, ...) via tabs. Each tab is a self-contained,
single-purpose view built on the same `vedic_astro` core library.
"""

from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from common import birth_details_form, get_chart
from styling import badge, card, inject_theme
from vedic_astro.constants import SUN, VENUS
from vedic_astro.dasha import DASHA_OVERVIEW_BLURB, current_dasha, mahadasha_periods_for_lords
from vedic_astro.transits import (
    GURU_GOCHAR_OVERVIEW_BLURB,
    SADE_SATI_OVERVIEW_BLURB,
    SADE_SATI_PHASE_BLURBS,
    compute_guru_gochar,
    compute_sade_sati,
    compute_transits,
)
from vedic_astro.util import rashi_display_name

LIVE_TRANSITS_REFRESH_MS = 30_000

st.set_page_config(page_title="Vedic Transit & Dasha Calculator", page_icon="🪐", layout="centered")
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


def _render_live_transits(chart) -> None:
    st_autorefresh(interval=LIVE_TRANSITS_REFRESH_MS, key="live_transits_autorefresh")

    now = datetime.now(timezone.utc)
    st.caption(f"Live · last updated {now.strftime('%H:%M:%S')} UTC · refreshes every 30s")

    transits = compute_transits(chart, at_dt=now, ayanamsa_name=chart.ayanamsa)
    rows = [
        {
            "Graha": name,
            "Rashi": rashi_display_name(t.rashi),
            "House (from Moon)": t.house_from_moon,
            "House (from Lagna)": t.house_from_lagna,
            "Retrograde": "Yes" if t.retrograde else "",
        }
        for name, t in transits.items()
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


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


st.title("🪐 Vedic Transit & Dasha Calculator")
st.caption("Sidereal (Lahiri) Vedic astrology.")

birth_details_form()
chart, place = get_chart()

if chart:
    st.divider()
    st.caption(f"{place.address} · {place.timezone} · Ayanamsa: {chart.ayanamsa}")

    tab_natal, tab_live, tab_sade_sati, tab_guru_gochar, tab_current_dasha, tab_mahadasha = st.tabs(
        ["Natal Chart", "Live Transits", "Sade Sati", "Guru Gochar", "Current Dasha", "Sun & Venus Mahadasha"]
    )
    with tab_natal:
        _render_natal_chart(chart)
    with tab_live:
        _render_live_transits(chart)
    with tab_sade_sati:
        _render_sade_sati(chart)
    with tab_guru_gochar:
        _render_guru_gochar(chart)
    with tab_current_dasha:
        _render_current_dasha(chart)
    with tab_mahadasha:
        _render_mahadasha(chart)
else:
    st.info("Enter your birth details above and click **Compute chart** to get started.")
