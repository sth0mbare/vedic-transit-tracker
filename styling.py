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

/* Starfield + nebula background: hand-drawn constellation lines on top,
   a few tiled star-dot layers for scattered stars, plus large soft
   blurred blobs for nebula-cloud color. */
.stApp {
    background-color: #05050d !important;
    background-image:
        url("data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%22900%22%20height%3D%22900%22%3E%0A%3Cg%20stroke%3D%22rgba%28230%2C225%2C255%2C0.4%29%22%20stroke-width%3D%221%22%20fill%3D%22rgba%28255%2C255%2C255%2C0.9%29%22%3E%0A%3Cline%20x1%3D%2260%22%20y1%3D%2280%22%20x2%3D%22120%22%20y2%3D%2260%22/%3E%0A%3Cline%20x1%3D%22120%22%20y1%3D%2260%22%20x2%3D%22180%22%20y2%3D%2290%22/%3E%0A%3Cline%20x1%3D%22180%22%20y1%3D%2290%22%20x2%3D%22230%22%20y2%3D%2270%22/%3E%0A%3Cline%20x1%3D%22230%22%20y1%3D%2270%22%20x2%3D%22210%22%20y2%3D%22130%22/%3E%0A%3Ccircle%20cx%3D%2260%22%20cy%3D%2280%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22120%22%20cy%3D%2260%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22180%22%20cy%3D%2290%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22230%22%20cy%3D%2270%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22210%22%20cy%3D%22130%22%20r%3D%222%22/%3E%0A%3Cline%20x1%3D%22520%22%20y1%3D%22210%22%20x2%3D%22580%22%20y2%3D%22270%22/%3E%0A%3Cline%20x1%3D%22580%22%20y1%3D%22270%22%20x2%3D%22500%22%20y2%3D%22310%22/%3E%0A%3Cline%20x1%3D%22500%22%20y1%3D%22310%22%20x2%3D%22520%22%20y2%3D%22210%22/%3E%0A%3Ccircle%20cx%3D%22520%22%20cy%3D%22210%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22580%22%20cy%3D%22270%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22500%22%20cy%3D%22310%22%20r%3D%222%22/%3E%0A%3Cline%20x1%3D%22650%22%20y1%3D%22520%22%20x2%3D%22690%22%20y2%3D%22560%22/%3E%0A%3Cline%20x1%3D%22690%22%20y1%3D%22560%22%20x2%3D%22720%22%20y2%3D%22520%22/%3E%0A%3Cline%20x1%3D%22720%22%20y1%3D%22520%22%20x2%3D%22760%22%20y2%3D%22560%22/%3E%0A%3Cline%20x1%3D%22760%22%20y1%3D%22560%22%20x2%3D%22800%22%20y2%3D%22530%22/%3E%0A%3Ccircle%20cx%3D%22650%22%20cy%3D%22520%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22690%22%20cy%3D%22560%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22720%22%20cy%3D%22520%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22760%22%20cy%3D%22560%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22800%22%20cy%3D%22530%22%20r%3D%222%22/%3E%0A%3Cline%20x1%3D%22100%22%20y1%3D%22680%22%20x2%3D%22160%22%20y2%3D%22730%22/%3E%0A%3Cline%20x1%3D%22160%22%20y1%3D%22730%22%20x2%3D%22140%22%20y2%3D%22790%22/%3E%0A%3Cline%20x1%3D%22140%22%20y1%3D%22790%22%20x2%3D%2280%22%20y2%3D%22810%22/%3E%0A%3Ccircle%20cx%3D%22100%22%20cy%3D%22680%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22160%22%20cy%3D%22730%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22140%22%20cy%3D%22790%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%2280%22%20cy%3D%22810%22%20r%3D%222%22/%3E%0A%3Cline%20x1%3D%22820%22%20y1%3D%22720%22%20x2%3D%22860%22%20y2%3D%22770%22/%3E%0A%3Cline%20x1%3D%22860%22%20y1%3D%22770%22%20x2%3D%22810%22%20y2%3D%22800%22/%3E%0A%3Ccircle%20cx%3D%22820%22%20cy%3D%22720%22%20r%3D%222%22/%3E%0A%3Ccircle%20cx%3D%22860%22%20cy%3D%22770%22%20r%3D%222.6%22/%3E%0A%3Ccircle%20cx%3D%22810%22%20cy%3D%22800%22%20r%3D%222%22/%3E%0A%3C/g%3E%0A%3C/svg%3E"),
        radial-gradient(1px 1px at 20px 30px, rgba(255, 255, 255, 0.85), transparent),
        radial-gradient(1px 1px at 90px 120px, rgba(255, 255, 255, 0.6), transparent),
        radial-gradient(1.5px 1.5px at 160px 60px, rgba(255, 255, 255, 0.75), transparent),
        radial-gradient(1px 1px at 210px 180px, rgba(255, 255, 255, 0.5), transparent),
        radial-gradient(2px 2px at 260px 40px, rgba(255, 255, 255, 0.85), transparent),
        radial-gradient(1px 1px at 310px 220px, rgba(255, 255, 255, 0.45), transparent),
        radial-gradient(1px 1px at 50px 260px, rgba(255, 255, 255, 0.55), transparent),
        radial-gradient(ellipse 900px 550px at 15% 15%, rgba(160, 120, 170, 0.32), transparent 65%),
        radial-gradient(ellipse 750px 650px at 85% 55%, rgba(200, 140, 100, 0.26), transparent 65%),
        radial-gradient(ellipse 650px 550px at 45% 95%, rgba(100, 110, 175, 0.28), transparent 65%) !important;
    background-repeat: repeat, repeat, repeat, repeat, repeat, repeat, repeat, repeat, no-repeat, no-repeat, no-repeat !important;
    background-size: 900px 900px, 350px 350px, 350px 350px, 350px 350px, 350px 350px, 350px 350px, 350px 350px, 350px 350px, auto, auto, auto !important;
    background-attachment: fixed !important;
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
