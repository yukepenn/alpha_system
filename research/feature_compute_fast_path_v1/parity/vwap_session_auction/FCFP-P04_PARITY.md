# FCFP-P04 VWAP / Session-Auction Parity Report

Value-free synthetic-fixture report for the V1 `vwap_session_auction` Polars
pack.

## Scope

- Campaign: `FEATURE_COMPUTE_FAST_PATH_V1`
- Phase: `FCFP-P04`
- Pack: `vwap_session_auction`
- Fixture: `tests/fixtures/feature_compute_fast_path/vwap_session_auction.py`
- Rows: 12 synthetic OHLCV rows
- Parameters: `opening_range_minutes=2`, `anchor_session_label=RTH`,
  `reset_on_session=True`
- Tolerance: `1e-12` absolute / relative for `vwap`, `anchored_vwap`, and
  `distance_to_vwap`, justified by cumulative floating-point VWAP summation.
  `opening_range` and `overnight_range` are exact.

## Results

| Feature | Rows | Valid value pairs | Gap rows | Max abs diff | Median abs diff | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `vwap` | 12 | 6 | 6 | 2.842170943040401e-14 | 7.105427357601002e-15 | within `1e-12` |
| `anchored_vwap` | 12 | 5 | 7 | 2.842170943040401e-14 | 0 | within `1e-12` |
| `distance_to_vwap` | 12 | 5 | 7 | 2.8059152223924855e-16 | 1.4051260155412137e-16 | within `1e-12` |
| `opening_range` | 12 | 5 | 7 | 0 | 0 | exact |
| `overnight_range` | 12 | 9 | 3 | 0 | 0 | exact |

## Contract Checks

- `available_ts` parity: exact for all five features.
- Gap-row parity: exact, including `no_trade`, `zero_volume`,
  `before_anchor`, `outside_rth`, `no_opening_trade`,
  `no_overnight_trade`, `no_overnight_range`, and `zero_vwap`.
- Quality-flag parity: exact, including reference ordering.
- Session and anchor behavior: session-reset VWAP, RTH-anchored VWAP reset,
  opening-window boundary exclusion, ETH-to-RTH overnight carry, and the
  reference overnight session-label carry are covered.
- `feature_version_id` parity: every fast declaration uses the reference
  `FeatureVersion.derive(feature_spec)` identity.
- Provenance: `materialize_pack()` records `producer_engine_id =
  alpha_system.features.fast.pack_materializer.v1` and
  `value_schema_version = alpha_system.features.fast.values.v1` in the
  value-store wrapper.

No per-row values, Parquet files, SQLite registries, provider data, raw /
canonical data, feature values, label values, or heavy artifacts are included in
this report.
