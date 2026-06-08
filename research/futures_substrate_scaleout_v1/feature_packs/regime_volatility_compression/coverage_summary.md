# regime_volatility_compression Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P09`
- Rollout: `full-window`
- Dry run: `yes`
- Accepted unit count: `24`
- Bounded-real year: `2024`
- Bounded-real unit count: `3`
- Planned: `24`
- Completed: `0`
- Skipped: `0`
- Failed: `0`

## Executor Materialization Attempt

- Bounded-then-full execute command was attempted after the dry-run preview.
- Result: environment blocked before materialized values or registry rows were
  written because `$ALPHA_DATA_ROOT/materialization` is read-only to this
  executor sandbox.
- Full-window expansion was not reached after the bounded-real environment
  block.
- Parquet paths, value content hashes, registry row counts, checkpoint
  completion markers, and observed materialized `available_ts` min/max are
  therefore unavailable from this executor run.
- The dry-run identity preview is symbol-scoped through the FeatureSpec
  `input_scope` (`symbol`, `partition_id`, `partition_schema`), so ES/NQ/RTY
  do not share FeatureVersion ids for the same year.
- Ralph owns any unsandboxed rerun, staging, review, and phase verdict.

## Acceptance States

| State | Unit count |
| --- | ---: |
| `ACCEPTED` | 18 |
| `ACCEPTED_WITH_WARNINGS` | 6 |

## Window Policy

- Eligible DatasetVersion states are `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.
- Dataset-level fallback is used for 2018: the blocked 2018 `ohlcv_1m`
  DatasetVersion is excluded rather than fabricating per-symbol acceptance.
- 2019 warning metadata and 2026 partial-year warning metadata are preserved
  through the accepted/warned DatasetVersion state.
- Multi-input units require every configured input schema/year to carry an
  accepted or accepted-with-warnings DatasetVersion before execution.

## Point-In-Time Guard

- Session metadata is treated as `SESSION_METADATA_POINT_IN_TIME`.
- Row-specific metadata with an explicit metadata availability timestamp
  later than the row `available_ts` fails closed.
- Static RTH clock parameters are schedule definitions, not future labels;
  optional expiration/status metadata is never fabricated when absent.

## Regime Primitive Bindings

- `trendiness` binds to the existing `base_ohlcv_trendiness` primitive.
- `atr_volatility_regime` binds to the existing `base_ohlcv_atr` primitive.
- `range_compression` binds to the existing
  `liquidity_structure_range_contraction` primitive.
- `range_expansion` binds to the existing `base_ohlcv_rolling_range` primitive.
- `momentum_reversion_state` binds to the existing `base_ohlcv_returns`
  primitive.
- All bindings use causal windows and emit values at the current row
  `available_ts`; no final-session state or future labels are used.

## Materialized Value Evidence

- This summary is value-free and does not include per-row feature values.
- In dry-run mode, Parquet paths, value content hashes, registry row
  fields, materialized row counts, checkpoint markers, and observed
  `available_ts` min/max are unavailable.
- When `--execute` succeeds, the driver verifies Parquet-backed registry
  rows for `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, and
  `feature_version_id` through `FeatureStore.register_materialized_feature`.

## Unit Outcomes

| Stage | Year | Symbol | Primary DatasetVersion | Input DatasetVersions | Status | Rows |
| --- | ---: | --- | --- | --- | --- | ---: |
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `planned` | 0 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `planned` | 0 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `planned` | 0 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `planned` | 0 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `planned` | 0 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `planned` | 0 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `planned` | 0 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `planned` | 0 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `planned` | 0 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `planned` | 0 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `planned` | 0 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `planned` | 0 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `planned` | 0 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `planned` | 0 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `planned` | 0 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `planned` | 0 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `planned` | 0 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `planned` | 0 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `planned` | 0 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `planned` | 0 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `planned` | 0 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_6722d83ad95c1f5079846ae7b90f5e1a732cec3e620c1b6f10b40281914a5b2c`, `fver_4bbf18503196d5473e47bf5274919ae1d423f2fe88b6235ddc8d52c3f42c61af`, `fver_ec9ec5923241884c1a9f05a6c5f2b2638022339309742f9fbae934e0fcea4574`, `fver_24bc0bd3770e186d473755be74bbfdbae93a236d6d4f701ebe4d899c3b1945a0`, `fver_c3b4540a41e0b524053fd5bcb4f1d0ac7501f576d1458ff13e2be197f25e212f` |
| `NQ` | `fver_da8325f46bed8f7c718cac1ea6816f6ff1f83dd2e554e75f633db1db2650ceeb`, `fver_7f7e4c3b81cafeefea39a214bf5abe5b321f382dbc4ad78ee6498b5a28876f6f`, `fver_bb072d59c9698bded66663e53d04947230818dde1e20a3ef45b2de786b1b0608`, `fver_830ea76019b68f2b113ad86486e61e45c61c5ae23e8acef2128deb8cca072d2f`, `fver_8074bf5207261f6663201fdb4e4343be44bc422975414f6e5df5237af1617bbd` |
| `RTY` | `fver_87ab8dd1f96af560233d2cc76f57e4bf47a522a2c200b6b754b7d1c779d8d97e`, `fver_6dbc330f3eff37f41993b63129404e91a73c8ed731db00fa3be748b2be355a6d`, `fver_9447640bf09065bd1c5f8fd71d6aa42ed6a363e734c49912511cc81cfcda3f27`, `fver_59c2c94ead9c1f6e148010fd595dc19e0dfebca4c9b2c239b41ceace0638e4f9`, `fver_72102fd8def4e4e5431917f8fb738a51737019699a3fc2a87868f6330db62637` |
