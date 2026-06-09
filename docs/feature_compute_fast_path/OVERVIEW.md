# Feature Compute Fast Path Overview

`FEATURE_COMPUTE_FAST_PATH_V1` is a producer-compute campaign for a
single-machine, local, columnar, batch/vectorized, incremental feature/label
materialization path. The goal is to stop large-scale backfill from depending on
the per-row Python reference engine for throughput, while retaining that
reference engine as the correctness oracle.

## Parity Discipline

The V1 path is not accepted for a family or label pack until a synthetic-fixture
reference-parity test proves the fast output matches the reference output for:

- feature or label values, exact where required and within documented tolerance
  where floating-point differences are expected
- `available_ts` and `label_available_ts`
- insufficient-window, input-gap, and session-reset rows
- missingness and quality flags
- reference feature or label identity

Unexplained differences are blockers. Benchmark evidence is required before the
campaign can make a runtime-speed claim.

## Retained Oracle

The existing reference engine remains in place and is never deleted or weakened.
The V1 path produces values for existing governed feature and label definitions;
it does not create new feature identities, label identities, AlphaSpecs, or alpha
hypotheses.

## P01 Engine Core

`src/alpha_system/features/fast/` contains the first shared V1 producer core:

- `PackMaterializer` loads one symbol-year canonical OHLCV frame through the
  sanctioned data-layer loader supplied by the caller.
- `FastFeaturePack` binds a `FeatureSetSpec` to Polars expressions for the
  governed values and quality flags.
- Feature identity is derived only with `FeatureVersion.derive(feature_spec)`,
  matching the reference engine's content-addressed id for the same
  `FeatureSpec`.
- Value persistence writes through the shared value-store helpers and
  registration goes through `FeatureStore`; the fast path does not write
  registry rows directly.
- Fast-produced feature registry records carry `producer_engine_id` as a
  registry record field and `value_schema_version` through the value-store
  handle. Fast-produced label records carry the same provenance through the
  existing label registry metadata and lineage path.

The P01 tests provide a reusable parity harness for later pack phases. It
compares feature values, `available_ts`, gap rows, quality flags, and
feature-version identity on tiny synthetic fixtures.

## P02 Base OHLCV Pack

`FCFP-P02` wires the first governed family pack into the V1 path. The
`base_ohlcv` pack resolves through `build_fast_feature_pack()` and computes the
six fixed-parameter Base OHLCV features from one Polars OHLCV frame:
`returns`, `log_returns`, `rolling_volatility`, `rolling_range`,
`range_position`, and `volume_zscore`.

Its synthetic fixture parity gate keeps the reference Base OHLCV family as the
oracle. The committed evidence is value-free: per-feature parity status,
max/median absolute diffs, gap counts, `available_ts` parity, and
feature-version identity equality only.

## P03 Session / Calendar / Roll Pack

`FCFP-P03` adds `alpha_system.features.fast.session_calendar_roll` and wires the
governed `SESSION_CALENDAR_ROLL` family through the same
`build_fast_feature_pack()` resolver. The pack computes session ids, RTH clock
minutes, RTH/ETH flags, day-of-week, and roll proximity from one Polars OHLCV
frame. Roll proximity follows the reference grouping and ordering:
`instrument_id`, then `(bar_start_ts, available_ts)`, with the next
`(contract_id, series_id)` transition backward-filled inside each instrument.

The synthetic parity gate is exact for these integer/string/list features. It
covers RTH/ETH boundaries, pre-open and post-close clock clamping,
contract-roll proximity and absent-roll flags, synthetic no-trade
position-only flags, row timing, entity ids, and feature-version identity.

The canonical fast frame does not yet carry the optional expiration/status
metadata maps used by the reference family. The fast pack therefore implements
the faithful absent-metadata behavior for `minutes_to_expiration` and
`halt_status_flag`: `None` values plus `expiration_metadata_absent` or
`status_metadata_absent` flags. Present-metadata values remain deferred to the
reference engine until a governed frame metadata projection is added.

## P04 VWAP / Session-Auction Pack

