# Relationship Timing v2 implementation report

## Outcome

Implemented an independent, opt-in `relationship_timing_v2_0` engine. No pre-existing files were modified during this implementation. Existing v1.1 working-tree changes remain intact. The Streamlit UI still uses its existing implementation; v2 has not been deployed, committed, or pushed.

## Files created

- `vedic_astro/relationship_v2/`: `__init__.py`, `spec.py`, `evidence.py`, `geometry.py`, `natal.py`, `periods.py`, `climate.py`, `transits.py`, `assessment.py`, `engine.py`, `windows.py`, `debug.py`, `provenance.py`, and `freeze.json`.
- `tests/test_relationship_v2.py`, `tests/test_relationship_v2_preservation.py`, `tests/test_relationship_v2_freeze.py`.
- `tests/fixtures/relationship_v1_1_synthetic_preservation.json`.
- `docs/relationship-timing-v2.md`, `docs/relationship-v2-implementation-decisions.md`, and this report.

## Architecture and reuse

The public `analyze_v2` entry point takes a natal chart and an explicit timezone-aware instant. Separate modules derive natal roles, dasha eligibility, Moon-based gochara climate, structural contacts, fast triggers, evidence, categorical assessments, and optional windows. The output includes passed and failed gates, missing requirements, contributing evidence, excluded evidence, and provenance.

The engine reuses the existing natal relationship metadata, D9/UL/Darakaraka calculations, sign lordships, `contact_rows`, `transit_houses`, `get_planet_positions`, and `dasha_at`. It never calls the legacy relationship scoring or scan functions. Natal calculations remain normal; generic transit houses use Chandra Lagna, with Lagna houses separately identified.

## Exact assessment gates

These are categorical states, not numerical scores or calibrated probabilities.

| Assessment | Required architecture | Trigger |
| --- | --- | --- |
| Romance | Romance period and romance trigger | A trigger without the period is reported only as a short-term trigger |
| Partner entry | Partnership period, qualified Jupiter support, D9 corroboration or positive UL/DK support, and at least two independent gate actors | Partner trigger inside that architecture |
| Commitment | Partnership period, qualified Jupiter support, D9 corroboration, continuity, and at least two independent gate actors | Partner trigger inside that architecture |
| Stress | Stress period, Saturn structural activation, and at least two independent gate actors | Moon/Venus/Mars timing; nodes/Mars can reinforce existing architecture |

Romance period requires romance-relevant AD plus romance-relevant MD or PD. Partnership period requires directly partnership-relevant AD, or supporting AD plus directly partnership-relevant MD or PD. Stress period requires AD to be both directly partnership-relevant and difficult, difficult AD plus directly partnership-relevant MD/PD, or directly partnership-relevant AD plus difficult PD. D9 and continuity qualification use AD/PD; MD is background only.

Only period and structural gate witnesses satisfy actor independence. Extra fast triggers cannot manufacture the two-actor requirement. Stress states never assert definitive separation.

## Evidence and duplicate prevention

Canonical evidence records identify actor, physical target, reference domain, operator, and interval. Alternative descriptions of one physical condition retain aliases and provenance rather than creating extra independent contributions. Rahu/Ketu share one node actor group. Degree contacts remain diagnostic-only. Each assessment records its own evidence usage and exclusions.

## Parameters and declared decisions

Diagnostic degree orb: 3 degrees. Minimum structural gate actors: two. Window sign-search brackets: one hour, with detected speed-station splits and one-second boundary refinement. No minimum duration or gap filling. No scoring weights, historical similarity metric, or probability calibration. Ayanamsa is inherited from the supplied natal chart.

The detailed methodology and exact Vedha map are in [relationship-timing-v2.md](relationship-timing-v2.md). Ambiguities and implementation decisions are recorded in [relationship-v2-implementation-decisions.md](relationship-v2-implementation-decisions.md), including the new v2-only Jaimini aspect operator, positive Jupiter UL/DK qualification, continuity eligibility, category-specific Mars handling, and boundary-search limits.

## Window and debug capabilities

Window functions preserve contiguous qualifying intervals, constituent evidence, dasha changes, and trigger subintervals. No scan runs automatically. The optional JSON debug interface requires an explicit exported chart and timezone-aware instant; no UI replacement was made. Window tests used fabricated motion and periods only.

The one-hour bracketing strategy is not a mathematical guarantee against arbitrary sub-hour oscillations. Unknown birth-time precision produces provisional warnings rather than silently dropping sensitive calculations.

## Test results and preservation

The three new test modules passed: **67 passed in 0.22 seconds**. They cover synthetic role/gate behavior, Moon-house climate and Vedha, structural and trigger distinctions, duplicate handling, fabricated window boundaries, v1.1 synthetic preservation, and frozen-source integrity. `git diff --check` passed. Previously captured hashes of pre-existing Python files remained unchanged.

The full pre-existing suite was deliberately not run because it contains calendar-specific evaluations excluded by the approved synthetic-only implementation scope. This is a limitation of validation, not a claim that the complete existing suite passed.

## Freeze and independence

Version: `relationship_timing_v2_0`.

Implementation SHA-256: `1ce3aeac2041a8b9ec58e9e9ef2c2753075b5b17a49345d1ab3497a543c307b4`.

`freeze.json` records source, methodology, tests, shared dependencies, parameters, and the starting Git commit. There is no implementation commit yet. Runtime provenance reports mismatches; it does not silently redefine the model. This completion report is outside the frozen calculation source.

No historical relationship template, outcome, date, score, weight, threshold, or similarity feature was used to implement or tune v2. No personal event validation, October analysis, or astronomical future scan was run. Existing historical context is not claimed to have been unknown; the implementation and synthetic tests do not use it as model input. Historical cases remain reserved for external validation after freezing.

The next phase is review of this frozen implementation before any real-date validation or UI integration.
