# FCFP-P02 Base OHLCV Parity Report

Value-free synthetic-fixture report for the V1 `base_ohlcv` Polars pack.

## Scope

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P02`
- Pack: `base_ohlcv`
- Fixture: `tests/fixtures/feature_compute_fast_path/base_ohlcv.py`
- Rows: 32 synthetic OHLCV rows, including one `no_trade` row
- Parameters: `horizon=1`, `window=20`, `ddof=0`,
  `reset_on_session=False`
- Tolerance: exact for five features; `volume_zscore` absolute tolerance
  `5e-8`, justified by rolling-standard-deviation summation order. The
  full-year proof documented max `volume_zscore` drift around `3.3e-8`.

## Results

| Feature | Rows | Valid value pairs | Gap rows | Max abs diff | Median abs diff | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `returns` | 32 | 29 | 3 | 0 | 0 | exact |
| `log_returns` | 32 | 29 | 3 | 0 | 0 | exact |
| `rolling_volatility` | 32 | 6 | 26 | 0 | 0 | exact |
| `rolling_range` | 32 | 7 | 25 | 0 | 0 | exact |
| `range_position` | 32 | 7 | 25 | 0 | 0 | exact |
| `volume_zscore` | 32 | 7 | 25 | 3.9968028886505635e-15 | 1.9984014443252818e-15 | within `5e-8` |

## Contract Checks

- `available_ts` parity: exact for all six features.
- Gap-row parity: exact for all six features, including first-window gaps,
  the no-trade input gap, and post-gap recovery.
- Quality-flag parity: exact for all six features.
- `feature_version_id` parity: every fast declaration uses the reference
  `FeatureVersion.derive(feature_spec)` identity.
- Provenance: `materialize_pack()` records `producer_engine_id =
  alpha_system.features.fast.pack_materializer.v1` and
  `value_schema_version = alpha_system.features.fast.values.v1` in the
  value-store wrapper.

No per-row values, Parquet files, SQLite registries, provider data, or raw /
canonical data are included in this report.