`FCFP-P04` adds `alpha_system.features.fast.vwap_session_auction` and wires the
governed VWAP / session-auction feature set through
`build_fast_feature_pack()`. The pack computes running VWAP, anchored VWAP,
distance to VWAP, opening range, and overnight range from one Polars OHLCV
frame. It uses vectorized session and anchor state columns while keeping the
reference OHLCV family as the oracle.

The synthetic parity gate covers session-reset cumulative VWAP, RTH anchor
activation and reset, opening-window boundary behavior, ETH-to-RTH overnight
carry, leading no-trade input, zero-volume input, and zero-VWAP distance gaps.
The committed evidence is value-free: counts, gap coverage, tolerance, and
max/median absolute diffs only.

## P05 Regime / Volatility / Compression Pack

`FCFP-P05` adds `alpha_system.features.fast.regime_vol_compression` and wires
the governed ATR, trendiness, and range-contraction feature set through
`build_fast_feature_pack()`. The pack computes ATR as true range plus a trailing
rolling mean, trendiness as the rolling efficiency ratio, and
range-contraction as the structure-family current range versus exclusive prior
mean range.

The synthetic parity gate covers two session segments, reset-on-session warm-up,
no-trade input-gap propagation, flat-close `zero_movement` trendiness rows, and
the structure-family prior-window behavior. The committed evidence remains
value-free: counts, tolerances, and max/median absolute diffs only.

## P12 Engine Provenance / Reconciliation

`FCFP-P12` makes producer provenance explicit on the official feature registry
write path. Reference feature registrations default to
`alpha_system.features.reference.materializer.v1`; V1 feature registrations use
`alpha_system.features.fast.pack_materializer.v1`. The provenance field and
`value_schema_version` remain descriptive registry metadata and do not enter
`feature_version_id` or `label_version_id`.

The reconciliation policy is value-free and fail-closed: identical or
within-tolerance V1 output keeps the existing valid reference output and tags
provenance; beyond-tolerance output is treated as a V1 bug, an explicit
value-schema-version boundary, or a future official keystone re-materialization
case. The fast path never silently overwrites or interleaves engines inside one
logical value series.

## P06 Liquidity / PA Structure Pack

`FCFP-P06` adds `alpha_system.features.fast.liquidity_pa_structure` and wires
the governed Liquidity Structure feature set through `build_fast_feature_pack()`.
The pack computes prior high/low distances, opening-range distances, sweep and
failed-breakout flags, close-location value, wick rejection, and range
contraction from one Polars OHLCV frame.

The synthetic parity gate covers session-scoped prior windows, opening-session
boundaries, no-trade input gaps, sweep and failed-breakout branches,
zero-range guards, and range-contraction values. It keeps the reference
Liquidity Structure family as the oracle and commits no feature values.

## P07 Volume / Activity Pack

`FCFP-P07` adds `alpha_system.features.fast.volume_activity` and wires the
governed volume/activity pack through `build_fast_feature_pack()`. The pack does
not introduce new volume/activity definitions; it computes the existing governed
bindings selected by the reference scaleout driver: rolling volume, volume
z-score, session minute, rolling range, range position, trendiness,
close-location value, and wick rejection.

The pack prepares typed OHLCV columns, normalized input flags, and contiguous
session segments once, then evaluates the reset-on-session rolling and
point-in-time expressions for the whole feature set. The synthetic parity gate
covers leading insufficient windows, a no-trade input gap, session-boundary
reset behavior, zero-range structure guards, `available_ts`, quality flags, and
reference feature-version identity.

## P08 BBO Tradability / Top-Book Pack

`FCFP-P08` adds `alpha_system.features.fast.bbo_tradability` and wires the
governed BBO tradability / top-book feature set through
`build_fast_feature_pack()`. The pack computes spread, spread ticks, spread
bps, top-book sizes/depth/imbalance, microprice, microprice-minus-mid,
missing-BBO and bad-quote flags, wide-spread and low-depth flags, and
reset-on-session spread z-score values from one BBO frame.

