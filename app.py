"""Vedic Transit & Dasha Calculator -- Streamlit app.

Enter your birth details once, then switch between calculators (Sade Sati,
Sun & Venus Mahadasha, ...) via tabs. Each tab is a self-contained,
single-purpose view built on the same `vedic_astro` core library.
"""

from datetime import datetime, timezone

import streamlit as st

from common import birth_details_form, get_chart
from vedic_astro.constants import SUN, VENUS
from vedic_astro.dasha import mahadasha_periods_for_lords
from vedic_astro.transits import SADE_SATI_OVERVIEW_BLURB, SADE_SATI_PHASE_BLURBS, compute_sade_sati

st.set_page_config(page_title="Vedic Transit & Dasha Calculator", page_icon="🪐", layout="centered")


def _format_timedelta_years_months(td) -> str:
    total_days = td.days
    years, remainder_days = divmod(total_days, 365)
    months = remainder_days // 30
    if years and months:
        return f"{years}y {months}m"
    if years:
        return f"{years}y"
    return f"{months}m" if months else "< 1m"


def _render_sade_sati(chart) -> None:
    st.metric("Natal Moon Rashi", chart.moon_rashi)

    with st.spinner("Checking Saturn's transit..."):
        sade_sati = compute_sade_sati(chart)

    if sade_sati.active:
        st.warning(f"**Active — {sade_sati.phase}** · Saturn transiting {sade_sati.saturn_rashi}")
        st.caption(SADE_SATI_PHASE_BLURBS[sade_sati.phase])
    else:
        st.success(f"Not active · Saturn transiting {sade_sati.saturn_rashi}")
        st.caption(SADE_SATI_OVERVIEW_BLURB)

    if sade_sati.next_transition:
        remaining = sade_sati.next_transition - datetime.now(timezone.utc)
        st.caption(
            f"Saturn moves to the next sign around {sade_sati.next_transition.date()} "
            f"(~{_format_timedelta_years_months(remaining)} from now)"
        )


def _render_mahadasha(chart) -> None:
    moon_longitude = chart.planets["Moon"].longitude
    periods = mahadasha_periods_for_lords(chart.birth_datetime_utc, moon_longitude, [SUN, VENUS])
    now = datetime.now(timezone.utc)

    col1, col2 = st.columns(2)
    for col, lord in zip((col1, col2), (SUN, VENUS)):
        period = periods[lord]
        with col:
            st.metric(f"{lord} Mahadasha", f"{period.start.date()} → {period.end.date()}")
            if period.contains(now):
                st.success("Currently active")
            elif now < period.start:
                st.caption("Upcoming")
            else:
                st.caption("Already passed")


st.title("🪐 Vedic Transit & Dasha Calculator")
st.caption("Sidereal (Lahiri) Vedic astrology.")

birth_details_form()
chart, place = get_chart()

if chart:
    st.divider()
    st.caption(f"{place.address} · {place.timezone} · Ayanamsa: {chart.ayanamsa}")

    tab_sade_sati, tab_mahadasha = st.tabs(["Sade Sati", "Sun & Venus Mahadasha"])
    with tab_sade_sati:
        _render_sade_sati(chart)
    with tab_mahadasha:
        _render_mahadasha(chart)
else:
    st.info("Enter your birth details above and click **Compute chart** to get started.")
