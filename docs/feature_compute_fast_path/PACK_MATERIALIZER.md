# PackMaterializer Contract

`PackMaterializer` is the P01 fast-path engine core for feature values. It is a
producer only: it computes governed values for existing `FeatureSpec` objects and
never mints a new feature identity.

## Engine Interface

Family phases declare a `FastFeaturePack`:

- `feature_set`: the governed `FeatureSetSpec`.
- `declarations`: one `FastFeatureDeclaration` per feature, in feature-set order.
- `prepare_frame`: an optional pack callback for vectorized intermediate Polars
  columns that are needed by multiple declarations.
- each declaration supplies Polars expressions for `value` and optional
  `quality_flags`, plus optional overrides for `entity_id`, `event_ts`, and
  `available_ts`.

The materializer sorts canonical rows by `available_ts`, applies
`prepare_frame` when present, evaluates all declared expressions as a pack,
converts the result to `FeatureValueRecord`, and validates that every record
belongs to the plan's feature-version ids.

## Canonical Loading

`SymbolYearFrameRequest` loads one symbol-year OHLCV frame through the existing
data-layer canonical loader. Callers provide the canonical root; the fast feature
module does not encode provider literals or raw/canonical repository paths. The
loaded frame is cached per request so a pack can compute all declarations from
one in-memory frame.

## Identity

Fast identity is:

```python
FeatureVersion.derive(feature_spec)
```

This is the same content-addressed identity used by the reference engine. It
hashes the computational contract and excludes request provenance such as
`feature_request_id`; fast packs produce values for that identity, not a separate
V1 identity.

## Persistence And Registration

Fast materialization builds the normal `FeatureMaterializationPlan`, writes
values through the shared value-store helpers, and registers through
`FeatureStore.register_materialized_feature()`.

Registry writes are protected by a process-local serial lock and remain delegated
to the official `FeatureStore` / `FeatureRegistry` path. The fast path does not
write SQLite rows by hand. The default value-store mode is `dual`: Parquet value
store plus JSONL audit output under `ALPHA_DATA_ROOT`.

Fast-produced registry records include:

- `producer_engine_id = alpha_system.features.fast.pack_materializer.v1`
- `value_schema_version = alpha_system.features.fast.values.v1`

These are provenance fields and do not participate in `feature_version_id`.

## Parity Harness

`tests/unit/feature_compute_fast_path/parity_harness.py` provides
`assert_feature_records_match()`, which later pack phases can reuse. It compares:

- exact feature-version id equality
- feature values, with explicit tolerance only when documented
- `available_ts`
- gap rows, including `insufficient_window`, `input_gap`, and `session_reset`
- quality flags

The P01 demonstrator test computes a tiny synthetic Base OHLCV `returns` feature
through both the reference family and a test-only fast declaration. It is not a
production Base OHLCV pack.

## Base OHLCV Pack

`FCFP-P02` adds the first governed family pack:
`alpha_system.features.fast.build_fast_feature_pack()` resolves the exact
six-feature `base_ohlcv` feature set to the Polars pack in
`alpha_system.features.fast.base_ohlcv`.

The pack is fixed to the reference parameters used by the proof and parity gate:
`horizon=1`, `window=20`, `ddof=0`, and `reset_on_session=False`. It computes
`returns`, `log_returns`, `rolling_volatility`, `rolling_range`,
`range_position`, and `volume_zscore` from one canonical OHLCV frame. Feature
identity still comes from `FeatureVersion.derive(feature_spec)`; the pack
declares values and quality flags only.

The synthetic parity test under `tests/unit/feature_compute_fast_path/` compares
the pack against the reference Base OHLCV family for values, `available_ts`, gap
rows, quality flags, and feature-version identity. Five features are exact on
the fixture; `volume_zscore` uses the documented rolling-standard-deviation
float tolerance.

## Session / Calendar / Roll Pack

`FCFP-P03` adds the governed Session / Calendar / Roll pack:
`alpha_system.features.fast.session_calendar_roll`. The resolver accepts the
exact ten-feature `SESSION_CALENDAR_ROLL` feature set and derives every
`feature_version_id` from the same `FeatureSpec` identity as the reference
family.

The pack computes:

- `session_id`, RTH/ETH segment flags, and `day_of_week`
- RTH clock minutes with `outside_rth`, `before_rth_open`, and
  `after_rth_close` flags
- `bars_to_roll` and `minutes_to_roll` by grouping on `instrument_id`, ordering
  by `(bar_start_ts, available_ts)`, detecting adjacent `(contract_id,
  series_id)` transitions, and backward-filling the next transition boundary
- absent-metadata behavior for `minutes_to_expiration` and `halt_status_flag`

When dense-grid semantic columns are present, the pack reproduces
`synthetic_no_trade_position_only`; canonical sparse no-trade rows retain the
reference `no_trade_position_only` flag. If those optional dense-grid columns
are absent, the materializer supplies null/false defaults so existing canonical
OHLCV frames remain valid.

Present expiration/status metadata values are intentionally deferred because the
P01 frame contract does not yet project the reference metadata maps as Polars
columns. The fast pack does not fabricate those values; it emits `None` plus the
reference absent-metadata flags.

## VWAP / Session-Auction Pack

