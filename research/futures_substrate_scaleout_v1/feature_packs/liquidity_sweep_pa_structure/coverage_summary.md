# liquidity_sweep_pa_structure Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P10`
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

- Family: `liquidity_sweep_pa_structure`
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
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `skipped` | 3145788 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `skipped` | 3148605 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `skipped` | 2959569 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `skipped` | 3146472 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `skipped` | 3140361 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `skipped` | 3042765 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `skipped` | 3180267 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `skipped` | 3180537 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `skipped` | 3059055 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `skipped` | 3187071 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `skipped` | 3187008 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `skipped` | 3106458 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `skipped` | 3178377 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `skipped` | 3180222 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `skipped` | 3081924 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 3121722 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 3122928 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 3001860 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `skipped` | 3101049 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `skipped` | 3100761 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `skipped` | 3002013 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `skipped` | 1265751 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `skipped` | 1265490 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `skipped` | 1247337 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_36830860325ed3dd849a9224e498e2c0bf693513a6df7b206f64772f2970c965`, `fver_7c61edb9bdf84b7e1635811a9c913a6acc87826de64b3ffbd88ffcf6895faf20`, `fver_0f049562a3598b2bc9a702c56b589360d3c3c3f6709dddb062343f1689f5706d`, `fver_125b17c3dfcd5ea043907e15486a390bdb88dd326b18cf4afc6837f254f17cfd`, `fver_4ddce8ae65388f465f7bc50d92cd11b9803316744d79cf2bbd9e8924c45405be`, `fver_f3fc632f503d7520cb1037990b290d291ebb6631b7ed1ba61dab05bcedf189b4`, `fver_112edf3ee4994d9b63a1a6524827a17af52a7d18d4cc13a6726b458ac104ce3d`, `fver_331fc9a9c71efebf8892155667eda7f1117be247d3705b9a34ac7ca710a54217`, `fver_8ad55e0f86172ba44f0aae4b9f11fc87bf32a67ae9b7f7db13e798fe2a85f1f9` |
| `NQ` | `fver_4fef62caf81ea76a15364d7b6a768335e50491333004b224eb444cfa2550c081`, `fver_dea163c73e8bcd2e1ab8b8b3d16f59ba147d3da1e819ac5a98e44b2a13fda35a`, `fver_77d19de41b650811f87e8d9c79a853532e1a950e874d91e65843d7a64bc66f81`, `fver_aa2ab8a7288fb677e5047d90e3241f9a1f99ccdb0e1da388df0cad976ac219cb`, `fver_c63ffb857ec0a005ac7658d1f7416230861f92381bd9b950a9c28b9d4ea2fc17`, `fver_4a9971dcff18e512adc26b0a8e9dcdd4ad7f7f20610a05adabf326711feaac1d`, `fver_3b8c62ac63a9333376feca0f97592032bf872709e20c380c2330e75cdfc62c50`, `fver_370608ae19e3eced736fbb735d84cffeff2b520762f01253d364c68fe1d32ed6`, `fver_eccfa1cd5cec13bfbed344513d9f8afe171a68358c3b7a71daa33e6985a59237` |
| `RTY` | `fver_c6617ef6867373249b070795d7272780eed858c64c9313f81ac8761a21354db5`, `fver_a12121f4b0cbd50e4ed59971ad52b02ea998717724dfe275d9bd97474333b2ba`, `fver_2618abc4a99ef580eb090aa7f2414be2db08447d2bf5865d83bf89984b6a6333`, `fver_cfbe13df1b56951537425169c9b07d63283e14ee313ae0d32055ce19e15d2cd6`, `fver_681a8b3bc00477b8504cced28955b5d8b7f8c2b60b4bc1ec20a54d8d934fc297`, `fver_d188f59a592c67dc4a00d6ae86cbbcdaf2cbe5f60323b92dd8db4c2230569b22`, `fver_680e1c7474ce5d9b31d64e38797a27208db63d512f750e1dc239ee42ef190cb2`, `fver_a37dfb5c97d7fd06c5b1f85f87fd11829881d96c92752d1d1916fe7b6c95363f`, `fver_67ebc54541d633d09904b652c896162e431d0ed48427c7af6781146283536987` |
