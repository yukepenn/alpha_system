# FUTSUB-P01 Reality Baseline

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P01`  
Purpose: value-free preflight baseline for downstream substrate scaleout phases

This preflight note mirrors the durable lock at
`docs/futures_substrate_scaleout/REALITY_LOCK.md`. It is not a diagnostic
report and does not contain materialized feature, label, dataset, or market
values.

## Inputs Consumed

- `docs/SUBSTRATE_REALITY_REPORT.md`
- `research/futures_core_alpha_pilot_v1/closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md`
- `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
- `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`
- `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`

## Preflight Baseline

- Local Databento ES/NQ/RTY OHLCV-1m and BBO-1m DatasetVersions are registered
  across 2018-01 through 2026-05, but registration is not the same as an
  accepted/locked coverage verdict.
- The lock-resolvable value substrate remains the smoke seed: single-week
  (2024-01-02 -> 2024-01-09), ES-only, OHLCV+session-only, with 5m/10m/30m
  labels.
- BBO, regime, liquidity/PA, and full cross-market values are not materialized
  into locked FeaturePacks today.
- The unadjusted provider-continuous series contain real roll-splice jumps, and
  no materialized roll calendar exists.
- `experiments/splits.py` exists but is not wired into the StudySpec/runtime
  diagnostics path; overlap-aware `N_eff` reporting is missing.
- Consumed primitives are expected to remain read-only in this phase:
  `runtime`, `features`, `labels`, `experiments.splits`,
  `data.foundation.rolls`, and `core.value_store`.

## Inherited Boundary

```text
4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH
```

No FactorLibrary-ingestible survivor and no Strategy Reference candidate are
inherited from the Core Pilot.

## Downstream Gates

- `FUTSUB-P02`: do not treat registered DatasetVersions as accepted/locked until
  the acceptance-lock contract is written and reviewed.
- `FUTSUB-P03`: do not treat provider-continuous roll boundaries as
  provider-exact; roll-splice guard work must make the approximation explicit.
- Later materialization phases: do not substitute missing BBO, regime,
  liquidity/PA, or cross-market values; resolver-smoke must fail closed on stale
  or unresolvable locks.

## Artifact Boundary

This preflight baseline is value-free and commit-eligible. It does not write or
copy raw/canonical data, materialized values, local registries, roll-calendar
data, provider responses, run artifacts, logs, caches, or heavy files. It makes
no paper/live/broker/order, production, capital-allocation, profitability, or
tradability claim.
