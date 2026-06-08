# PackMaterializer Contract

`PackMaterializer` is the P01 fast-path engine core for feature values. It is a
producer only: it computes governed values for existing `FeatureSpec` objects and
never mints a new feature identity.

## Engine Interface

Family phases declare a `FastFeaturePack`:

- `feature_set`: the governed `FeatureSetSpec`.
- `declarations`: one `FastFeatureDeclaration` per feature, in feature-set order.
- each declaration supplies Polars expressions for `value` and optional
  `quality_flags`, plus optional overrides for `entity_id`, `event_ts`, and
  `available_ts`.

The materializer sorts canonical rows by `available_ts`, evaluates all declared
expressions as a pack, converts the result to `FeatureValueRecord`, and validates
that every record belongs to the plan's feature-version ids.

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

## Optional Dependency

Polars remains optional. Importing `alpha_system.features.fast` does not import
Polars. Runtime compute, canonical frame construction, and Parquet writes call
the existing `require_dependency("polars")` guard, so environments without
Polars fail closed or skip the synthetic parity tests cleanly.
