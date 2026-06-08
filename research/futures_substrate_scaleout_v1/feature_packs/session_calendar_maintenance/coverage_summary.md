# session_calendar_maintenance Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P07`
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

- Bounded-real execute command was attempted after the dry-run preview.
- Result: environment blocked before materialized values or registry rows were
  written because `$ALPHA_DATA_ROOT/materialization` is read-only to this
  executor sandbox.
- Full-window execute was not run after the bounded-real environment block.
- Parquet paths, value content hashes, registry row counts, and checkpoint
  completion markers are therefore unavailable from this executor run.
- The dry-run identity preview is symbol-scoped through the FeatureSpec
  `input_scope` (`symbol`, `partition_id`, `partition_schema`), so ES/NQ/RTY
  do not share FeatureVersion ids for the same year.
- Ralph owns any unsandboxed rerun, staging, review, and phase verdict.

## Acceptance States

| State | Unit count |
| --- | ---: |
| `ACCEPTED` | 21 |
| `ACCEPTED_WITH_WARNINGS` | 3 |

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

## Bounded-Real Identity Preview

The 2024 bounded-real dry-run preview produced symbol-scoped FeatureVersion ids.
No content hashes are listed because the bounded execute attempt was blocked
before Parquet value writes.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_e3d63c8083ca7d772a242e126573ed572024fc0d96160705d8eee1acc140e32c`, `fver_923297bcb23477c00413b2be6bc3a8f6324625a7cde9da7c49df7d5630f3d776`, `fver_8614c506d972bc853b65c72b9ed14a60466221044ade29e2368f47bb3e961824`, `fver_ee89e3878f0fb8c710780ead45f95bc7293c8e4a48f239f37c5c0cb1f12d44c1`, `fver_43644a1f66ac329567d881d3d2d8ff2e1169983c60bbcd0149b729e49eaa6c94`, `fver_d8e8044691a541c3bfd612ce8a9fc85085e390e766be8955b3814a65431e30b3`, `fver_d31ce177589e47a76f917b18dbd630c76b3d6c4ea81e7bbf87da860738d51b0a`, `fver_4c9619e8537b90e0b25d19bf836448d05140426dd5b94270f5fc6e9e4de6def3`, `fver_6bbdb6fd8a877daf877e4a8ffe5c7f7cab286443a1e2e44466b8d31e7e69ddca`, `fver_8cbbe2f71841a536ff644e49d28a6ad00925e575ec08272ed4eb67e926b77d9a` |
| `NQ` | `fver_ea367c3ea9d84a7f065c2460ef21f46551ad2b30a5d9b784d1ad8f7783ae4731`, `fver_3eb3605acc5f8a79c42347b3c9022c5ccc6b5fee1de664f0d39f3694f0c02cec`, `fver_98538959aee114de50454e56a5fb86d69801a89b008b68a2926be479de2f4fff`, `fver_0125aa635e0a991a58ca58f5aa1d7c192a34623909f9f9f0f5781175f8286c62`, `fver_95e1897c95cec1ee6fe52eb45d6454420770e4bfdb100e8ee3a075a84f565d16`, `fver_3effda3c5876e70b8707236fcb595626dc2a5941d81a6cbe1483126dace7b4eb`, `fver_2ffb2b6482a497eaa959a670ea75ebedf9d2f427a11b518338480d8c48476170`, `fver_8ad3c663965a767ad63ee6f9d704aece5a51a254d688095ca33fea6e6a641e12`, `fver_e27a5d4a5e7595ddd619cf996e97e8a9914682f72f111401fe43c02b41b82e7c`, `fver_ffda3eaa928a1aeb421a1d0a08fb89aa4b8173c728ab2ef45b01becf5884a09b` |
| `RTY` | `fver_b0f9486b8486b0fcdc680e3be2c580b95c1efe20030cbbb86a55e8acbf8df5ea`, `fver_b666480c8813d0cd35fffa5cb2a79e13a7c7dd1c7b80269630e1c1209ef348c8`, `fver_44d8569b78ce408f88c5222d2d04438544f3b5d37b5a8f269b0136a326095e5f`, `fver_fe032bcbf4a9ece7a0b16c119fc5b621254431f74a1f8e760bb6c0c669e8aaa1`, `fver_ce94c49767fcbe549d58341b2f343ad539dfb8cd223cbfe42fdd9bc5d02019bb`, `fver_e0053b466aebadf8804ab4fabdb13b8d8b69747ac5f5d57ea685d08d09d7d193`, `fver_d954f3bbc6b29cd672315a275351bfc352d436d233869971692e06a1da47653c`, `fver_98b349ea5126ee9fc7776f6d1992bcc7828d52af0d4ff7863a3924b153967768`, `fver_ba7961b8dafb0e8bf2324281156f7a114d8e449a737dbde929db2e1e2fc20de1`, `fver_de84c0766000685e5af391463d09a6036acd37e7b1e124076c88a5c45f7f21da` |

## Unit Outcomes

| Stage | Year | Symbol | Primary DatasetVersion | Input DatasetVersions | Status | Rows |
| --- | ---: | --- | --- | --- | --- | ---: |
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `planned` | 0 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `planned` | 0 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `planned` | 0 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `planned` | 0 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `planned` | 0 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `planned` | 0 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `planned` | 0 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `planned` | 0 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `planned` | 0 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `planned` | 0 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `planned` | 0 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `planned` | 0 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `planned` | 0 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `planned` | 0 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `planned` | 0 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `planned` | 0 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `planned` | 0 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `planned` | 0 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `planned` | 0 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `planned` | 0 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `planned` | 0 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `planned` | 0 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `planned` | 0 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `planned` | 0 |
