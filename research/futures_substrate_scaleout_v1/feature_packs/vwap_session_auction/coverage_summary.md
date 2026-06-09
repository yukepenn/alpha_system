# vwap_session_auction Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P08`
- Engine: `v1`
- Rollout: `full-window`
- Dry run: `no`
- Targeting active: `no`
- Accepted unit count: `24`
- Bounded-real year: `2024`
- Bounded-real unit count: `3`
- Planned: `0`
- Completed: `21`
- Skipped: `3`
- Failed: `0`
- Requested workers: `4`
- Effective workers: `4`
- Threads per worker: `4`

## Target

- Family: `vwap_session_auction`
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
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 2097192 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 2099070 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 1973046 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 2097648 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 2093574 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 2028510 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 2120178 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 2120358 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 2039370 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 2124714 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 2124672 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 2070972 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 2118918 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 2120148 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 2054616 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 2081148 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 2081952 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 2001240 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 2067366 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 2067174 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 2001342 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 843834 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 843660 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 831558 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_efa14d9ddb32eb7e68d6ef3fd40162e0df3676a8565e55d29c5356134da8aec8`, `fver_a94c15e9abbfc066cc56fc3d36e9e5b7853765f357dae5d1b218c738bed1335f`, `fver_73775a3f9efe50264531dc03c7f0b5d3d56c55f6eea58a807850a4f303d2daa5`, `fver_e9d27e99685e3817a394ea838f904c50a9ab37a82df9c96a35bef51b79078816`, `fver_5d39378961253bdf6ff344a56b0ad293906b9a8d7c32b44ca7f203666bd4bff6`, `fver_cd79dba79e1f6185b61b0eb7ad3bb0fa8b08457361926f12fd8f88cee0170b5f` |
| `NQ` | `fver_6c1ee121688f628d557abacdfaedfd356bbc3f58935aa286acb393d7fd3a74af`, `fver_712a3b304c1531aeaca5300bb1a59fced9029159ca2205c94ec55d8d69b47920`, `fver_3975807c32e91a0807f4a03033d4486efa529df378135fc51d79014944ee37c7`, `fver_34043733acf8b9409d5eb694aa45b6f07a642cef018140404b4adf1e19dee501`, `fver_c22e9048edb04197c5197df974b12c97571b791106259aee702a2343d8e7753c`, `fver_87d356230ac6b0fc21d57b7fdff88463dfafe9a9dc65a5172ead93eb7cb1549e` |
| `RTY` | `fver_84f360b50751653860eaa5d7d6fffbfeac94d423a7ff8fd3b02f883d40563a4b`, `fver_00315e11d199109b128f78651315231231de90c07bc76da7b925c5321ddd35fe`, `fver_bb889f0b415b1537d118dc835591c01ddec817021b9ec3a78050e01edead47f9`, `fver_67c3395db85cf742d668242348db0a677547ddb1438d873dfba13437e2adaeb4`, `fver_f8d2338fd24b889050a79a9454486e4b9cbeddcfd8b15854b52943559d20ef7e`, `fver_fda4d75f7b8ed0a2551284c5789274b49c995b5b98f0d79080f0cb74512994e9` |
