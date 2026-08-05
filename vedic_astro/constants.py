"""Static reference data for Vedic (sidereal) astrology calculations."""

import swisseph as swe

# --- Grahas (planets used in Vedic astrology) ---
# Ketu has no swisseph body id; it's derived as Rahu + 180 deg.
SUN = "Sun"
MOON = "Moon"
MARS = "Mars"
MERCURY = "Mercury"
JUPITER = "Jupiter"
VENUS = "Venus"
SATURN = "Saturn"
RAHU = "Rahu"
KETU = "Ketu"

# Maps our graha names to swisseph body ids for the ones swisseph computes directly.
SWE_BODY = {
    SUN: swe.SUN,
    MOON: swe.MOON,
    MARS: swe.MARS,
    MERCURY: swe.MERCURY,
    JUPITER: swe.JUPITER,
    VENUS: swe.VENUS,
    SATURN: swe.SATURN,
    RAHU: swe.MEAN_NODE,  # mean node is standard for Vedic dasha/gochara calcs
}

GRAHAS = [SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU]

# --- Rashis (zodiac signs), sidereal, 30 deg each starting at 0 Aries ---
RASHIS = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
]
RASHI_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# --- Nakshatras: 27 lunar mansions, 13d20m each, starting at 0 Aries ---
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Nakshatra lord cycle repeats every 9 nakshatras, in this fixed order.
DASHA_LORD_CYCLE = [KETU, VENUS, SUN, MOON, MARS, RAHU, JUPITER, SATURN, MERCURY]

NAKSHATRA_LORDS = [DASHA_LORD_CYCLE[i % 9] for i in range(27)]

# --- Vimshottari Dasha periods, in years, total = 120 ---
DASHA_YEARS = {
    KETU: 7,
    VENUS: 20,
    SUN: 6,
    MOON: 10,
    MARS: 7,
    RAHU: 18,
    JUPITER: 16,
    SATURN: 19,
    MERCURY: 17,
}
DASHA_TOTAL_YEARS = sum(DASHA_YEARS.values())  # 120

# --- Ayanamsa options exposed to the user ---
AYANAMSAS = {
    "Lahiri": swe.SIDM_LAHIRI,
    "Raman": swe.SIDM_RAMAN,
    "Krishnamurti (KP)": swe.SIDM_KRISHNAMURTI,
}
DEFAULT_AYANAMSA = "Lahiri"

AYANAMSA_OVERVIEW_BLURB = (
    "The ayanamsa is the angular gap between the sidereal zodiac (fixed to the "
    "actual stars, used in Vedic astrology) and the tropical zodiac (fixed to "
    "the seasons, used in Western astrology). Different schools measure that "
    "gap slightly differently, which shifts every planet's sign by a degree "
    "or two depending which one you pick."
)

AYANAMSA_DESCRIPTIONS = {
    "Lahiri": (
        "The official ayanamsa adopted by the Indian government's Calendar "
        "Reform Committee in 1955 -- the de facto standard used by most "
        "Vedic astrologers today, and the default here."
    ),
    "Raman": (
        "Devised by astrologer B.V. Raman using a different reference star "
        "point than Lahiri -- a few tenths of a degree apart from it, "
        "favored in some traditional Indian astrology lineages."
    ),
    "Krishnamurti (KP)": (
        "Developed by K.S. Krishnamurti for his Krishnamurti Paddhati (KP) "
        "system of astrology, which relies on finer sub-divisions of each "
        "sign for its predictive technique."
    ),
}

DEG_PER_RASHI = 30.0
DEG_PER_NAKSHATRA = 360.0 / 27.0  # 13 deg 20 min
DEG_PER_PADA = DEG_PER_NAKSHATRA / 4.0  # 3 deg 20 min
