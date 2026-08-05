"""Shared birth-details form, used by every calculator page.

Stores the computed chart in st.session_state, which Streamlit shares
across all pages in a multi-page app -- so entering birth details once on
any page makes it available on every other page too.
"""

from datetime import date, datetime, time

import streamlit as st

from vedic_astro.chart import NatalChart, compute_natal_chart
from vedic_astro.constants import AYANAMSA_DESCRIPTIONS, AYANAMSA_OVERVIEW_BLURB, AYANAMSAS, DEFAULT_AYANAMSA
from vedic_astro.location import LocationError, Place, geocode_place, local_to_utc


@st.cache_data(show_spinner=False)
def _geocode(place_name: str) -> Place:
    return geocode_place(place_name)


@st.cache_data(show_spinner=False)
def _compute_chart(birth_dt_utc: datetime, lat: float, lon: float, ayanamsa: str) -> NatalChart:
    return compute_natal_chart(birth_dt_utc, lat, lon, ayanamsa)


def birth_details_form() -> None:
    has_chart = "chart" in st.session_state
    container = st.expander("Change birth details", expanded=not has_chart) if has_chart else st.container()

    with container:
        with st.form("birth_details"):
            st.subheader("Birth details")
            col1, col2 = st.columns(2)
            with col1:
                birth_date = st.date_input(
                    "Date of birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1), max_value=date.today()
                )
            with col2:
                birth_time = st.time_input("Time of birth", value=time(12, 0))
            birth_place = st.text_input("Place of birth", placeholder="e.g. Pune, Maharashtra, India")
            ayanamsa = st.selectbox(
                "Ayanamsa", options=list(AYANAMSAS), index=list(AYANAMSAS).index(DEFAULT_AYANAMSA)
            )
            with st.expander("What's an ayanamsa?"):
                st.caption(AYANAMSA_OVERVIEW_BLURB)
                for name, description in AYANAMSA_DESCRIPTIONS.items():
                    st.markdown(f"**{name}** — {description}")
            submitted = st.form_submit_button("Compute chart")

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


def get_chart():
    """Returns (chart, place), or (None, None) if not yet computed."""
    return st.session_state.get("chart"), st.session_state.get("place")
