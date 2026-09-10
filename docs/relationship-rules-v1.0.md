# Relationship Timing Rules v1.0 — frozen model

This specification is fixed before evaluating saved personal events. No personal
date, event type, name, notes or outcome enters eligibility or thresholds. The
existing three categories retain their exact eligibility, family counts, matching,
flags, and future-window criteria. Ending/separation is additive.

## Basis and limits

We retain the app's whole-sign D1, sidereal longitudes, Vimshottari MD/AD/PD,
projected D9, seven-planet Darakaraka and Upapada conventions. The traditional
background includes partnership through the seventh/Venus and difficulty through
6/8/12 (BPHS, chapter 32, verses 35–37), seventh-house considerations and Upapada.
Source: [Brihat Parashara Hora Shastra translation](https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf).

The precise temporal scoring below is an application hypothesis, **not a classical
formula or validated breakup predictor**. Saturn, Ketu and Mars are selected as
pressure/detachment/conflict actors; their presence alone does not imply an ending.
No gendered or fatalistic classical outcomes are implemented. D9 transit projection
and the selected degree orb remain explicitly app conventions. No node drishti.

## Ending / separation: six candidate families

1. **Dasha:** an active MD/AD/PD lord must have BOTH a disruption role (Saturn,
   Ketu, Mars, or a D1 6/8/12 lord/occupant) AND a partnership role (Venus,
   D1/D9 seventh lord, DK, UL lord, or D1/D9 seventh-house occupant).
2. **Slow:** Saturn/Ketu degree conjunction/opposition to natal Venus, D1 seventh
   lord or Lagna. Sign-only aspects remain supporting context.
3. **House:** Saturn/Ketu/Mars in D1 1/7. Their 6/8/12 occupancy is eligible only
   with a simultaneous degree contact to natal Venus or seventh lord. Otherwise
   it is context; general adversity is not automatically relationship adversity.
4. **D9:** Saturn/Ketu/Mars project into the natal D9 seventh-house, seventh-lord,
   or Venus sign. Coincident target signs merge into one condition.
5. **UL/DK:** Saturn/Ketu/Mars share UL's sign or have a degree contact to DK.
   Sign-only aspects are context. DK overlapping another target role does not
   create an additional contact or point.
6. **Fast:** Mars degree conjunction/opposition to natal Venus or D1 seventh
   lord. Moon/Venus degree contacts to those same targets are neutral triggers,
   eligible only with eligible dasha AND slow background. Their contacts to
   natal Saturn/Ketu/Mars or house occupancy remain context.

## Counting and thresholds

Ending/separation uses a maximum matching: **one point per different family AND
per different source planet**. A planet's dasha/transit/D9/UL descriptions cannot
supply separate points. Repeated MD/AD/PD lords cannot stack. Multiple contacts,
role aliases, a close opposition plus its whole-sign aspect, and duplicated rows
cannot inflate the score. This is conservative operational diversity, not proof
of statistical independence (even distinct planets can be correlated).

Choose a maximum-size matching; ties prefer one containing both dasha and slow,
then fixed condition-ID order. One representative condition per matched family
and source is marked **Counted indicator**. All others are **Supporting context**,
with a reason distinguishing ineligible context from eligible but redundant
conditions. All candidate records are retained and downloadable.

The existing numeric display bands remain Low 0–1, Moderate 2–3, High 4–6.
Ending/separation counts the matched points, unlike the legacy categories' raw
eligible-family counts; the UI and exports explicitly distinguish them. A stacking
flag needs at least three matched families/sources including dasha and slow.
Existing future rules remain unchanged: above preceding 90-day median, at least
75th percentile, and at least two consecutive daily samples. High is a display
band, not a promise, and is distinct from the stacking flag.

## Freeze and comparison protocol

The rule manifest and scoring source files are pinned by regression checks.
Changes require a new model version and explicit review; mismatched historical
results are never a reason to silently edit v1.0. Orb and ayanamsha are recorded
inputs, not learned values. Hold them constant across comparisons. Old cached
results must be recalculated under this version rather than silently relabeled.
Unknown event times remain provisional local noon. Event labels are metadata.
Saved-event evaluations and private birth data must not be committed to GitHub.
