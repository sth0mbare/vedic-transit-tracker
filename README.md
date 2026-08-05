# Vedic Transit Tracker

A sidereal (Vedic/Jyotish) astrology web app: enter your birth details once
and see your natal chart, current Vimshottari dasha, Sade Sati status, and
live planetary transits (gochara) relative to your chart — all computed with
[Swiss Ephemeris](https://www.astro.com/swisseph/swephinfo_e.htm), not a
tropical/Western engine.

## Features

- **Natal chart**: Lagna (ascendant), planet sign/house placements, Moon's
  Rashi and Nakshatra, using selectable ayanamsa (Lahiri, Raman, or KP)
- **Vimshottari dasha**: current mahadasha and antardasha
- **Sade Sati tracker**: whether Saturn is currently transiting the 12th,
  1st, or 2nd house from your natal Moon, and roughly how much longer
- **Live transits**: current sidereal position of every graha, with house
  placement counted from both your natal Moon and natal Lagna, for any date
- Historically-correct timezone handling (birth time is converted to UTC
  using the actual offset in effect on that date, not today's offset)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Run tests

```bash
pip install pytest
pytest tests/
```

## Project layout

- `vedic_astro/` — core library, independent of the UI
  - `constants.py` — grahas, rashis, nakshatras, dasha periods, ayanamsas
  - `location.py` — geocoding + IANA timezone resolution
  - `ephemeris.py` — Swiss Ephemeris wrapper (sidereal planet positions)
  - `chart.py` — natal chart computation
  - `dasha.py` — Vimshottari mahadasha/antardasha
  - `transits.py` — gochara comparison + Sade Sati
  - `util.py` — sign/nakshatra/house math shared across modules
- `app.py` — Streamlit UI
- `tests/` — regression tests against a hand-verified reference chart

## Notes

- House placements use the whole-sign system (the traditional Vedic
  approach), not Placidus or other quadrant systems.
- Rahu is computed as the mean lunar node; Ketu is derived as Rahu + 180°.
- Dasha and Sade Sati durations use a 365.2425-day solar year approximation.
