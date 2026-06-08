# volume_activity Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P11`
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

- Feature values are emitted at the current source row `available_ts`.
- Rolling, expanding, prior-boundary, and derived-state inputs may use only
  source rows whose `available_ts` is less than or equal to the output
  `available_ts`.
- Accepted DatasetVersion gates fail closed before canonical rows are
  loaded or values are written.

## Volume / Activity Primitive Bindings

- `participation` is represented by existing rolling-volume and
  volume-zscore primitives; no new participation formula is introduced.
- `time_of_day_relative_volume` binds to existing volume-zscore plus
  session-minute context.
- `volume_regime` binds to existing rolling-volume and volume-zscore
  primitives.
- `activity_bursts` binds to existing volume-zscore plus rolling-range
  activity context.
- `effort_result_proxies` binds to existing rolling-volume, range-position,
  trendiness, close-location, and wick-rejection primitives.
- All bindings are deterministic OHLCV-derived primitives emitted at
  the current row `available_ts`; no volume feature zoo is introduced.

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
| `ES` | `fver_ccb5d6cce79b1c240eaf39f27ccd515dd1aa94bfc2ee5e563e68ebef2b9e9dff`, `fver_549dcb192f83997cb3012a9456d3d70df7d3cfaf3fa89e1b867a685497435907`, `fver_08e2018de3391f25853e35f73624754ae193e9c5644f85060b1143cfbf57f258`, `fver_ef3fe0bf5a76f5c479d10d056ca1b4898a0fd83bfdd0c83a71a008c3c36dde6f`, `fver_07b45e55ecdd647ccb5e8baffd6d80d17579857c1bf5ab2c7b240e0f1c0f1774`, `fver_98249ec3c303d5064546c0415a18a63a56000dc370a4ac2faafa39604103e067`, `fver_49160cd3f470930e18a0a19351731f09301284e6c962755e9c2a5a2705a11a0f`, `fver_1adb262ab5abeafd8c2ec8347bb0c52ca17e49fa6a7ff8efea175bd672c3b199` |
| `NQ` | `fver_321b4f73c33bf02ffc2b3c0073f676a1c17dfb74aad91676001cb7d05c4aa124`, `fver_7e184c82ea3e99d8ee579a0161f00aec2ae2fc693bdd0fac63e8a8f5df470299`, `fver_234b2decb4f831edb4ad7e4269ed21e66e686f5e9f4acf6c38494e54b4b88ed8`, `fver_081dc7d570f2ed19c5381a4c86410303d73c737eab5c4a8f5daa0eb1db0e4aae`, `fver_56f0e02ff68f352e003dc424f27fa90d9ced04bb3a51856469318a8017e3c7be`, `fver_97eeded66557aa5741ab764f0cc8a8ab15ec7e5cbf8859479f96ef9eb833d25d`, `fver_8828d045c994f4a6904912e2265111a689d66871cf6651e2d646a15ed0f39c8a`, `fver_b24202c7ab7501170c483ee1ad5a60586576a37f7b4ba721cccdfe7bffc4357a` |
| `RTY` | `fver_2797a62c21f3b344ca9af672b5c92336bb87c5126e06fb3e666824aa0b1229c6`, `fver_4d3c0849ce25e01c530dd9297fbc1f31d7200c43e7c0c9be2462ef554e726888`, `fver_a7fad887608351affab7bc51dcef33ffde2f3c78c0dfbe2c8d47e82fd95746bd`, `fver_142631a1af07d4fe108039703315996736e4b5db3e560ba5e062d67a30cc0a83`, `fver_e7d3d7800dc61fd455a53a55e77cdccd86af3981c6be520a7321a27efcc8f87e`, `fver_85bcbfdbb3ba3d562297a5878a480d9de38e7691c07fcbf270ab072da98e0a7b`, `fver_8462697bbea444b4a747f7bba587a2e48881b60645c319b7ffd665e62920cad1`, `fver_5d681934d584e0bf810be675544d8ff5316a0cf589769264fe08e9434f549506` |
