# session_close_maintenance_flat Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, label values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P18`
- Engine: `reference`
- Rollout: `full-window`
- Dry run: `no`
- Targeting active: `no`
- Accepted unit count: `48`
- Bounded-real year: `2024`
- Bounded-real unit count: `6`
- Planned: `0`
- Completed: `48`
- Skipped: `0`
- Failed: `0`
- Requested workers: `1`
- Effective workers: `1`
- Threads per worker: `16`

## Target

- Family: `session_close_maintenance_flat`
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
| `ACCEPTED` | 36 |
| `ACCEPTED_WITH_WARNINGS` | 12 |

## Window Policy

- Eligible DatasetVersion states are `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.
- Dataset-level fallback is used for 2018: the blocked 2018 `ohlcv_1m`
  DatasetVersion is excluded rather than fabricating per-symbol acceptance.
- 2019 warning metadata and 2026 partial-year warning metadata are preserved
  through the accepted/warned DatasetVersion state.
- Multi-input units require every configured input schema/year to carry an
  accepted or accepted-with-warnings DatasetVersion before execution.

## Point-In-Time Guard

- Feature values are emitted at the current source row `available_ts`;
  label values carry `label_available_ts` at or after the forward terminal.
- Rolling, expanding, prior-boundary, and derived-state inputs may use only
  source rows whose `available_ts` is less than or equal to the output
  `available_ts`.
- Accepted DatasetVersion gates fail closed before canonical rows are
  loaded or values are written.

## Unit Outcomes

| Stage | Year | Symbol | Primary DatasetVersion | Input DatasetVersions | Status | Rows |
| --- | ---: | --- | --- | --- | --- | ---: |
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `completed` | 332447 |
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `completed` | 343475 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `completed` | 332753 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `completed` | 343778 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `completed` | 312279 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `completed` | 323130 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `completed` | 332472 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `completed` | 343501 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `completed` | 331823 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `completed` | 342848 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `completed` | 321169 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `completed` | 332157 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `completed` | 333349 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `completed` | 347266 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `completed` | 333351 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `completed` | 347293 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `completed` | 320533 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `completed` | 334055 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `completed` | 333230 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `completed` | 347989 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `completed` | 333222 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `completed` | 347982 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `completed` | 324485 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `completed` | 339233 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `completed` | 331491 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `completed` | 347026 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `completed` | 331676 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `completed` | 347228 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `completed` | 321237 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `completed` | 336491 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `completed` | 326040 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `completed` | 340740 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `completed` | 326169 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `completed` | 340869 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `completed` | 313015 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `completed` | 327671 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `completed` | 323800 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `completed` | 338379 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `completed` | 323769 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `completed` | 338347 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `completed` | 313012 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `completed` | 327551 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `completed` | 132979 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `completed` | 139039 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `completed` | 132950 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `completed` | 139010 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `completed` | 130942 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `completed` | 136996 |
