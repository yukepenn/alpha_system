# vwap_session_auction Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P08`
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
- Multi-input units require every configured input schema/year to carry an
  accepted or accepted-with-warnings DatasetVersion before execution.

## Point-In-Time Guard

- Session metadata is treated as `SESSION_METADATA_POINT_IN_TIME`.
- Row-specific metadata with an explicit metadata availability timestamp
  later than the row `available_ts` fails closed.
- Static RTH clock parameters are schedule definitions, not future labels;
  optional expiration/status metadata is never fabricated when absent.

## Running-Vs-Final VWAP Discipline

- Running VWAP and distance-to-VWAP are computed as expanding
  point-in-time state keyed to each row `available_ts`.
- Anchored ETH VWAP starts from the ETH anchor and carries forward only
  rows already available at the output `available_ts`.
- Final-session VWAP, full-session value area, and closing-auction
  aggregates are not bound into intraday feature values.
- Opening and overnight ranges update or freeze only after the source
  rows needed for that point-in-time range are available.

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
| `ES` | `fver_ec9a7ee9a57170ccd0619091f12aa0bdee7fd165b5ee4d6cc09a1dae3ac81518`, `fver_8e7ff53d4b6d28e02145e3f3ee9a012367e56d56865d6e03757f190ef99ed3b9`, `fver_46515d5072636cf7863957f17797a8adeea7fc0842478515d036e51f13419775`, `fver_298f943de06937e149bbe6d07cc3dc431e2f98f092805c50c4bdc55cc8804eeb`, `fver_7a7907e75074e0383df821745651dd17f0e55de3a29fd2116b87e51589185122`, `fver_a8c25e26c130100941d9c0ea842a1eab6aa7ccb336d0cdba20b424b220b5f9c4` |
| `NQ` | `fver_a292b0338513a1575b224fa73c814d88a2187821964d0de5e0f2fb9deb6d3104`, `fver_ab5f9f0298015c8ba2198b2526e2848ce2016281b7e9357a71e0401168e16151`, `fver_79ce0f548ee632ca5133544e64d723b452c15408c774b4dc77ac457330cac032`, `fver_c5925aa978a091541eb4fbdfd7af1ba3fa6387ec88fe9eaa632ea199bae1c8c4`, `fver_3e6410e0ddf16c26d697dc4652779d45ea3756e566c715d430727e9824226010`, `fver_27dadb0aafd6fd2512405ba1a93995d3f273cc111ebfbc85893cf61636048597` |
| `RTY` | `fver_79cd1b684e4f3c81ce1cd128e729537c22958db50467d76188e4dc96ef577c90`, `fver_c6814f08cefcfbb442fc8d28153da10654d0735ab28469dba59a569061e6badd`, `fver_38af82217bfa9deb1c1a91215e440f1d9a94b94ccfaf5290fe36cc92c0244c39`, `fver_203ced37575995aa1cca3f32e999ffb85dd3de9ad16b9a4274666f0b32672f53`, `fver_6b88f455e822004fd77ca1b63263d0123765867dad717fe92c308918ade2a042`, `fver_0a3a5a9902a8515e99ea4be218bf9a16801d4bc34fff6df76f6cb3ab5cad71f0` |
