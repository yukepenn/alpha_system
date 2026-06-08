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
- Fast-produced registry records carry `producer_engine_id` in registry metadata
  and `value_schema_version` through the value-store handle.

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
