# Relationship product removal — local review

## Dependency classification

A. Deleted UI/application modules: relationship_ui.py, relationship_v2_ui.py, relationship_consumer.py, relationship_presentation.py. These powered only the two removed views. Their four dedicated UI/presentation test files were also removed.

B. All vedic_astro files are byte-for-byte unchanged from HEAD. relationships.py remains because it contains reusable graha drishti, contacts, sign lordships, arudha/UL and Darakaraka functions used by frozen v2. relationship_records.py retains timezone ambiguity handling and reusable profile/date plumbing. D1, divisional, ephemeris, timing, transits and other core calculations remain intact.

C. The entire frozen v2 package, legacy analysis/endings code, synastry, record utilities, calculation regression fixtures/tests, and methodology documents remain dormant. No application import path reaches relationship analysis. No Streamlit pages directory or replacement feature was added.

## Modified files

- app.py: removed only two relationship imports and two navigation entries. Existing invalid-selection fallback returns old sessions to D1.
- README.md: replaced obsolete relationship navigation instructions with an archival-code note.
- tests/test_relationship_moon.py: removed only the deleted consumer import and its UI-copy assertion; calculation coverage remains.
- tests/test_relationship_endings.py: removed only the deleted UI-helper import and the retired-page render test; calculation coverage remains.
- tests/fixtures/relationship_v1_1_lock.json: removed only the three deleted legacy UI/presentation paths. All calculation hashes are unchanged. This is the legacy v1.1 test manifest, not v2 freeze metadata.

## Deleted files

- relationship_ui.py
- relationship_v2_ui.py
- relationship_consumer.py
- relationship_presentation.py
- tests/test_relationship_ui.py
- tests/test_relationship_v2_ui.py
- tests/test_relationship_consumer.py
- tests/test_relationship_presentation.py

## Added files

- tests/test_core_navigation.py: 11 core-page render checks, two retired-session fallback checks, and recursive application import check. Relationship analysis calls are forbidden during page smoke tests.
- docs/relationship-ui-removal.md: this report.

## Verification

- Full remaining suite: 375 passed in 4.69 seconds; one existing environment urllib3/LibreSSL warning.
- D1, D2, D4, D9, D10, Live Transits, Past Transits, Sade Sati, Guru Gochar, Current Dasha, and Sun & Venus Mahadasha render without application exceptions or errors, preserving the natal chart.
- Navigation contains exactly those 11 pages. Neither retired relationship page is reachable, including via a stale selected_chart_view session value.
- All frozen v2 manifest files verified, and independently recomputed implementation SHA-256 is unchanged: 1ce3aeac2041a8b9ec58e9e9ef2c2753075b5b17a49345d1ab3497a543c307b4
- No commit, push, replacement dating feature, or private-report deletion. Deployed Streamlit is unchanged until a later approved push.

## Preserved calculation files (unchanged)

- vedic_astro/chart.py
- vedic_astro/constants.py
- vedic_astro/dasha.py
- vedic_astro/divisional.py
- vedic_astro/ephemeris.py
- vedic_astro/horoscope.py
- vedic_astro/location.py
- vedic_astro/navamsa.py
- vedic_astro/relationship_endings.py
- vedic_astro/relationship_records.py
- vedic_astro/relationship_v2/__init__.py
- vedic_astro/relationship_v2/assessment.py
- vedic_astro/relationship_v2/climate.py
- vedic_astro/relationship_v2/debug.py
- vedic_astro/relationship_v2/engine.py
- vedic_astro/relationship_v2/evidence.py
- vedic_astro/relationship_v2/freeze.json
- vedic_astro/relationship_v2/geometry.py
- vedic_astro/relationship_v2/natal.py
- vedic_astro/relationship_v2/periods.py
- vedic_astro/relationship_v2/provenance.py
- vedic_astro/relationship_v2/spec.py
- vedic_astro/relationship_v2/transits.py
- vedic_astro/relationship_v2/windows.py
- vedic_astro/relationships.py
- vedic_astro/synastry.py
- vedic_astro/timing.py
- vedic_astro/transits.py
- vedic_astro/util.py
