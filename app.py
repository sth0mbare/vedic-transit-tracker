"""Sade Sati Calculator -- Streamlit app.

Enter your birth details and see whether you're currently in Sade Sati
(Saturn's ~7.5-year transit through the 12th, 1st, and 2nd houses from your
natal Moon), which phase, and roughly how much longer.

This is the first of several planned single-purpose Vedic transit
calculators built on the same `vedic_astro` core library -- kept narrow on
purpose rather than one large multi-feature dashboard.
"""

from datetime import date, datetime, time, timezone

import streamlit as st

from vedic_astro.chart import NatalChart, compute_natal_chart
from vedic_astro.constants import AYANAMSAS, DEFAULT_AYANAMSA
from vedic_astro.location import LocationError, geocode_place, local_to_utc
from vedic_astro.transits import compute_sade_sati

st.set_page_config(page_title="Sade Sati Calculator", page_icon="🪐", layout="centered")


@st.cache_data(show_spinner=False)
def _geocode(place_name: str):
    return geocode_place(place_name)


@st.cache_data(show_spinner=False)
def _compute_chart(birth_dt_utc: datetime, lat: float, lon: float, ayanamsa: str) -> NatalChart:
    return compute_natal_chart(birth_dt_utc, lat, lon, ayanamsa)


def _format_timedelta_years_months(td) -> str:
    total_days = td.days
    years, remainder_days = divmod(total_days, 365)
    months = remainder_days // 30
    if years and months:
        return f"{years}y {months}m"
    if years:
        return f"{years}y"
    return f"{months}m" if months else "< 1m"


st.title("🪐 Sade Sati Calculator")
st.caption("Sidereal (Lahiri) Vedic astrology -- is Saturn currently transiting your natal Moon?")

with st.form("birth_details"):
    st.subheader("Birth details")
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("Date of birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
    with col2:
        birth_time = st.time_input("Time of birth", value=time(12, 0))
    birth_place = st.text_input("Place of birth", placeholder="e.g. Pune, Maharashtra, India")
    ayanamsa = st.selectbox("Ayanamsa", options=list(AYANAMSAS), index=list(AYANAMSAS).index(DEFAULT_AYANAMSA))
    submitted = st.form_submit_button("Check Sade Sati")

if submitted:
    if not birth_place.strip():
        st.error("Please enter a place of birth.")
    else:
        try:
            with st.spinner("Looking up location..."):
                place = _geocode(birth_place)
            birth_dt_utc = local_to_utc(birth_date, birth_time, place.timezone)
            with st.spinner("Computing chart..."):
                chart = _compute_chart(birth_dt_utc, place.latitude, place.longitude, ayanamsa)
            st.session_state["chart"] = chart
            st.session_state["place"] = place
        except LocationError as e:
            st.error(str(e))

if "chart" in st.session_state:
    chart: NatalChart = st.session_state["chart"]
    place = st.session_state["place"]

    st.divider()
    st.caption(f"{place.address} · {place.timezone} · Ayanamsa: {chart.ayanamsa}")
    st.metric("Natal Moon Rashi", chart.moon_rashi)

    with st.spinner("Checking Saturn's transit..."):
        sade_sati = compute_sade_sati(chart)

    if sade_sati.active:
        st.warning(f"**Active — {sade_sati.phase}** · Saturn transiting {sade_sati.saturn_rashi}")
    else:
        st.success(f"Not active · Saturn transiting {sade_sati.saturn_rashi}")

    if sade_sati.next_transition:
        remaining = sade_sati.next_transition - datetime.now(timezone.utc)
        st.caption(
            f"Saturn moves to the next sign around {sade_sati.next_transition.date()} "
            f"(~{_format_timedelta_years_months(remaining)} from now)"
        )
else:
    st.info("Enter your birth details above and click **Check Sade Sati** to get started.")
