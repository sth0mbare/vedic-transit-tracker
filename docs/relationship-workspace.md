# Relationship Timing & Retrospective

Open **Relationships** in the sidebar after computing your birth chart.

## Sections

- **Date snapshot:** choose a historical or future date, local time and IANA timezone. Shows MD/AD/PD, all nine sidereal planetary longitudes, degrees within sign, whole-sign houses from natal D1 Lagna, degree contacts, whole-sign aspects, and relationship indicators.
- **MD / AD / PD hierarchy:** inspect the active periods on any supported date from birth onward, or browse every AD and PD in the first nine full mahadashas. Starts and ends include timezone offsets. Endpoints are exclusive. The first MD starts before birth when there is an elapsed balance.
- **Events:** add, edit, open or delete relationship events, with a person label, type, date, optional time and notes. Unknown event times use **local noon**, clearly labeled as provisional. These are not exact event snapshots and are not full-day analyses.
- **Compare events:** select at least two historical events. Each selected event gets its own column. Repeated signatures require two distinct event IDs with the same calculated rule, source, target and contact type; they include event IDs and evidence. This is descriptive comparison, not a causal model or significance test.
- **Future windows:** daily sampling at 12:00 UTC, for up to three years. Eligible families must meet stacking requirements, exceed the preceding 90-day median, and meet its nearest-rank 75th percentile. At least two consecutive qualifying samples form a window; isolated qualifying samples are listed separately. Boundary times are samples, not precise ingress times. No matching windows is a valid result.
- **Natal synastry:** profiles with reliable birth times get D1, D9, Moon/nakshatra, Lagna, seventh lord, Darakaraka, Upapada, directed natal contacts and reciprocal house overlays. Unknown-time profiles have provisional noon positions and hourly sign/nakshatra samples; no Lagna, house, D9 or Upapada calculation is performed. Hourly samples are not guaranteed bounds. Synastry is separate from event timing and does not assign a compatibility or outcome score.

Events and partner profiles are **session-only**. Export your backup before leaving or rebooting Streamlit. Restore validates the schema, IDs, dates, timezones and source birth-chart/ayanamsha identity. Backups contain personal data; the app does not place them in the repository or a shared server database. Restore replaces the current chart's session records. Different natal charts have separate workspaces.

## Calculation conventions

The workspace inherits the natal chart's selected ayanamsha (Lahiri by default), Swiss Ephemeris wrapper and mean nodes. It does not recalculate or mutate the existing session chart. Existing D1/D2/D4/D9/D10, dasha pages and transit APIs are unchanged.

- **Vimshottari:** exact stored sidereal birth Moon longitude determines nakshatra fraction and birth balance. New lookup treats exact nakshatra boundaries as the start of the new nakshatra, without rounding the input degrees. A year remains **365.2425 days**, matching the app. AD proportions use the existing routine; PD duration is AD duration multiplied by the PD lord's years / 120. Last child endpoints are fixed to their parent endpoint to avoid microsecond gaps. Timestamps are arithmetic under this convention, not claims of universal astronomical accuracy; other year conventions produce different dates.
- **Timezone:** the new forms validate local wall times against IANA timezone rules. Nonexistent DST times are rejected. Repeated times require selecting first or second occurrence. Original birth form behavior remains unchanged.
- **Darakaraka:** seven-planet system, lowest unrounded degree within sign among Sun through Saturn. Nodes excluded. Exact ties are shown together rather than silently resolved.
- **Upapada:** arudha of D1 house 12 using classical sign lords (Mars for Scorpio, Saturn for Aquarius). Count from house 12 to its lord, then the same inclusive count from the lord. If the result is first/seventh from house 12, move to the tenth from that result. UL is a sign, not an invented exact longitude.
- **Graha drishti:** full whole-sign seventh aspect for the seven classical planets; Mars additionally fourth/eighth, Jupiter fifth/ninth, Saturn third/tenth. No disputed node special aspects. Contacts to Rahu/Ketu are included.
- **Degree contacts:** conjunction and opposition within the displayed user-selected orb (default 3 degrees), distinct from sign-based drishti. This orb is an application convention, not a universal classical threshold.
- **D9 activation:** a transit's projected Navamsa sign sharing a natal D9 reference sign. This is explicitly divisional co-occupation, not a physical sky aspect. Dasha lords' natal D9 roles are also shown as context.

Traditional rule references: P.V.R. Narasimha Rao, [Vedic Astrology: An Integrated Approach](https://www.vedicastrologer.org/articles/vedic_astro_textbook.pdf), especially chapters on divisional charts, aspects, arudhas, chara karakas and Vimshottari. The seven-planet karaka convention is explicitly selected here; other lineages may use eight. The relationship scoring below is an application heuristic, not a rule attributed to that text.

## Scores are inspectable rule-family counts

All activations remain visible, including context-only ones. An eligible family contributes **one point**, regardless of how many contacts it contains:

| Family | Eligibility |
|---|---|
| Dasha | Active MD/AD/PD lord is the natal fifth/seventh lord or Venus/Jupiter |
| House | Jupiter/Saturn occupy natal fifth/seventh house |
| Slow planet | Jupiter/Saturn degree contact to fifth/seventh lord or Venus/Jupiter |
| Fast planet | Venus/Mars degree contact to those points |
| D9 | Jupiter/Saturn's projected D9 sign shares natal D9 seventh sign or seventh lord's sign |
| UL/DK | Jupiter/Saturn share UL sign, or a degree contact to Darakaraka |

Meeting/dating uses house5/house11/Venus/Mars targets. Formation adds house7/Jupiter/UL/Darakaraka. Commitment uses house7/Jupiter/UL/Darakaraka. D9 seventh-lord targets count as house7. House1/8 and Moon/nodes remain contextual unless the contacted planet also holds an eligible lordship or is Darakaraka.

A stacking flag requires at least three eligible families, a dasha family and a slow-planet contact family, plus a matching of **at least three distinct source planets to different families**. This prevents one planet being counted as the entire stack. It does not establish statistical independence. Future windows additionally need an above-baseline score and consecutive days. Each window exports all supporting signatures, dates, transit positions, active dashas, natal inputs and baseline daily counts. No probability, soulmate label, future-spouse identification or deterministic prediction is produced.

## Limits

- UI dates: 1800–2200 (partner birth dates cannot be in the future); personal dasha lookup starts at birth.
- Daily future sampling can miss short intraday changes, including PD boundaries. For exact moment inspection use Date snapshot.
- Unknown birth-time synastry is provisional, including Moon/nakshatra and degree contacts.
- Events are not linked to partner profiles automatically; labels and natal synastry are separate.
- The existing Sade Sati/Guru Gochar ayanamsha caveat is not changed by this feature.

## Architecture

`timing.py`: additive hierarchy and lookup.
`relationships.py`: indicators, contact rules, evidence, comparison and scanning.
`relationship_records.py`: event/profile schemas, timezone validation and backup validation.
`synastry.py`: natal comparison with explicit unknown-time handling.
`relationship_ui.py`: Streamlit workspace; `app.py` adds one sidebar entry.
