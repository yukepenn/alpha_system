# base_ohlcv Scaleout Summary

Value-free FUTSUB-P06 summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P06`
- Rollout: `full-window`
- Dry run: `yes`
- Accepted unit count: `24`
- Bounded-real year: `2024`
- Bounded-real unit count: `3`
- Planned: `24`
- Completed: `0`
- Skipped: `0`
- Failed: `0`

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

## Unit Outcomes

| Stage | Year | Symbol | DatasetVersion | Status | Rows |
| --- | ---: | --- | --- | --- | ---: |
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `planned` | 0 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `planned` | 0 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `planned` | 0 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `planned` | 0 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `planned` | 0 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `planned` | 0 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `planned` | 0 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `planned` | 0 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `planned` | 0 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `planned` | 0 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `planned` | 0 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `planned` | 0 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `planned` | 0 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `planned` | 0 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `planned` | 0 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `planned` | 0 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `planned` | 0 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `planned` | 0 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `planned` | 0 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `planned` | 0 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `planned` | 0 |
