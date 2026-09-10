# Relationship Timing Rules v1.1 — Moon-based gochara occupancy

User-authorized reference correction only. All actor eligibility, category routing,
family weights, matching, flags, display bands and future-window thresholds remain
v1.0. Do not adjust against historical outcomes.

Only transit HOUSE OCCUPANCY uses house from Moon / Chandra Lagna. Positive
categories still admit only Jupiter/Saturn occupying 5/7. Ending occupancy still
admits Saturn/Ketu/Mars in 1/7, or 6/8/12 with a simultaneous natal Venus/seventh-lord
degree contact. Moon/Venus occupancy remains context. House from D1 Lagna remains
separate, non-scoring secondary evidence. Both explicit house fields are exported.
The legacy `natal_house` field remains an alias of `house_from_lagna` for external
compatibility; it is not consumed by occupancy scoring or displayed ambiguously.

`transits.transit_houses` contains the existing two house calculations, shared by
`compute_transits` and relationship snapshots. This avoids duplicate house formulas,
extra ephemeris calls and expensive future-ingress scans during relationship analysis.

Natal D1/Lagna, D9, UL, DK, lordships, degree contacts and Vimshottari calculations
are unchanged. A house5 target on a natal-contact or dasha record still means the
D1 fifth LORD role, not transit occupancy of fifth from Moon. Only occupancy
records use the new reference. Aspect distances remain planet-to-target distances.

## Darakaraka discrepancy: documentation correction only

The v1.0 descriptive text restricted DK contacts to Jupiter/Saturn, but executable
code accepted conjunction/opposition from any transit graha. The preexisting
relationship_legacy fixture explicitly includes an eligible Sun-to-DK contact.
Thus the frozen executable/regression contract supports preserving any-graha
eligibility in the original three categories; the prose is corrected to match.
This is evidence of the established behavior, not proof of the author's original
intent. Restricting sources would require a separately authorized scoring change.
Ending/separation retains its existing Saturn/Ketu/Mars DK restrictions and
contact-routing precedence. No behavior is changed for DK in this revision.

## Versioning

The v1.0 specification/manifest and historical score fixture remain archived.
The pre-change generic regression calculations preserve natal/contact/dasha evidence
for exact invariance checks. v1.1 has a new source manifest. Cached snapshots are
recomputed on version mismatch; old future scans require rerunning. Prior v1.0
reports are not silently relabeled. No personal birth/event data is added to tests.
