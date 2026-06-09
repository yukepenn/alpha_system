# session_calendar_maintenance Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P07`
- Engine: `v1`
- Rollout: `full-window`
- Dry run: `no`
- Targeting active: `no`
- Accepted unit count: `24`
- Bounded-real year: `2024`
- Bounded-real unit count: `3`
- Planned: `0`
- Completed: `0`
- Skipped: `24`
- Failed: `0`
- Requested workers: `4`
- Effective workers: `4`
- Threads per worker: `4`

## Target

- Family: `session_calendar_maintenance`
- Feature ids: `config default`
- Feature groups: `none`
- Label ids: `none`
- Label groups: `none`
- Symbols: `config default`
- Years: `config default`
- DatasetVersion ids: `accepted grid default`

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

- Feature values are emitted at the current source row `available_ts`.
- Rolling, expanding, prior-boundary, and derived-state inputs may use only
  source rows whose `available_ts` is less than or equal to the output
  `available_ts`.
- Accepted DatasetVersion gates fail closed before canonical rows are
  loaded or values are written.

## Unit Outcomes

| Stage | Year | Symbol | Primary DatasetVersion | Input DatasetVersions | Status | Rows |
| --- | ---: | --- | --- | --- | --- | ---: |
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `skipped` | 3560400 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `skipped` | 3560400 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `skipped` | 3560400 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `skipped` | 3573000 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `skipped` | 3573000 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `skipped` | 3573000 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `skipped` | 3574200 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `skipped` | 3574200 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `skipped` | 3574200 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `skipped` | 3560400 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `skipped` | 3560400 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `skipped` | 3560330 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `skipped` | 3560400 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `skipped` | 3560400 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `skipped` | 3560400 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `skipped` | 3470850 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `skipped` | 3470850 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `skipped` | 3470840 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `skipped` | 3457050 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `skipped` | 3457030 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `skipped` | 3457000 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `skipped` | 1406400 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `skipped` | 1406400 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `skipped` | 1406400 |
