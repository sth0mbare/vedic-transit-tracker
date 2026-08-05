"""Shared CSS and small HTML components for a consistent look across pages.

Kept separate from app.py so the visual layer doesn't tangle with the
calculator logic -- this only ever emits markup/CSS, never computes
anything astrological.
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    letter-spacing: 0.02em;
}

hr {
    border-color: rgba(217, 180, 90, 0.25) !important;
}

.vt-card {
    background: linear-gradient(160deg, #171B36 0%, #12152A 100%);
    border: 1px solid rgba(217, 180, 90, 0.25);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.9rem;
}
.vt-card-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #A9A6C4;
    margin-bottom: 0.35rem;
}
.vt-card-value {
    font-size: 1.3rem;
    font-weight: 600;
    color: #F2EFE9;
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
    background: rgba(110, 231, 168, 0.14);
    color: #6EE7A8;
    border: 1px solid rgba(110, 231, 168, 0.4);
}
.vt-badge-upcoming {
    background: rgba(217, 180, 90, 0.14);
    color: #D9B45A;
    border: 1px solid rgba(217, 180, 90, 0.35);
}
.vt-badge-neutral {
    background: rgba(255, 255, 255, 0.06);
    color: #A9A6C4;
    border: 1px solid rgba(255, 255, 255, 0.12);
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
