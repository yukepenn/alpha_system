# regime_volatility_compression Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P09`
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

- Family: `regime_volatility_compression`
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
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 1747660 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 1749225 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 1644205 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 1748040 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 1744645 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 1690425 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 1766815 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 1766965 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 1699475 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 1770595 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 1770560 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 1725810 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 1765765 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 1766790 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 1712180 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 1734290 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 1734960 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 1667700 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 1722805 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 1722645 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 1667785 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 703195 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 703050 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 692965 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_7ec915567dc27afe767adc6a6d588dff5f03e5a805cfc3f606fa9edcac3af4f6`, `fver_01b55b064ce54ec0f3757fb2befd4316c6ecdd3cb54dfff6c29914be486f04db`, `fver_91454e766dfd05f9271a9546d2ea9d52d655e2f0b23437b8498092603adb3a8f`, `fver_27b2ba8d4791ec25a4d351026bc0a6df344188ad392ec265c21d77be0e38eb74`, `fver_bb016b77709e32d912ec2c35b1b3a23fc024a5c18c3b29dc0dddd8ddb033be5b` |
| `NQ` | `fver_6fb6d5f709baf837fcbca867468e149c34c861cd2d91942956a98646bee51c41`, `fver_9a0098e04fb4210c214ffa585a199653210317b92677118f2dee174c0ad9d611`, `fver_1020629606f8813f4c196d465e5bcf55531441263e2b21f6eb10bc53a86d8e9a`, `fver_77b8dccdd7ff6346f732aac58c5b0e3b4aab5c86c1ecc51315d32c8a8afc2170`, `fver_45b9368c5bf75420427be641a6468c62c7b503eeddf6e5130121335bb118b948` |
| `RTY` | `fver_ed3c0907584c226f1373a4f2b1d5b4a9eaa0db13094821662cb91e138145057e`, `fver_d99e222cab3828b7bbdb0a15d16975c91bba9c1450556aaccc828137c27e2ea6`, `fver_a1d49a0037912b29e7a33b156214b5540b6d4942349e44df2fc144ab5110dcb4`, `fver_9e03f905275b600b1ce1a3d6e8182535639a6ab68a69015765094485fb0778a4`, `fver_32a511e5f0336e70c1349a0c586d20fa6395139ea3bfea63f1d7e14c066257f8` |
