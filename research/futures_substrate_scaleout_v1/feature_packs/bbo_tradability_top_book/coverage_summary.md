# bbo_tradability_top_book Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P12`
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
- Dataset-level fallback is used for 2018: the blocked 2018 `bbo_1m`
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

## BBO Proxy Guardrails

- BBO-1m is treated strictly as a time-sampled and forward-filled
  tradability proxy, not execution truth.
- Passive-fill, queue-priority, market-impact, intra-minute path, and
  execution-quality claims are forbidden.
- Canonical BBO `available_ts` is preserved; no feature is emitted
  before the source quote row is available.
- Missing, quarantined, wide-spread, and low-depth conditions are
  surfaced as flags or value gaps; they are not silently imputed.

## BBO Top-Book Bindings

- `mid`, `spread`, `spread_ticks`, and `spread_zscore` bind to existing
  BBO spread primitives.
- `top_book_depth` and `top_book_imbalance` bind to existing top-book
  depth/imbalance primitives.
- `missing_bbo_flag`, `bad_quote_flag`, `wide_spread_flag`, and
  `low_depth_flag` bind to existing quote-quality flag primitives.
- `microprice_proxy` binds to the existing BBO `microprice` primitive
  and remains a proxy feature, not a fill or execution model.

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
| `full_window` | 2019 | `ES` | `dsv_databento_bbo_f91f510a8d6fa87b` | `bbo_1m:dsv_databento_bbo_f91f510a8d6fa87b` | `planned` | 0 |
| `full_window` | 2019 | `NQ` | `dsv_databento_bbo_f91f510a8d6fa87b` | `bbo_1m:dsv_databento_bbo_f91f510a8d6fa87b` | `planned` | 0 |
| `full_window` | 2019 | `RTY` | `dsv_databento_bbo_f91f510a8d6fa87b` | `bbo_1m:dsv_databento_bbo_f91f510a8d6fa87b` | `planned` | 0 |
| `full_window` | 2020 | `ES` | `dsv_databento_bbo_af9511d169b0aead` | `bbo_1m:dsv_databento_bbo_af9511d169b0aead` | `planned` | 0 |
| `full_window` | 2020 | `NQ` | `dsv_databento_bbo_af9511d169b0aead` | `bbo_1m:dsv_databento_bbo_af9511d169b0aead` | `planned` | 0 |
| `full_window` | 2020 | `RTY` | `dsv_databento_bbo_af9511d169b0aead` | `bbo_1m:dsv_databento_bbo_af9511d169b0aead` | `planned` | 0 |
| `full_window` | 2021 | `ES` | `dsv_databento_bbo_d5cb08f949e7ff28` | `bbo_1m:dsv_databento_bbo_d5cb08f949e7ff28` | `planned` | 0 |
| `full_window` | 2021 | `NQ` | `dsv_databento_bbo_d5cb08f949e7ff28` | `bbo_1m:dsv_databento_bbo_d5cb08f949e7ff28` | `planned` | 0 |
| `full_window` | 2021 | `RTY` | `dsv_databento_bbo_d5cb08f949e7ff28` | `bbo_1m:dsv_databento_bbo_d5cb08f949e7ff28` | `planned` | 0 |
| `full_window` | 2022 | `ES` | `dsv_databento_bbo_7b5595d5030462ab` | `bbo_1m:dsv_databento_bbo_7b5595d5030462ab` | `planned` | 0 |
| `full_window` | 2022 | `NQ` | `dsv_databento_bbo_7b5595d5030462ab` | `bbo_1m:dsv_databento_bbo_7b5595d5030462ab` | `planned` | 0 |
| `full_window` | 2022 | `RTY` | `dsv_databento_bbo_7b5595d5030462ab` | `bbo_1m:dsv_databento_bbo_7b5595d5030462ab` | `planned` | 0 |
| `full_window` | 2023 | `ES` | `dsv_databento_bbo_8772e3b47aa5fb98` | `bbo_1m:dsv_databento_bbo_8772e3b47aa5fb98` | `planned` | 0 |
| `full_window` | 2023 | `NQ` | `dsv_databento_bbo_8772e3b47aa5fb98` | `bbo_1m:dsv_databento_bbo_8772e3b47aa5fb98` | `planned` | 0 |
| `full_window` | 2023 | `RTY` | `dsv_databento_bbo_8772e3b47aa5fb98` | `bbo_1m:dsv_databento_bbo_8772e3b47aa5fb98` | `planned` | 0 |
| `full_window` | 2024 | `ES` | `dsv_databento_bbo_f9e1d70a04d9dae4` | `bbo_1m:dsv_databento_bbo_f9e1d70a04d9dae4` | `planned` | 0 |
| `full_window` | 2024 | `NQ` | `dsv_databento_bbo_f9e1d70a04d9dae4` | `bbo_1m:dsv_databento_bbo_f9e1d70a04d9dae4` | `planned` | 0 |
| `full_window` | 2024 | `RTY` | `dsv_databento_bbo_f9e1d70a04d9dae4` | `bbo_1m:dsv_databento_bbo_f9e1d70a04d9dae4` | `planned` | 0 |
| `full_window` | 2025 | `ES` | `dsv_databento_bbo_35d4417c086be53f` | `bbo_1m:dsv_databento_bbo_35d4417c086be53f` | `planned` | 0 |
| `full_window` | 2025 | `NQ` | `dsv_databento_bbo_35d4417c086be53f` | `bbo_1m:dsv_databento_bbo_35d4417c086be53f` | `planned` | 0 |
| `full_window` | 2025 | `RTY` | `dsv_databento_bbo_35d4417c086be53f` | `bbo_1m:dsv_databento_bbo_35d4417c086be53f` | `planned` | 0 |
| `full_window` | 2026 | `ES` | `dsv_databento_bbo_22c49fbf57cceea6` | `bbo_1m:dsv_databento_bbo_22c49fbf57cceea6` | `planned` | 0 |
| `full_window` | 2026 | `NQ` | `dsv_databento_bbo_22c49fbf57cceea6` | `bbo_1m:dsv_databento_bbo_22c49fbf57cceea6` | `planned` | 0 |
| `full_window` | 2026 | `RTY` | `dsv_databento_bbo_22c49fbf57cceea6` | `bbo_1m:dsv_databento_bbo_22c49fbf57cceea6` | `planned` | 0 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_72e28331ba598c0198691f1b004ee14bb8f49c916b8bce5ad8e4296eb220e1f1`, `fver_22bd3a07d77b51a85154f71ece5df49d4658296e0026f141b19eabd8c767caff`, `fver_86354529dc0a1c2903ee13d9e78595e912ce174cdb8d38081e8818362f540bdd`, `fver_0e492cc195730931a92247b68b9a2a679b24c8ada9f76a242f77a67b4c38a3d1`, `fver_a836cabceaf9b832aa18a9aaf4ae535126fc2bfe156435f26083ae30c99339c1`, `fver_8c4bfdc069eaf0595ccef63b581f72c32ae02f2406e941fa1a204ce45f5575d7`, `fver_22077239555b69ee81bf0dfcf9bc03fe63a38663aa2967f46e85f559eee49837`, `fver_9ee87e3ea14bdb6fa283fb512bbc2eb6e3582d3fdfe9c5eae774cc3e02dc484e`, `fver_ad22b2dc8c52673906416f68325c439e032b67ffe3a188662fe17fc1c929eae9`, `fver_ea1598b368dbe263bc611ac2e911c1efed7adda1513324df8a4bcea7a0a715c8`, `fver_d2756ceefdddaa692ae29fdb24208827e98ba025a49ea90c88baba45dd31a5d2` |
| `NQ` | `fver_f35cc0c772d8211d148d68c3d336c0744622533293dd5b5ed82f89415856318c`, `fver_d6ff3fceeeb1af108a1e2cf7e7eb44b639656356077946dede3f5e1002c0e70d`, `fver_458c224eb24bbb2fdcc41d09137a2d135b4718beac3cee1d9eb228a38ce88cb3`, `fver_93294b837ac194dd38dd59620def385f8ec4a59a2d75ace67bf7b76109d7bf9e`, `fver_7bbe9a5146772fe0cc32a21775aed43a491edfdac7acffb4aa2aac87b619d784`, `fver_23299247768bdc2a94a6522291fd3064ade4a5970a8d203a749001b67a778b78`, `fver_fe3da8b3d17c1b79e9e066fe198a1c3614a9ef89a6b9bff3225bd69f4582c930`, `fver_ebd6385a059a59e4632f7d5b2165fc51a51cb3a9b0d233a8dde06e414fe4a8f8`, `fver_ac3d85853600c5c76c89753abb86a3774571ed893cc0e0514c7d12ec82f70d30`, `fver_19995db6c53738c9871419568f9afb829c396351133cc1e07db6fd0460b13959`, `fver_95085ae38a1ed36295a825d8242975960123859df214cd63475f6d47873b023d` |
| `RTY` | `fver_e9ce72cfd3b724f50dbdf020ede133a8dde9fdbffa906a94f53434d4e7a27ce4`, `fver_aadfd90e273da1c86ff8b01ac0c0d5a43c44d776f1d020274e767eeb0396202b`, `fver_bd203ee15d103c042323e2e0c3fe793687faa84e2d31811c78216be50fecdb0a`, `fver_f40db5872b7ffb7bc06b9ab308950ca31aa2f1d637817dd79071fc62854c2213`, `fver_6e21d4d4fea18eeda278a5af45c47d5aadbb77d9ea8e61f27f4968c0494a435c`, `fver_13d957b05c822739bc3e4f8f33139a270498d81be97a7822e72509a15a5fdad7`, `fver_5a99d6534dbeb2705a4ef40d88bf676ff12bf1499f1b7d7f88c8b88af251221a`, `fver_0db46ea4e45ffc42943489c0e7e9db64df15174c4c341792acae1f5ad1a0453c`, `fver_203319e03a8d88ac3d9cb04de93bb1d6820e1c40bc1636e6dbc361e43859ca1b`, `fver_58a4a2c1311355b33b71f821a0d9e1dc1707449bf9478b08e36fd092d900e1b2`, `fver_54c730dac71169ba01b065d5fc8364835c16078029688a2677d9dd534c7741c2` |
