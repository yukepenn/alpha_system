# BBO And Cross-Market Matrices

`FUTSUB-P26` adds the value-free BBO quality and cross-market alignment matrices for `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

## Artifacts

- `research/futures_substrate_scaleout_v1/matrices/bbo_quality.md` records symbol x accepted-year x session x spread-bucket x BBO-quality-regime summaries for the registered P12 BBO FeaturePack.
- `research/futures_substrate_scaleout_v1/matrices/cross_market_alignment.md` records year x session x state/scope coverage, strict-intersection survival, and availability-discipline evidence for the registered P13 cross-market FeaturePack.

## Production Method

Both matrices were produced read-only from local registered values under `$ALPHA_DATA_ROOT` using the supported feature registry and value-store surfaces. The reproducibility command surface is:

```bash
PYTHONPATH=src alpha feature list --alpha-data-root "$ALPHA_DATA_ROOT" --json
PYTHONPATH=src alpha feature report --kind both --feature-version-id <recorded fver> --alpha-data-root "$ALPHA_DATA_ROOT" --json
```

The local scratch aggregation helper resolved the same registry rows through the CLI registry helper in read-only mode, filtered registered Parquet-backed value handles by exact `feature_version_id`, and emitted only counts, rates, shares, bucket labels, and identities. The helper and any intermediate frames were local-only and are not commit artifacts.

## BBO Reading Contract

BBO-1m is a time-sampled + forward-filled tradability proxy. The BBO matrix must not be read as passive-fill evidence, queue-priority evidence, intra-minute-impact evidence, execution quality, or execution truth.

The BBO matrix uses the materialized P12 flags as-is: `missing_bbo`, `bad_quote`, `wide_spread`, and `low_depth`. It does not redefine those flags. It uses `bbo_tradability_spread` for spread buckets and records `bbo_tradability_spread_ticks` availability separately; in this local substrate pass, spread ticks resolved all-null while spread values and quality flags resolved.

The session split is also consumed as materialized substrate, not rederived. The registered session flags collapse the accepted rows into `ETH_NON_RTH` (`eth_segment_flag=1`, `rth_segment_flag=0`, `halt_status_flag=null`). Any downstream need for an RTH or maintenance-adjacent split is a session-substrate follow-up, not a P26 timestamp rewrite.

FUTSUB-P28 must consume the worst-cell section as diagnostics gating context. Cells with concentrated missingness, bad quotes, wide spreads, or low top-book availability are not to be smoothed away or treated as complete tradability evidence.

## Cross-Market Reading Contract

The cross-market substrate uses `alignment_policy=strict_intersection`. The `asof` default still exists in `src/alpha_system/features/fast/cross_market_panel.py`, but the FUTSUB scaleout path is guarded to reject `asof` for substrate materialization. The P26 matrix does not present `asof`-aligned aggregates as substrate truth.

The availability re-check joined every registered cross-market synchronized-return panel row by `event_ts` to registered ES/NQ/RTY `base_ohlcv_log_returns` rows. The matrix records the per-year panel rows where at least one exact `event_ts` contributor did not resolve; these contributor gaps are availability context, not estimated or forward-filled coverage. The same check found zero panel rows whose `available_ts` preceded any resolved contributor `available_ts`, and zero duplicate panel `event_ts` rows.

Lead-lag, residual, divergence/agreement, relative-strength, and catch-up/rotation entries are state-coverage records only. They are not relationship-strength, predictive, profitability, tradability, production, paper/live, broker, order-routing, or capital-allocation evidence.

## Downstream Consumption

- `FUTSUB-P27` should use the matrices as lock/readiness context when re-locking Core Pilot StudySpecs, preserving the 2018 expected exclusion and 2019/2026 warning context.
- `FUTSUB-P28` should route BBO diagnostics through the BBO worst-cell context and route cross-market diagnostics through the strict-intersection survival and availability checks.
- `FUTSUB-P29` should interpret any rerun output under `docs/RESEARCH_INTERPRETATION_POLICY.md` and must not promote these matrices into an alpha/profitability/tradability claim.
- `ALPHA_VALIDATION_GOVERNANCE_V1` via P31 should treat the matrices as value-free substrate quality gates and require explicit review before any downstream promotion state.
- `ALPHA_FUTURES_MULTI_HORIZON_ALPHA_MINING_V1` via P32 should consume the matrices as availability and quality context, not as mined signal evidence.

## Exclusions

2018 remains expected-excluded for these matrices because the required DatasetVersions are `BLOCKED`. No registry writes, materialization, external provider calls, raw/canonical data reads by the committed artifact, code changes, test changes, or heavy artifacts are part of this phase.

The committed artifacts are markdown-only and value-free: counts, rates, shares, bucket labels, state labels, commands, and registry identities.
