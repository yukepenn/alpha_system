# liquidity_sweep_pa_structure Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P10`
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

## Liquidity / PA Primitive Bindings

- `prior_high_low_sweep` binds to prior-boundary distance plus
  sweep-high and sweep-low flags.
- `close_back_inside` and `failed_breakout` bind to failed-high and
  failed-low breakout flags.
- `wick_rejection` binds to close-location and wick-rejection scores.
- `displacement` is represented by the existing causal prior-boundary
  distance and close-location primitives; no new displacement feature
  is introduced.
- `compression_breakout` is represented by existing range-contraction
  plus sweep flags; no new compression-breakout feature is introduced.
- All bindings are deterministic OHLCV-derived primitives emitted at
  the current row `available_ts`; subjective/discretionary PA encodings
  are forbidden.

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
| `ES` | `fver_b7da756ecd315a4a6ac0c926c287bd0062ff6c927459dec91f14c5f40f7fd8a3`, `fver_637b9e8d5e288372943e8b90b7b349b60c7d7c24a2903c22d0b3e1820f0acab4`, `fver_0edbfa0de1d46b5f79fe4d3f4f6f5e743a730bce27e9710cca438e1a1e0a6d07`, `fver_102960ed42eff43f016b1f606d45fe560a6b4c83b2dd9a90b96fe7189ed20339`, `fver_55e8d7592a7f9aaf6fdc820ff3d6babe73d2924f245e8322df907759cc1d5d8b`, `fver_e46f6bf0051958e240da9b8eab0d2d9709e52dea5015fdcced6a1e8e7945133b`, `fver_678cbd71b2728705b216df86a32462481fddfe6f294233bb29a449b7eaf1c533`, `fver_70e8739c60778bd1ed870d176cd55c001b844a62f8205a6ca584f32ea6e0a4cc`, `fver_b74348e7ef12e1a0e520fc3783f31dcbd331df123e6b5ced9d2bd4657951fa2d` |
| `NQ` | `fver_40ee0cd00f40f3ba989b3aabc9bb67553fe158ae9dabb619a2942c1b50fe7e84`, `fver_d6a744eb56a9670a156ec02defcbccb86d78bd4165c1e9955ae4e108a98c5f31`, `fver_101819071b86c94a4b9c1ca7e1f0a24656f823afcf3e7b58cb207a48a76919cb`, `fver_31acdaeaf9f0f9ede1b54bd3241c29dd14fa1856e4fc12554d8010c654c884a4`, `fver_7059e0634cbf888e1f9811f7d1dead69337d0e358e26def648bc918057137029`, `fver_205a376903b84596339df85c386650424f21ae84c6ec393a576ab911f4459674`, `fver_cd48bdbaa04611070249f0a51c5a0bb453c1b5e0a8de5ae770f7414dd2971115`, `fver_84d949ca750065523cd9ab692433ac7e0213b7d1483dd5b1c1ef55be47fbf6f2`, `fver_438108a7ac44ff0275a3960a83421964cf54ec631a57832b589f47b9261416b3` |
| `RTY` | `fver_0d576a299646236b053e83d18d7687307c6a78006c3265058a3cb71dad7d8280`, `fver_7f85e6786f622a21a7b78b079bff7102c0b099b16f8ee965098d7c0478f595bf`, `fver_ed5c997291079def1c677891cd39d2edb49bf7e20f8a9702f9009b7fbca0e40e`, `fver_b4ede4f2aeebad0307b5d6138bb504c07f21eebeeaa65a07f2769e60eb5cfbff`, `fver_54e0acc8c566915545adabc6a6647d5e53513e443542e05dc2299760fc14fd69`, `fver_1336826eba73bad28b2fcc863cd8b4ff0278854abc43f7d545529eae8f65c0e9`, `fver_cccbd7344dc2d6e53ade2f5bf693d9a24b88f116d78e30bf0a9256083025763b`, `fver_b1d7a4e7a781451885e0969a5bbb41421de412e2d85992d7da3593ad2d5ff4f1`, `fver_4d14f83c716c223f364bf3a47ea2a928dde5fe49ce2419c3b1528a6e9a26fa69` |
