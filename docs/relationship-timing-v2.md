# relationship_timing_v2_0 — independent prospective engine

Status: implementation for review, synthetic methodology tests only. No personal
historical validation or astronomical future scan has been run. v1.1 remains an
unchanged separate experiment. Prior author exposure to personal results is not
claimed to be fully blinded; implementation uses only the approved design and
explicit engineering decisions, with no historical/outcome/template inputs.

## API and conceptual layers

`vedic_astro.relationship_v2.analyze_v2(chart, at)` is a read-only snapshot. It accepts
a normal NatalChart and timezone-aware instant, with optional birth-time precision.
It does not accept event labels, partner identities, outcomes, templates, similarity
metrics, training records, or fitted weights. No combined score or probability.

- `natal.py`: normal shared UL/DK/D9 metadata and D1 natal role interpretation.
- `periods.py`: consumes normal MD/AD/PD, applies the exact approved Boolean gates.
- `climate.py`: shared Moon houses, planet-specific favorable houses and Vedha.
- `geometry.py`: adapter for shared Parashari graha drishti; separate Jaimini operator.
- `transits.py`: personalized Jupiter/Saturn, restricted UL/DK, nodes, fast triggers,
  and diagnostic-only natal degree contacts.
- `evidence.py`: canonical physical atoms, redundant aliases and actor dependencies.
- `assessment.py`: four independent assessments with passed/failed gates and witnesses.
- `windows.py`: opt-in numerical boundary discovery, exact dasha endpoints and maximal
  continuous state intervals; no minimum duration, gap fill, ranking or automatic scan.
- `debug.py`: opt-in JSON snapshot CLI; no current UI/cards modified.
- `provenance.py`: freeze hash/integrity status in each result.

## Exact role definitions

N-P: D1 seventh lord, occupants, and directed full graha drishti onto seventh.
N-R: Venus plus D1 fifth lord, occupants and directed full aspects onto fifth.
P-support: Venus, DK, UL lord, or one-step natal connection to D1 seventh lord.
One-step: sign conjunction, aspect from candidate to target, or mutual sign exchange.
No recursive dispositors. Jupiter is not granted unconditional natural P-support.
Difficulty: Saturn/Mars/Ketu and normal D1 sixth/eighth/twelfth lords, with the period
gates below supplying the required partnership connection.

D9 eligibility: D9 seventh lord/occupants/full-aspecting planets, or shares the natal
D9 Venus/seventh-lord sign. AD/PD qualify; MD is background. No transit D9 projection.
Continuity: AD/PD is UL lord, second-from-UL lord, or D1 second lord connected to N-P.

## Exact category gates (engineering hypotheses)

Romance-period = AD in N-R AND (MD in N-R OR PD in N-R).
Partnership-period = AD in N-P OR (AD in P-support AND (MD in N-P OR PD in N-P)).
Stress-period = (AD in N-P AND Difficulty) OR (AD in Difficulty AND (MD or PD in N-P))
OR (AD in N-P AND PD in Difficulty).

- Romance elevated: romance-period AND Moon or Venus-R trigger. Otherwise short-term
  trigger only when a romance trigger exists; otherwise inactive.
- Partner entry: partnership-period AND qualified Jupiter natal-target transit AND
  (D9 corroboration OR positive UL/DK corroboration) AND two actual period/structural
  actors. Triggered state additionally requires Moon/Venus-P trigger.
- Commitment: partnership-period AND qualified Jupiter AND D9 corroboration AND
  continuity AND two actual period/structural actors. Moon/Venus-P refines timing.
- Stress: stress-period AND Saturn natal partnership/UL/DK structure AND two actual
  period/structural actors. Nodes or Mars can reinforce; Moon/Venus/Mars can refine
  timing inside that structure. The result never asserts definitive separation.

Two-actor counting uses only the selected period and structural gate witnesses, not
fast triggers or an extra D9 description. All valid witness alternatives are examined;
minimal deterministic valid witness set is reported. Nodes form one source group.
Repeated period lords, multiple targets and overlapping role names are not extra actors.

## Climate, structure, operators and references

Climate favorable houses/Vedha pairs are versioned in `spec.py`: seven-classical
blockers, Sun/Saturn and Moon/Mercury exceptions. Nodes cannot block core Vedha or
receive generic favorable relationship credit. Favorable, favorable-but-obstructed,
and other/non-favorable remain distinct. A personalized Jupiter contact with non-clear
climate is explicitly mixed; it is not qualified positive structural support.

