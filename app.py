"""Sade Sati Calculator -- Streamlit app.

Enter your birth details and see whether you're currently in Sade Sati
(Saturn's ~7.5-year transit through the 12th, 1st, and 2nd houses from your
natal Moon), which phase, and roughly how much longer.

This is one of several single-purpose Vedic transit/dasha calculators built
on the same `vedic_astro` core library -- see the sidebar for the others.
"""

from datetime import datetime, timezone

import streamlit as st

from common import birth_details_form, get_chart
from vedic_astro.transits import compute_sade_sati

st.set_page_config(page_title="Sade Sati Calculator", page_icon="🪐", layout="centered")


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

birth_details_form()
chart, place = get_chart()

if chart:
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
    st.info("Enter your birth details above and click **Compute chart** to get started.")
