"""Shared CSS and small HTML components for a consistent look across pages.

Kept separate from app.py so the visual layer doesn't tangle with the
calculator logic -- this only ever emits markup/CSS, never computes
anything astrological.
"""

import streamlit as st

# Traditional planet/gemstone colors, used for the dasha timeline chart.
GRAHA_COLORS = {
    "Moon": "#F2F2F0",
    "Sun": "#E14B4B",
    "Mars": "#F2823C",
    "Mercury": "#4FAE6E",
    "Venus": "#F0A0C0",
    "Jupiter": "#F2CB4E",
    "Saturn": "#3D4F91",
    "Rahu": "#C6923F",  # gomedh / honey yellow
    "Ketu": "#8D8F94",  # smokey grey
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    letter-spacing: 0.02em;
    color: #1F2A37 !important;
}

hr {
    border-color: rgba(90, 114, 144, 0.3) !important;
}

/* Bright sky-with-clouds background: a blue-to-white gradient sky with
   layered soft radial-gradient cloud puffs (grey-blue shadow undersides
   first, then dense white cumulus texture bottom-heavy like looking down
   from above, thinning to wispy cirrus near the top). Pure CSS gradients
   (no tiled image), so it fills any viewport with no seams. */
.stApp {
    background:
        radial-gradient(ellipse 320px 180px at 10% 92%, rgba(140,165,195,0.40), transparent 70%),
        radial-gradient(ellipse 360px 190px at 30% 96%, rgba(140,165,195,0.38), transparent 70%),
        radial-gradient(ellipse 340px 185px at 52% 90%, rgba(140,165,195,0.35), transparent 70%),
        radial-gradient(ellipse 380px 195px at 72% 95%, rgba(140,165,195,0.40), transparent 70%),
        radial-gradient(ellipse 300px 175px at 90% 88%, rgba(140,165,195,0.35), transparent 70%),
        radial-gradient(ellipse 260px 150px at 20% 78%, rgba(140,165,195,0.28), transparent 70%),
        radial-gradient(ellipse 280px 155px at 60% 80%, rgba(140,165,195,0.30), transparent 70%),
        radial-gradient(ellipse 240px 140px at 85% 72%, rgba(140,165,195,0.25), transparent 70%),
        radial-gradient(ellipse 138px 86px at 21% 89%, rgba(255,255,255,0.94), transparent 58%),
        radial-gradient(ellipse 92px 57px at 64% 76%, rgba(255,255,255,0.98), transparent 58%),
        radial-gradient(ellipse 219px 136px at 24% 81%, rgba(255,255,255,0.92), transparent 58%),
        radial-gradient(ellipse 173px 107px at 87% 87%, rgba(255,255,255,0.87), transparent 58%),
        radial-gradient(ellipse 158px 98px at 65% 98%, rgba(255,255,255,0.96), transparent 58%),
        radial-gradient(ellipse 189px 117px at 69% 76%, rgba(255,255,255,0.94), transparent 58%),
        radial-gradient(ellipse 203px 126px at 28% 75%, rgba(255,255,255,0.92), transparent 58%),
        radial-gradient(ellipse 183px 113px at 74% 99%, rgba(255,255,255,0.99), transparent 58%),
        radial-gradient(ellipse 148px 92px at 38% 96%, rgba(255,255,255,0.99), transparent 58%),
        radial-gradient(ellipse 108px 67px at 92% 77%, rgba(255,255,255,0.88), transparent 58%),
        radial-gradient(ellipse 171px 106px at 101% 86%, rgba(255,255,255,0.90), transparent 58%),
        radial-gradient(ellipse 136px 84px at 51% 85%, rgba(255,255,255,0.94), transparent 58%),
        radial-gradient(ellipse 179px 111px at 59% 99%, rgba(255,255,255,0.99), transparent 58%),
        radial-gradient(ellipse 177px 110px at 89% 102%, rgba(255,255,255,0.87), transparent 58%),
        radial-gradient(ellipse 208px 129px at 90% 101%, rgba(255,255,255,0.94), transparent 58%),
        radial-gradient(ellipse 198px 123px at 74% 80%, rgba(255,255,255,0.94), transparent 58%),
        radial-gradient(ellipse 201px 125px at 26% 76%, rgba(255,255,255,1.00), transparent 58%),
        radial-gradient(ellipse 143px 89px at 5% 96%, rgba(255,255,255,0.87), transparent 58%),
        radial-gradient(ellipse 203px 126px at 27% 96%, rgba(255,255,255,0.86), transparent 58%),
        radial-gradient(ellipse 183px 114px at 63% 75%, rgba(255,255,255,0.90), transparent 58%),
        radial-gradient(ellipse 156px 97px at 92% 101%, rgba(255,255,255,1.00), transparent 58%),
        radial-gradient(ellipse 168px 104px at 29% 76%, rgba(255,255,255,0.85), transparent 58%),
        radial-gradient(ellipse 169px 105px at 17% 85%, rgba(255,255,255,0.87), transparent 58%),
        radial-gradient(ellipse 131px 81px at -0% 98%, rgba(255,255,255,0.99), transparent 58%),
        radial-gradient(ellipse 150px 93px at 94% 85%, rgba(255,255,255,0.93), transparent 58%),
        radial-gradient(ellipse 163px 101px at 66% 91%, rgba(255,255,255,0.94), transparent 58%),
        radial-gradient(ellipse 175px 101px at 94% 61%, rgba(255,255,255,0.77), transparent 58%),
        radial-gradient(ellipse 257px 149px at 24% 54%, rgba(255,255,255,0.71), transparent 58%),
        radial-gradient(ellipse 172px 100px at 55% 45%, rgba(255,255,255,0.72), transparent 58%),
        radial-gradient(ellipse 205px 119px at 2% 64%, rgba(255,255,255,0.57), transparent 58%),
        radial-gradient(ellipse 212px 123px at 63% 59%, rgba(255,255,255,0.66), transparent 58%),
        radial-gradient(ellipse 113px 66px at 71% 68%, rgba(255,255,255,0.57), transparent 58%),
        radial-gradient(ellipse 148px 86px at 68% 75%, rgba(255,255,255,0.69), transparent 58%),
        radial-gradient(ellipse 165px 95px at 59% 55%, rgba(255,255,255,0.64), transparent 58%),
        radial-gradient(ellipse 155px 90px at 37% 63%, rgba(255,255,255,0.66), transparent 58%),
        radial-gradient(ellipse 195px 113px at 77% 46%, rgba(255,255,255,0.77), transparent 58%),
        radial-gradient(ellipse 231px 134px at 31% 52%, rgba(255,255,255,0.62), transparent 58%),
        radial-gradient(ellipse 215px 125px at 19% 58%, rgba(255,255,255,0.58), transparent 58%),
        radial-gradient(ellipse 292px 102px at 32% 17%, rgba(255,255,255,0.29), transparent 58%),
        radial-gradient(ellipse 207px 73px at 86% 11%, rgba(255,255,255,0.33), transparent 58%),
        radial-gradient(ellipse 188px 66px at 88% 21%, rgba(255,255,255,0.22), transparent 58%),
        radial-gradient(ellipse 287px 101px at 53% 12%, rgba(255,255,255,0.37), transparent 58%),
        radial-gradient(ellipse 287px 101px at 18% 15%, rgba(255,255,255,0.33), transparent 58%),
        radial-gradient(ellipse 172px 60px at 81% 17%, rgba(255,255,255,0.26), transparent 58%),
        linear-gradient(180deg, transparent 0%, transparent 55%, rgba(255,255,255,0.55) 80%, rgba(255,255,255,0.92) 100%),
        linear-gradient(180deg, #4A85C0 0%, #6FA3D8 20%, #9AC3E8 38%, #C3DEF2 56%, #E4F1FB 75%, #F5FAFE 100%)
        !important;
    background-attachment: fixed !important;
}


/* Phthalo green sidebar with ivory labels and a soft mint selection. */
[data-testid="stSidebar"] {
    background: linear-gradient(165deg, #164D40 0%, #123524 100%);
    color: #F2F7EF;
    border-right: 1px solid rgba(194, 224, 203, 0.22);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F2F7EF !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: rgba(255, 255, 255, 0.06);
    color: #F2F7EF;
    border: 1px solid rgba(194, 224, 203, 0.25);
    border-radius: 12px;
    justify-content: flex-start;
    padding: 0.65rem 0.9rem;
    transition: background 150ms ease, border-color 150ms ease;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #28604C;
    border-color: #A8CDB5;
    color: #FFFFFF;
}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
    background: #D5E8D7;
    color: #123524;
    border-color: #D5E8D7;
    font-weight: 600;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:focus-visible {
    outline: 2px solid #E6CE8F;
    outline-offset: 3px;
}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {
    color: #F2F7EF;
}

.vt-card {
    background: rgba(255, 255, 255, 0.62);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.85);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 4px 24px rgba(70, 110, 150, 0.15);
}
.vt-card-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #5A7290;
    margin-bottom: 0.35rem;
}
.vt-card-value {
    font-size: 1.3rem;
    font-weight: 600;
    color: #1F2A37;
    white-space: normal;
    word-break: break-word;
    line-height: 1.3;
}

.vt-badge {
    display: inline-block;
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 0.6rem;
}
.vt-badge-active {
    background: rgba(34, 150, 90, 0.14);
    color: #1F7A4D;
    border: 1px solid rgba(34, 150, 90, 0.4);
}
.vt-badge-upcoming {
    background: rgba(184, 134, 11, 0.14);
    color: #8A6415;
    border: 1px solid rgba(184, 134, 11, 0.4);
}
.vt-badge-neutral {
    background: rgba(90, 114, 144, 0.12);
    color: #4B5768;
    border: 1px solid rgba(90, 114, 144, 0.3);
}

.vt-footer {
    text-align: center;
    font-size: 0.82rem;
    color: #5A7290;
    padding: 0.5rem 0 1.5rem;
}
</style>
"""


def inject_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def badge(text: str, kind: str = "neutral") -> str:
    """kind: 'active' | 'upcoming' | 'neutral'"""
    return f'<span class="vt-badge vt-badge-{kind}">{text}</span>'


def card(label: str, value: str, badge_html: str = "") -> None:
    st.markdown(
        f"""
        <div class="vt-card">
            <div class="vt-card-label">{label}</div>
            <div class="vt-card-value">{value}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