G-J/G-S: conjunction by sign or Parashari full aspect onto natal D1 seventh sign,
seventh-lord sign, or Venus sign. Jupiter additionally requires favorable/unblocked
Moon-house climate. Saturn activates/pressures; it is not automatically benefic.
G-N: nodal occupancy of those targets, UL or DK is secondary/reinforcing only.

UL/DK uses the explicit Jaimini sign operator: movable to fixed excluding adjacent;
fixed to movable excluding adjacent; dual to other dual. Jupiter/Saturn may occupy
or aspect UL, second from UL, DK. Positive UL/DK requires clear Jupiter climate.
Saturn is stress/activation. Nodes occupancy only; no node aspect. Moon/Venus occupy
UL/DK as timing refinements, Mars additionally second-from-UL for stress. Sun/Mercury
remain context. These restrictions do not change legacy v1.1 eligibility.

Moon trigger: seventh from natal Moon or sign conjunction with natal seventh lord,
Venus, UL or DK. Venus-R: clear climate AND (Moon house 1/5/11 OR sign conjunction
with natal fifth lord/Venus). Venus-P: clear climate AND sign conjunction with natal
seventh lord/UL/DK. Mars is a mixed timing marker at fifth/seventh lord, Venus, UL/DK;
fifth-only contacts cannot reinforce stress. Sun is supplementary only when an
eligible active AD/PD lord occupies a relevant natal target sign. Mercury context only.
Degree conjunction/opposition within 3° is diagnostic-only and never bypasses a gate.

Natal lordships and D1/D9 remain normal. Transit-house climate is explicitly from
Moon / Chandra Lagna. Lagna occupancy is returned as a separately named secondary
field and is not recruited into gochara gates. Parashari, Jaimini, conjunction, exchange,
and degree-diagnostic operators are explicitly named, never a generic unlabeled aspect.

## Auditability and source classifications

Every evidence atom retains actor, physical target, reference(s), operator, timestamp/
interval, roles, layer(s), eligible categories, feature roles, dependency group, status,
reason, per-category use/exclusion and source classification. Canonical aliases are
recorded separately as redundant. Used/excluded IDs, all candidate proofs and exact
missing gates accompany each assessment. Data uncertainty is a warning, not a hidden
score change. All snapshots include method parameters and freeze-integrity metadata.

Traditional ingredients: natal seventh-house roles, Vimshottari, Moon-based gochara,
classical favorable-house and Vedha tables, Parashari aspects. Interpretive choices:
romance/fifth-house translation, natal D9 aspects, Jaimini UL/DK transit applications,
node exclusions, gender-neutral significators. Engineering: all Boolean combinations,
actor restrictions/minimum, 3° diagnostics, trigger restrictions, dependency handling
and numerical precision. None are claimed empirically calibrated.

Source registry (exact URLs and classifications also frozen in spec.py):
- Phaladeepika chapter 10: https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621582.html
- Phaladeepika chapter 26: https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621598.html
- Jaimini Sutras I.4: https://lakshminarayanlenasia.com/articles/JAIMINISUTRAS.pdf

## Parameters and limitations

Version: relationship_timing_v2_0. Ayanamsa inherited from input chart (not silently
reset); normal shared mean-node calculation. Degree orb fixed 3°, diagnostic only.
Two distinct qualifying actors for entry/commitment/stress. Seven-classical Vedha
blockers and stated exceptions. No node aspects, projected transit D9, fitted weights,
probability calibration, minimum duration, gap fill or arbitrary strongest-window cutoff.
Numerical sign boundaries: hourly brackets split at detected stations, refined to one
second; shared dasha endpoints remain exact. Near-station sub-hour oscillations outside
this bounded scheme are a documented limitation, not claimed mathematically exhaustive.
Window metadata retains every constituent segment/dasha and trigger interval.

Birth-time precision is metadata: omitted/uncertain precision makes sensitive results
provisional. No rectification, dignity scoring, combustion gate, Ashtakavarga or
unspecified cancellation has been added. The design did not specify these algorithms.
All implementation resolutions are in relationship-v2-implementation-decisions.md.

## Review and validation boundary

Freeze hashes identify new source, methodology and read-only shared dependencies.
A changed dependency produces a source-mismatch status, not a silent relabeling.
Existing uncommitted v1.1 remains untouched. No application commit is implied by the
base Git revision; the implementation source digest identifies this uncommitted build.
Only fabricated charts, positions and periods are used in methodology tests, including
fabricated window motion. Personal/historical evaluation and real future scans remain
outside this implementation phase. Outcome data may be used only after this freeze,
with a separately approved validation plan. The current user-facing UI is unchanged.