`FCFP-P04` adds the governed VWAP / session-auction pack:
`alpha_system.features.fast.vwap_session_auction`. The resolver accepts the
exact five-feature set for `vwap`, `anchored_vwap`, `distance_to_vwap`,
`opening_range`, and `overnight_range`; each declaration derives its
`feature_version_id` from the same `FeatureSpec` identity as the reference
family.

The pack prepares contiguous session segment columns once and then computes:

- session-reset running VWAP with `no_trade` and `zero_volume` gap branches
- anchored VWAP with `before_anchor`, `no_trade`, and `zero_volume` branches
- distance to session VWAP, including the `zero_vwap` gap branch
- RTH opening range with `outside_rth` and `no_opening_trade`
- ETH overnight range with frozen carry into RTH and the reference
  `no_overnight_trade` / `no_overnight_range` branches

The synthetic parity fixture covers two RTH anchors, ETH-to-RTH carry, an
opening-window boundary, leading no-trade input, zero-volume input, and a
synthetic zero-VWAP edge row. No feature values or real market data are
committed.

## Regime / Volatility / Compression Pack

`FCFP-P05` adds the governed regime / volatility / compression pack:
`alpha_system.features.fast.regime_vol_compression`. The resolver accepts the
exact three-feature set for `atr`, `trendiness`, and `range_contraction`; each
declaration derives its `feature_version_id` from the same `FeatureSpec`
identity as the reference family.

The pack prepares shared OHLCV, normalized quality-flag, and contiguous session
segment columns once and then computes:

- ATR true range, including previous valid close and reset-on-session behavior,
  followed by the reference rolling mean and primitive gap flags
- trendiness as the rolling efficiency ratio with `insufficient_window`,
  `input_gap`, and `zero_movement` branches
- structure-family range contraction using an exclusive prior window, current
  no-trade handling, and zero-range guards

The synthetic parity fixture covers two session segments, warm-up after a
session reset, a no-trade input gap, flat-price `zero_movement` rows, and an
exclusive prior-window range-contraction value. No feature values or real market
data are committed.

## Liquidity / PA Structure Pack

`FCFP-P06` adds the governed liquidity-sweep / price-action structure pack:
`alpha_system.features.fast.liquidity_pa_structure`. The resolver accepts the
governed Liquidity Structure feature set, and each declaration derives its
`feature_version_id` from the same `FeatureSpec` identity as the reference
family.

The pack prepares shared OHLCV, normalized quality-flag, contiguous session,
prior-window, and opening-window columns once and then computes:

- prior high/low distances and sweep / failed-breakout flags from exclusive
  prior windows
- opening-range distances with opening-session and no-opening-trade guards
- close-location value and wick rejection as point-in-time structure proxies
- range contraction with current no-trade, prior-window, and zero-range guards

The synthetic parity fixture covers input gaps, session resets, opening-range
boundaries, sweep branches, zero-range guards, and range-contraction values. No
feature values or real market data are committed.

## Volume / Activity Pack

`FCFP-P07` adds the governed volume/activity pack:
`alpha_system.features.fast.volume_activity`. The resolver accepts the exact
mixed feature set selected by the reference scaleout driver: rolling volume,
volume z-score, session minute, rolling range, range position, trendiness,
close-location value, and wick rejection. The pack computes values for existing
governed primitive identities only; it does not mint participation, regime, or
effort/result feature ids.

The pack prepares shared OHLCV, normalized input-flag, and contiguous session
segment columns once and then computes:

- reset-on-session rolling volume, rolling range, range position, and trendiness
- reset-on-session volume z-score with the reference `ddof=0` normalization
- session minute from the current contiguous `(series_id, session_label)` segment
- point-in-time close-location value and wick rejection structure proxies

The synthetic parity fixture covers leading insufficient windows, a no-trade
input gap, reset-window warm-up after a session boundary, zero-range structure
guards, `available_ts`, quality flags, and reference feature-version identity.
No feature values or real market data are committed.

## Cross-Market Aligned-Panel Pack

`FCFP-P09` adds the governed Cross-Market pack:
`alpha_system.features.fast.cross_market_panel`. The resolver accepts the exact
11-feature ES/NQ/RTY Cross-Market feature set, and each declaration derives its
`feature_version_id` from the same `FeatureSpec` identity as the reference
family.

The pack's `prepare_frame` builds one aligned panel and all declarations read
from that panel. Under the governed `strict_intersection` alignment policy, ES,
NQ, and RTY rows are joined only by exact shared `event_ts`; output
`available_ts` is the max contributing row / return availability timestamp, and
no instrument's stale return is carried into another instrument's later event.
The legacy `asof` policy remains supported for feature specs that select it.

The panel computes synchronized returns, return spreads, rolling beta residuals,
rolling correlations, confirmation/divergence flags, and rotation proxies while
preserving reference gap reasons and optional exact-time BBO quality flags. The
synthetic parity fixture covers leading history gaps, no-trade input gaps,
session-reset behavior, zero-benchmark and zero-target variance gaps, delayed
availability, missing-instrument no-imputation, `available_ts`, quality flags,
and reference identity. No feature values or real market data are committed.

## Optional Dependency

Polars remains optional. Importing `alpha_system.features.fast` does not import
Polars. Runtime compute, canonical frame construction, and Parquet writes call
the existing `require_dependency("polars")` guard, so environments without
Polars fail closed or skip the synthetic parity tests cleanly.
