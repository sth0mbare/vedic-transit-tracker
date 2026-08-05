"""Sun & Venus Mahadasha -- Streamlit page.

Each of the 9 grahas rules exactly one mahadasha in a person's 120-year
Vimshottari cycle. This shows when the Sun and Venus mahadashas fall for the
entered birth chart, and flags whether either is currently active.
"""

from datetime import datetime, timezone

import streamlit as st

from common import birth_details_form, get_chart
from vedic_astro.constants import SUN, VENUS
from vedic_astro.dasha import mahadasha_periods_for_lords

st.set_page_config(page_title="Sun & Venus Mahadasha", page_icon="☀️", layout="centered")

st.title("☀️ Sun & Venus Mahadasha")
st.caption("Sidereal (Lahiri) Vedic astrology -- when do your Sun and Venus mahadashas fall?")

birth_details_form()
chart, place = get_chart()

if chart:
    st.divider()
    st.caption(f"{place.address} · {place.timezone} · Ayanamsa: {chart.ayanamsa}")

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
else:
    st.info("Enter your birth details above and click **Compute chart** to get started.")
