"""Vedic Transit Tracker -- Streamlit app.

Enter your birth details once, then see your natal chart, current
Vimshottari dasha, Sade Sati status, and live planetary transits relative
to your chart.
"""

from datetime import date, datetime, time, timezone

import pandas as pd
import streamlit as st

from vedic_astro.chart import NatalChart, compute_natal_chart
from vedic_astro.constants import AYANAMSAS, DEFAULT_AYANAMSA, GRAHAS
from vedic_astro.dasha import current_dasha
from vedic_astro.location import LocationError, geocode_place, local_to_utc
from vedic_astro.transits import compute_sade_sati, compute_transits

st.set_page_config(page_title="Vedic Transit Tracker", page_icon="🪐", layout="centered")


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


st.title("🪐 Vedic Transit Tracker")
st.caption("Sidereal (Lahiri) birth chart, Vimshottari dasha, and live gochara transits.")

with st.form("birth_details"):
    st.subheader("Birth details")
    col1, col2 = st.columns(2)
    with col1:
        birth_date = st.date_input("Date of birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
    with col2:
        birth_time = st.time_input("Time of birth", value=time(12, 0))
    birth_place = st.text_input("Place of birth", placeholder="e.g. Pune, Maharashtra, India")
    ayanamsa = st.selectbox("Ayanamsa", options=list(AYANAMSAS), index=list(AYANAMSAS).index(DEFAULT_AYANAMSA))
    submitted = st.form_submit_button("Generate chart")

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
    st.subheader("Natal chart")
    st.caption(f"{place.address} · {place.timezone} · Ayanamsa: {chart.ayanamsa}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Lagna (Ascendant)", chart.ascendant_rashi)
    c2.metric("Moon Rashi", chart.moon_rashi)
    c3.metric("Moon Nakshatra", f"{chart.moon_nakshatra} (pada {chart.moon_pada})")

    planet_rows = [
        {
            "Graha": name,
            "Rashi": p.rashi,
            "House (from Lagna)": p.house,
            "Retrograde": "Yes" if p.retrograde else "",
        }
        for name, p in chart.planets.items()
    ]
    st.dataframe(pd.DataFrame(planet_rows), hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("Current Vimshottari dasha")
    moon_longitude = chart.planets["Moon"].longitude
    dasha_status = current_dasha(chart.birth_datetime_utc, moon_longitude)
    d1, d2 = st.columns(2)
    with d1:
        st.metric("Mahadasha", dasha_status.mahadasha.lord)
        st.caption(
            f"{dasha_status.mahadasha.start.date()} → {dasha_status.mahadasha.end.date()}"
        )
    with d2:
        st.metric("Antardasha", dasha_status.antardasha.lord)
        st.caption(
            f"{dasha_status.antardasha.start.date()} → {dasha_status.antardasha.end.date()}"
        )

    st.divider()
    st.subheader("Sade Sati")
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

    st.divider()
    st.subheader("Live transits")
    transit_date = st.date_input("Transit date", value=date.today(), key="transit_date")
    transit_dt_utc = datetime.combine(transit_date, time(12, 0), tzinfo=timezone.utc)

    transits = compute_transits(chart, at_dt=transit_dt_utc, ayanamsa_name=chart.ayanamsa)
    transit_rows = [
        {
            "Graha": name,
            "Rashi": t.rashi,
            "House (from Moon)": t.house_from_moon,
            "House (from Lagna)": t.house_from_lagna,
            "Retrograde": "Yes" if t.retrograde else "",
        }
        for name, t in transits.items()
    ]
    st.dataframe(pd.DataFrame(transit_rows), hide_index=True, use_container_width=True)
else:
    st.info("Enter your birth details above and click **Generate chart** to get started.")
