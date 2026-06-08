# cross_market_alignment Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P13`
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

## Cross-Market Alignment Guardrails

- Cross-market materialization uses exact event-timestamp intersection
  across ES, NQ, and RTY.
- Output `available_ts` is the latest contributing per-instrument
  availability timestamp for the same event timestamp.
- Cross-instrument forward-fill and missing-instrument imputation are
  forbidden; missing instruments or no-trade rows are surfaced as
  gaps or excluded intersections.
- The config labels bind to existing governed Cross-Market primitives;
  no new cross-market feature formulas are introduced in this phase.

## Cross-Market Primitive Bindings

- `aligned_returns` binds to `synchronized_returns`.
- `beta_residual` binds to NQ/ES and RTY/ES rolling beta residuals.
- `basket_residual` binds to NQ-minus-ES and RTY-minus-ES return spreads.
- `relative_strength_rank` and `catch_up_rotation` bind to existing
  risk-on/risk-off rotation proxies.
- `divergence_agreement` binds to confirmation and divergence flags.
- `lead_lag` binds to existing NQ/ES and RTY/ES rolling correlations as
  governed pair-state proxies; it does not introduce a new lead-lag
  formula.

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

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_c0cc57f41efa92eb392e0461fe35287491fd4df8f30c9b066afa428f8c5aa942`, `fver_c3af14eed11e162b909705d86fc962f7113512398edcbb83312281da4f6446f4`, `fver_8a435cf445eb62dcbf1438373494a62b76dd12abb64d37a3a22f36faaa8116c8`, `fver_d28e0e4137155bcac62cbc1040d95d9a21a36b4548ce13822eaeb3ee7e124441`, `fver_44dd0b39553d8b93ae9fb1e1437546b9a35d1a0204f07d22fd780f7b696f2340`, `fver_8a58244f4ac9c18e48ac5bc3ee424180673f30582edf440c060bc7f69bb1d62e`, `fver_ee7c9b033e3e60a0f9b52547bed077f4b8952340ce473764f27967f49bf9f7ad`, `fver_426349f1d505bdd5dac06bb4770b4bdf8e2657e8930a26010cf707985480c598`, `fver_811ece329e3b91115ac4edea9cbe9b157425fcd6b96a52b8b9a3a8156c1d250a`, `fver_00ac18edf1e84fa7600e6a7a42f43bd59a31d97fae26f146dca5070f3937807b`, `fver_394b014f44ad55ac6c8c236967cac7432b5452bd541a2a10d98521ee038fe0c9` |
| `NQ` | `fver_8c97f9b7f1c7c7deec49de2e7acd0917da09816160eaea51e6ed72505d44bff2`, `fver_5461082596865b73eab67c3a6d9d36d48b2072be6d2168e1a81edc7ed798cc2a`, `fver_6464459452207d04a8079d2074c299e29ad9f55e2108295522e2a0dcbf1acd8b`, `fver_b82c54cfa6548716eb873b8d91682ad09d63199ec3be74a10538b8504eab6ff3`, `fver_bb81bdddf712fdc29949c8daf5d0e43064dd02190457c24a57a3f6c3baedd408`, `fver_8b22dedc4ef6fef289bac5c5ab89c87fda65c72b38d08c51c45dc1be2b142d90`, `fver_bcb2f064749dcd7b2e706b154dbbe929239ad84b8831fcd9e7eb02a5ccb530d6`, `fver_f2e323b2d3eb8bc59e3d3a4400f1bd21581873c138d9a9704caa53c91b16ceb2`, `fver_bf2e9e3e59c6504bc4c2129b19802c4fe813c1949617acbf2bce8489c40a14b7`, `fver_f38f7a59bf6a68648de9689b8cf87e4fd9838c3e0c0a268b158018707c4b682a`, `fver_45a58b91b3efe9621b93cceb6749e5ddffbd6432c1473e3b6b3ac8d36b3ee7df` |
| `RTY` | `fver_0d2f4c928ce8a86a82222c0327fc6e1a6c5592383f6ee110b9ebfb9fb20e8e21`, `fver_9c7d7ddf2ae3a0e19a27ccf46977b5b39ff95566ea91e4a78c98b53766f2caf1`, `fver_bdde72d0bfa06e07cea2b58facd3ca6647255de6b8f2360860be7bdb2da260bb`, `fver_ec8bb4c7166c884b717273b08fdd634ad69316a1ac6203eab2ff3bb6a63d7d60`, `fver_abe561927050019e2f5230dc96587bea25a975ed92e608b023aa6c58be9dfa03`, `fver_6f0ba855de43be18115cc0588f1f78c1e279a7d77c427b206f7af09cef3acca1`, `fver_84a176ce7b5d860b1a5be94e09518244978a714d8d058c87d6a40b43319468f5`, `fver_83e3d9d5a92c350de0561dfbddd1d599866b4e1ddf48e1aa269621994008b6f4`, `fver_3684f133c6d4879cc10cba502e9e5152466f90b589220de5d5ce8b6c81e81e0d`, `fver_530f63f5ba4dacd769cb1aac162a759c8c3535977a7ed87e0e2aad14c425437f`, `fver_0579e663e29def7bc39c54c5fccd8bd69ae117bdc444b3d7b764a39ce3e9b608` |
