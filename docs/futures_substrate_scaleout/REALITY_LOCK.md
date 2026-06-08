# Reality Lock - FUTSUB-P01

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P01` - Reality Report Lock and Core Pilot Handoff Ingestion  
Lock date: 2026-06-07  
Status: value-free factual baseline for downstream planning

This document reconciles the measured substrate reality and the Core Pilot
scaleout handoff into the single locked baseline for this campaign. It does not
materialize values, accept DatasetVersions, edit primitives, run diagnostics,
create research claims, or change any runtime behavior.

## Source Artifacts

- `docs/SUBSTRATE_REALITY_REPORT.md` - measured local substrate reality from
  direct inspection of local-only data roots and registries.
- `research/futures_core_alpha_pilot_v1/closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`
  - Core Pilot scaleout handoff.
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md` - campaign
  goal contract and inherited boundary.
- `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md` - Core Pilot
  closeout resolution and acceptance audit.
- `research/futures_core_alpha_pilot_v1/promotion/INDEX.md` and
  `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md` -
  promotion boundary evidence.

Where the measured reality report and pilot handoff overlap, they agree: the
raw Databento history and substrate code exist, but the lock-resolvable value
layer is still the smoke/pilot seed.

## Locked Baseline

1. Local Databento market-data coverage is deep and real as registered local
   substrate: ES/NQ/RTY, OHLCV-1m and BBO-1m, 2018-01 through 2026-05.
2. `registry/datasets.sqlite` records 29 DatasetVersions: 9 OHLCV-1m, 9 dense
   OHLCV research-grid, 9 BBO-1m, and 2 IBKR validation versions.
3. `registered != accepted/locked`: the dataset registry does not persist a
   per-version accept/reject verdict or coverage-quality lock. DatasetVersion
   acceptance-lock is therefore future work, beginning with `FUTSUB-P02`.
4. The current lock-resolvable value substrate is a single-week
   (2024-01-02 -> 2024-01-09), ES-only, OHLCV+session-only seed pack.
5. Registered feature values are limited to base OHLCV and two session context
   features: returns, log returns, rolling volatility, rolling range, volume
   z-score, range position, `rth_flag`, and `session_minute`.
6. Registered label values are limited to 5m, 10m, and 30m forward-return
   labels over the same smoke window.
7. Feature family code exists for `ohlcv`, `bbo`, `session`, `cross_market`,
   and `structure`; label family code exists for `fixed_horizon`,
   `cost_adjusted`, `path`, and `event`. Most families do not yet have
   full-window materialized values.
8. The continuous series are unadjusted provider-continuous `ES.v.0`, `NQ.v.0`,
   and `RTY.v.0`. Roll splice points are real price jumps. No materialized roll
   calendar exists today, and provider-internal exact splice points are not
   recoverable from the continuous series alone.
9. `experiments/splits.py` contains split primitives, including
   `train_validation_split`, `walk_forward_splits`, and
   `apply_purge_embargo`, but those primitives are not wired into the runtime
   diagnostics path. Overlap-aware `N_eff` reporting is missing.
10. Keystone identity and resolver-smoke discipline are inherited as the entry
    invariant: locks must resolve to real registry-backed Parquet values, and
    stale or unresolvable locks fail closed rather than substituting values.

## Inherited Promotion Boundary

The inherited promotion boundary is locked verbatim:

```text
4 REJECT / 6 INCONCLUSIVE / 0 WATCH / 0 CANDIDATE_RESEARCH
```

This means no FactorLibrary-ingestible survivor and no Strategy Reference
candidate. The Core Pilot boundary is a substrate coverage finding, not a new
research claim.

## Exact Substrate Gaps To Close

The campaign starts from these inherited gaps:

- Single-week (2024-01-02 -> 2024-01-09), ES-only, OHLCV+session-only
  lock-resolvable substrate.
- `FUTCORE-P18`: missing regime trendiness, volatility, and compression values.
- `FUTCORE-P19`: missing liquidity/PA sweep, failed-breakout, wick,
  displacement, and compression primitives as materialized values.
- `FUTCORE-P20`: missing locked/materialized BBO top-book FeaturePack.
- Missing full ES/NQ/RTY aligned cross-market values.
- `registered != accepted/locked`; DatasetVersion acceptance and coverage
  verdicts are not persisted in the registry.
- Unadjusted provider-continuous series have real roll-splice jumps and no
  materialized roll calendar.
- `experiments/splits.py` primitives are not wired into the runtime path; no
  overlap-aware `N_eff` reporting is present.

## Downstream Entry Gate

Downstream phases must plan from the baseline above:

- `FUTSUB-P02` owns DatasetVersion inventory and acceptance-lock contract work.
- `FUTSUB-P03` owns roll-boundary metadata and roll-splice guard work.
- `FUTSUB-P04` and later preflight/materialization phases must not infer that
  registration is acceptance, or that smoke values are full-window values.
- Resolver-smoke is not rerun in this phase. The inherited discipline remains
  intact by reference and is enforced in later feature, label, and StudySpec
  resolver-smoke phases.

## Boundary

This reality lock is value-free. It records ids, counts, paths, source
relationships, limitations, and future gates only. It does not commit raw data,
canonical data, feature values, label values, local SQLite databases, roll
calendar data, provider responses, run artifacts, or heavy artifacts. It makes
no paper/live/broker/order, production, capital-allocation, profitability, or
tradability claim.
