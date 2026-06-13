# SHIP_REFIT-P03 Settler Evidence Note

This note is value-free. It records the coordinator's bounded scope decision
for SHIP_REFIT-P03 and contains no feature values, label values, returns,
observation rows, alpha claim, profitability claim, tradability claim, or
deployment claim.

## Result Of Record

- Settler: A-vs-B conditional re-score.
- Coordinator result date: 2026-06-13.
- Result: NULL.
- Summary: conditional uplift collapsed to approximately `1e-6` at full power
  across the substrate-scale observation range (`39M` to `66M` observations),
  cross-validated byte-exact against `research/regimes.py`.
- Bounded consequence: P03 stays scoped to detection power, MDE, and honest
  N_eff reporting. No interaction or gating detector is added in this phase.

## Scoped Lesson

The settler also exposed a distinct reporting gap: a stacked IC can dilute a
single declared factor's signal. P03 therefore reports MDE and power per
declared factor in addition to the stacked aggregate. This is reporting rigor
only; it is not a survivor finding and not an interaction detector.
