# cross_market_alignment Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P13`
- Engine: `v1`
- Rollout: `full-window`
- Dry run: `no`
- Targeting active: `no`
- Accepted unit count: `8`
- Bounded-real year: `2024`
- Bounded-real unit count: `1`
- Planned: `0`
- Completed: `0`
- Skipped: `8`
- Failed: `0`
- Requested workers: `4`
- Effective workers: `4`
- Threads per worker: `4`

## Target

- Family: `cross_market_alignment`
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
| `ACCEPTED` | 7 |
| `ACCEPTED_WITH_WARNINGS` | 1 |

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
| `full_window` | 2019 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2019_v1` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2019_v1` | `skipped` | 3916440 |
| `full_window` | 2020 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2020_v1` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2020_v1` | `skipped` | 3930300 |
| `full_window` | 2021 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2021_v1` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2021_v1` | `skipped` | 3931620 |
| `full_window` | 2022 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2022_v1` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2022_v1` | `skipped` | 3916363 |
| `full_window` | 2023 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2023_v1` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2023_v1` | `skipped` | 3916440 |
| `full_window` | 2024 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2024_v1` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2024_v1` | `skipped` | 3817924 |
| `full_window` | 2025 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2025_v1` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2025_v1` | `skipped` | 3802700 |
| `full_window` | 2026 | `ES_NQ_RTY` | `dsv_databento_ohlcv_dense_2026_v1` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b, ohlcv_dense_research_grid:dsv_databento_ohlcv_dense_2026_v1` | `skipped` | 1547040 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES_NQ_RTY` | `fver_65bc052a7d8372b90322a2c69013d29317a5ea4e22cc94961fca784eb8d86b1a`, `fver_6ae9a54d4cd0b08add3b635e2ec3fa4014625383fe9d7018d2d2a162a5c9ceda`, `fver_09e6ce6480f6c22aae71145ef115a573ac8cff09197d9eae71b509acee660fa3`, `fver_921a962a906efaadd2c7812610679dc987a76c95c5fb76b46ac82914a2cb999b`, `fver_693704d36430cf7ff842b57ec78d87f5be9e6692f19a81e3cda15fadf94529d1`, `fver_bacd82e2b2a873ca162859e15d22634bc7d350fd8d3cc3f9c418b449d37dc64c`, `fver_9ed797cf41de2d25c7add5ad1de37ff12e6df6fc7146ccdfdf84ba9197c54475`, `fver_b9d318eb8342a911c191d0622b869d17255702b3183351a0bb45fdeb0e0c31aa`, `fver_6e8aa35cc88f66165273f56c006e89dcb024e4ffb84dc7191731839c481c7b3e`, `fver_5f27368f8a583e5b2e19650eff63d2c6815bee9eccdf594eae2fcb5b8c0783d3`, `fver_c7124d0bc9192f838a763dd02a284a79dfbb8b032123a0033118d3e6b1c3af9e` |
