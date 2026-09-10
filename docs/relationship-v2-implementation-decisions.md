# v2 implementation decisions — declared before implementation tests

Scope: new independent prospective engine only. No historical templates, similarity,
weights, outcome-selected thresholds, personal charts, historical evaluations, or scans.
Existing v1.1 and UI files stay unchanged. The approved fifteen-section design is the
methodological basis. This file resolves operational details without event evaluation.

## Reuse and conflicts

- Reuse `relationships.indicators` strictly for natal UL/DK/D9 metadata, not legacy
  scoring; `SIGN_LORDS`, `CLASSICAL`, `contact_rows` strictly for trusted geometry.
  Imports do not call the legacy `analyze` or `scan_windows` engines.
- Shared `contact_rows` returns unqualified whole-sign aspect strings. The v2 adapter
  maps those to `parashari_graha_drishti`; it never changes the shared helper.
- Jaimini rashi drishti is absent from the shared engine. Add the specified sign
  operator only in v2. No node drishti. No projected-transit D9.
- Reuse `transits.transit_houses`, ephemeris positions, `timing.dasha_at` and natal
  metadata. No second astronomy, Moon-house, Vimshottari, UL or DK implementation.
- Existing ingress search has coarse multi-day brackets and can miss sign excursions.
  v2 therefore isolates a boundary search around the shared positions. Use hourly
  brackets, split brackets at speed-sign changes/stations, and refine detected
  sign transitions to one second. Period boundaries are exact shared dasha endpoints.
  This is a bounded numerical search, not a proof against arbitrary sub-hour
  oscillations. Tests use fabricated position providers, not real future scans.

## Exact operational choices where prose was ambiguous

- Venus favorable/unblocked climate applies to BOTH alternatives in T-Venus-R.
- Positive UL/DK corroboration requires Jupiter and its clear favorable climate.
  Saturn UL/DK evidence remains neutral/pressure, usable for stress, not automatically
  a positive corroboration. This follows the actor table's stated polarities.
- D1 second-lord continuity connection means identity in N-P or one-step connection
  to an N-P planet. A one-step connection is sign conjunction, directed graha
  drishti from candidate to target, or exchange with that target planet. No chains.
- R/P/Difficulty natal sets are exactly the approved definitions. N-D's raw set is
  Saturn/Mars/Ketu plus D1 6/8/12 lords; the approved Stress-period gate supplies the
  required partnership connection. Occupancy of a difficult natal house is not added.
- D9 AD and PD corroboration qualify; MD corroboration is background only.
- Stress reinforcement requires a node occupancy or Mars sign trigger to a partnership
  or continuity target AND a different actor from its Saturn structural witness.
  Mars on a fifth-lord-only target is not sufficient for stress reinforcement.
- Stress has independent `reinforced` and `trigger_active` flags. Primary state is
  `stress trigger active` when a Moon/Venus/Mars stress trigger is inside the stress
  architecture; otherwise reinforced, active, or absent. No certainty of separation.
- Sun triggers are contextual only; never promote any gate. Mercury contextual only.
- All geometry is canonical by reference, actor, target physical sign/longitude,
  operator, and timestamp. Role aliases merge; dependency groups also merge multiple
  operators on the same actor/target. Nodes share one actor group. Diagnostic degree
  contacts never appear in structural, corroborative or trigger witness sets.
- Each category enumerates valid gate-witness combinations. Two-actor gates count
  only actual qualifying dasha/structural witnesses, not irrelevant extra evidence,
  diagnostic contacts, fast triggers, or merely another D9 description.
- Evidence stores category-specific use/exclusion reasons, because one atom can be
  contextual for one category and used by another. Canonical aliases are recorded as
  redundant descriptions rather than duplicate point-bearing atoms.
- No new probabilistic/Low/High/global score exists. Positive and stress outputs
  coexist. Generic climate has favorable, obstructed, other statuses; mixed is used
  for personalized activation with non-clear climate, not invented as a new planet
  occupancy class.
- Birth-time uncertainty is supplied as metadata; unknown precision generates a
  warning. D9/D1-sensitive outputs are provisional, not automatically discarded or
  claimed robust. Finite complete nine-graha input is required; exact DK ties retained.
- Window segments are maximal continuous category states, with no minimum duration,
  gap fill or top-N truncation. Broad periods use dasha gates only. Triggers are
  emitted inside qualified architecture. No automatically executed scanner/UI change.

## Freeze/independence

Freeze a new `relationship_timing_v2_0` manifest with methodology, classifications,
parameters, implementation files and read-only shared dependency hashes. Existing
uncommitted v1.1 files are not committed, overwritten or relabeled. Synthetic cases
are selected to exercise logical predicates, not to reproduce known relationships.
Existing tests that evaluate prohibited calendar examples are not run in this phase;
new v1.1 regression tests use fully fabricated positions and periods instead.