The synthetic parity gate covers missing and quarantined BBO rows,
wide-spread/low-depth flags, spread-ticks gaps, reset-on-session rolling
warm-up, `available_ts`, quality flags, and reference feature-version identity.
No feature values or real market data are committed.

## P09 Cross-Market Aligned Panel Pack

`FCFP-P09` adds `alpha_system.features.fast.cross_market_panel` and wires the
governed ES/NQ/RTY Cross-Market feature set through
`build_fast_feature_pack()`. The pack prepares one aligned Polars panel for the
selected reference alignment policy: `strict_intersection` joins exact
same-event ES/NQ/RTY rows and derives `available_ts` as the max contributing
availability timestamp, while legacy `asof` uses the reference union
availability timeline. The strict path does not carry one instrument's return
into another instrument's later timestamp.

The pack computes all 11 governed Cross-Market values from that panel:
synchronized returns, NQ/RTY return spreads versus ES, NQ/RTY beta residuals
versus ES, NQ/RTY rolling correlations versus ES, confirmation/divergence
flags, and risk-on/risk-off rotation proxies. The synthetic parity gate covers
leading history gaps, no-trade input gaps, reset-on-session behavior,
zero-benchmark and zero-target rolling variance gaps, optional exact-time BBO
flags, no-forward-fill strict-intersection behavior, `available_ts`, quality
flags, and reference feature-version identity. No feature values or real market
data are committed.

## P11 Targeted / Incremental CLI

`FCFP-P11` extends the existing local scaleout CLI and unit-grid builder with
targeted / incremental selection. `alpha scaleout feature-pack` can now target
family, feature id, configured feature group, label selector, symbols, years,
and DatasetVersion ids. Dry-run emits value-free unit, row, and time estimates;
execute mode runs selected units only; completed units are skipped only through
checkpoint plus official registry truth.

## P14 Producer Path Integration

`FCFP-P14` makes the V1 `PackMaterializer` the default scaleout producer path.
The CLI exposes `--engine {v1,reference}` with `v1` as the default and keeps the
reference engine selectable as the oracle/fallback. The selected engine does not
enter governed identity: V1 still writes values for existing
`feature_version_id` and `label_version_id` locks only.

The driver preserves checkpoint/restart behavior with engine-aware registry
truth. A completed unit skips only when the official registry resolves the
previewed feature identities to existing values for the selected producer
engine; reference-produced records are not silently treated as V1 completion.

The P14 resolver smoke materializes representative bounded-real feature and
label locks through the integrated V1 path, resolves exact locks through the
official runtime resolver, and verifies stale or fuzzy controls fail closed.
The committed report is value-free and lives under
`research/feature_compute_fast_path_v1/integration/`.

## P15 CPU Worker Parallelism

`FCFP-P15` adds `--workers` and `ALPHA_CPU_WORKERS` for V1 scaleout compute.
Worker processes load canonical inputs, compute V1 values, and write local
Parquet plus deterministic manifests; the parent process remains the only
official `FeatureStore` registry writer and registers worker outputs in
deterministic unit order. Cross-market alignment is planned as one
ES/NQ/RTY panel unit per year.

The fast value stores canonicalize record order before content hashing so
worker count cannot change hashes. The value-free worker benchmark records
elapsed time, rows/sec, canonical reads, memory, registry-queue wait,
resolver-smoke, parity, deterministic hashes, worker reductions, and the
fastest stable requested worker count.

## Boundaries

This campaign is substrate/infra engineering only. It does not include live
trading, paper trading, broker operations, order routing, production deployment,
external provider calls, Ray/GPU/cluster work, a feature-compiler/DSL platform,
new feature/label families, parameter search, or profitability/tradability
claims.

Raw/canonical data, feature values, label values, provider responses, local
SQLite registries, heavy artifacts, logs, caches, and `runs/**` artifacts remain
local-only and are never committed.

## Evidence Directory

`research/feature_compute_fast_path_v1/` is reserved for commit-eligible,
value-free summaries produced by later phases: parity reports, benchmark
summaries, and reconciliation summaries. Per-row values, Parquet outputs,
SQLite registries, and provider responses are not commit-eligible there.
