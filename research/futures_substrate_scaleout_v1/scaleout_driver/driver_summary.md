# base_ohlcv Scaleout Summary

Value-free FUTSUB-P06 summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P06`
- Rollout: `bounded-real`
- Dry run: `yes`
- Accepted unit count: `24`
- Bounded-real year: `2024`
- Bounded-real unit count: `3`
- Planned: `3`
- Completed: `0`
- Skipped: `0`
- Failed: `0`

## Acceptance States

| State | Unit count |
| --- | ---: |
| `ACCEPTED` | 3 |

## Window Policy

- Eligible DatasetVersion states are `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.
- Dataset-level fallback is used for 2018: the blocked 2018 `ohlcv_1m`
  DatasetVersion is excluded rather than fabricating per-symbol acceptance.
- 2019 warning metadata and 2026 partial-year warning metadata are preserved
  through the accepted/warned DatasetVersion state.

## Unit Outcomes

| Stage | Year | Symbol | DatasetVersion | Status | Rows |
| --- | ---: | --- | --- | --- | ---: |
| `bounded_real` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `bounded_real` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
| `bounded_real` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `planned` | 0 |
