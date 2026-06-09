# bbo_tradability_top_book Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P12`
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

- Family: `bbo_tradability_top_book`
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
| `full_window` | 2019 | `ES` | `dsv_databento_bbo_f91f510a8d6fa87b` | `bbo_1m:dsv_databento_bbo_f91f510a8d6fa87b` | `skipped` | 3844852 |
| `full_window` | 2019 | `NQ` | `dsv_databento_bbo_f91f510a8d6fa87b` | `bbo_1m:dsv_databento_bbo_f91f510a8d6fa87b` | `skipped` | 3848295 |
| `full_window` | 2019 | `RTY` | `dsv_databento_bbo_f91f510a8d6fa87b` | `bbo_1m:dsv_databento_bbo_f91f510a8d6fa87b` | `skipped` | 3617251 |
| `full_window` | 2020 | `ES` | `dsv_databento_bbo_af9511d169b0aead` | `bbo_1m:dsv_databento_bbo_af9511d169b0aead` | `skipped` | 3845688 |
| `full_window` | 2020 | `NQ` | `dsv_databento_bbo_af9511d169b0aead` | `bbo_1m:dsv_databento_bbo_af9511d169b0aead` | `skipped` | 3838219 |
| `full_window` | 2020 | `RTY` | `dsv_databento_bbo_af9511d169b0aead` | `bbo_1m:dsv_databento_bbo_af9511d169b0aead` | `skipped` | 3718935 |
| `full_window` | 2021 | `ES` | `dsv_databento_bbo_d5cb08f949e7ff28` | `bbo_1m:dsv_databento_bbo_d5cb08f949e7ff28` | `skipped` | 3886993 |
| `full_window` | 2021 | `NQ` | `dsv_databento_bbo_d5cb08f949e7ff28` | `bbo_1m:dsv_databento_bbo_d5cb08f949e7ff28` | `skipped` | 3887323 |
| `full_window` | 2021 | `RTY` | `dsv_databento_bbo_d5cb08f949e7ff28` | `bbo_1m:dsv_databento_bbo_d5cb08f949e7ff28` | `skipped` | 3738845 |
| `full_window` | 2022 | `ES` | `dsv_databento_bbo_7b5595d5030462ab` | `bbo_1m:dsv_databento_bbo_7b5595d5030462ab` | `skipped` | 3895309 |
| `full_window` | 2022 | `NQ` | `dsv_databento_bbo_7b5595d5030462ab` | `bbo_1m:dsv_databento_bbo_7b5595d5030462ab` | `skipped` | 3895232 |
| `full_window` | 2022 | `RTY` | `dsv_databento_bbo_7b5595d5030462ab` | `bbo_1m:dsv_databento_bbo_7b5595d5030462ab` | `skipped` | 3796782 |
| `full_window` | 2023 | `ES` | `dsv_databento_bbo_8772e3b47aa5fb98` | `bbo_1m:dsv_databento_bbo_8772e3b47aa5fb98` | `skipped` | 3884683 |
| `full_window` | 2023 | `NQ` | `dsv_databento_bbo_8772e3b47aa5fb98` | `bbo_1m:dsv_databento_bbo_8772e3b47aa5fb98` | `skipped` | 3886938 |
| `full_window` | 2023 | `RTY` | `dsv_databento_bbo_8772e3b47aa5fb98` | `bbo_1m:dsv_databento_bbo_8772e3b47aa5fb98` | `skipped` | 3766796 |
| `full_window` | 2024 | `ES` | `dsv_databento_bbo_f9e1d70a04d9dae4` | `bbo_1m:dsv_databento_bbo_f9e1d70a04d9dae4` | `skipped` | 3815438 |
| `full_window` | 2024 | `NQ` | `dsv_databento_bbo_f9e1d70a04d9dae4` | `bbo_1m:dsv_databento_bbo_f9e1d70a04d9dae4` | `skipped` | 3816912 |
| `full_window` | 2024 | `RTY` | `dsv_databento_bbo_f9e1d70a04d9dae4` | `bbo_1m:dsv_databento_bbo_f9e1d70a04d9dae4` | `skipped` | 3668940 |
| `full_window` | 2025 | `ES` | `dsv_databento_bbo_35d4417c086be53f` | `bbo_1m:dsv_databento_bbo_35d4417c086be53f` | `skipped` | 3790171 |
| `full_window` | 2025 | `NQ` | `dsv_databento_bbo_35d4417c086be53f` | `bbo_1m:dsv_databento_bbo_35d4417c086be53f` | `skipped` | 3789819 |
| `full_window` | 2025 | `RTY` | `dsv_databento_bbo_35d4417c086be53f` | `bbo_1m:dsv_databento_bbo_35d4417c086be53f` | `skipped` | 3669127 |
| `full_window` | 2026 | `ES` | `dsv_databento_bbo_22c49fbf57cceea6` | `bbo_1m:dsv_databento_bbo_22c49fbf57cceea6` | `skipped` | 1547029 |
| `full_window` | 2026 | `NQ` | `dsv_databento_bbo_22c49fbf57cceea6` | `bbo_1m:dsv_databento_bbo_22c49fbf57cceea6` | `skipped` | 1546710 |
| `full_window` | 2026 | `RTY` | `dsv_databento_bbo_22c49fbf57cceea6` | `bbo_1m:dsv_databento_bbo_22c49fbf57cceea6` | `skipped` | 1524523 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_179d857790a3dfbafd326a1c572765ab0411a53a69e69b00f2b2c61c73a182b6`, `fver_d4c2cd7edbe9a1a6f20bf93a0b1380c07edd8ef009a665e538093aad74b8859e`, `fver_fe6fcc0cd2f91ddadadc1e756ac94129e58fda7e4a9fb8286eaa9e7d970ac284`, `fver_2299793f5f46957e1822896314c220e44ec11f267d3f5252590a3e12abcbc358`, `fver_aac3c66c35784079ea809e433c304e72fda34fd1a8cf344c8ba335df7c94737a`, `fver_8432afad162111e16c77ff3d55b20ef91392cd3e2bd32817eb605adddbfe75cc`, `fver_b696f0b2399075ce36422b62458eff97386ec476e56c009014aab63834670cce`, `fver_8bc345c2b1d85250bb6b85754a5d4700b06c22bd056c5d91473ac10ff3899759`, `fver_3a162c4da024b6a81cbf997ba02d47b070bcc13f2f09884a104ee6053f3dc486`, `fver_88d2d46cb7ffc1c9cfff7c5a8cfd3a7553d54ac88360ddc5b869af16394233dd`, `fver_2516741a49026db901c2d5c3cd85ea24d2911eb5ea9fd5f25f993a8077b559ec` |
| `NQ` | `fver_bdf9753749ef485d2c399fc4ee046e91f3f070a537ee37b1f280d982e3cd4a22`, `fver_7439eca390095664c91a1d55df523eb6685ed6867692fdee23bbf72c9697e3f5`, `fver_6ccf67910310b8e4b40e0ee9531107b996b4d0f0056e69b63e164bb056dd1213`, `fver_309a92e21c7d9c4c01533851242d0a72c463b40b64ace1ef730b8cf1a7365b2c`, `fver_1c4961e4235038e374f34e510fc0591080e3467f89564fdd1a1cb944ce113496`, `fver_c0ba132a128c175d736b0a8f53f6ebd064e3136ffd4731b64ba3890e0f067014`, `fver_bfc08f2e84c7f133c95cd7a3ef78ac2f965662f00e44935a4f13c3b07ba48aed`, `fver_024ed7e353c75c3108667bc029050ca7d673389df98b67ee6415de624317a4af`, `fver_2380c0a86af332a677944eaff06b41b8279d4064a23794a63b3b1c792ad556a9`, `fver_e32fdf9814d3e2f365c661c53ba28da9ea4135fcbf9342527d28b1a868354ecc`, `fver_947dc71ef55374cf48733dd2ad7571bb59fbbc5e283704414e03ec2bab743f77` |
| `RTY` | `fver_0a1f6448f9a47a6db7c5bad72bf4b6aebcb788ac45276364c178e5944066d535`, `fver_ee12498a0dd96d1a94398a5ee469eca4c6783d7b400ef1edc5d9a762989cd46d`, `fver_391aed1ecec176fcf1b54b41562dc937b1946067f3b19811225cd48e2149068f`, `fver_2b709fdb2db17b580d89305d87b39e97aaf5cc5a25b60d593ec41f386e56e8af`, `fver_21bb98c1823fb4d8a34906cc45e2cac19e0533af754dc3fc71ff019087870603`, `fver_ddd91663628be6743354b93ba9ddd7e8c1bde5c23985dfb9e603e2056d86215e`, `fver_15c604fac1031090750739065737e425e723f3a260d5b314a9fda56c7e49f363`, `fver_5476ec77f4237284d28e4764c0150100243d2933ce4e8fd166d9f81ad70acba7`, `fver_9cb271e01d0a85c376f9a4e2d8f8297d0c6e39a91fcb5b4ee6859a33b78fd0af`, `fver_dfb1495910d2c5ce5c599dfd34b1e8b5e172978ce73e4cff3060b52dd993e0b1`, `fver_999e35e5ab99b31efaf44a5c5dcda0403bd6b8022bba8838c6c04c38c18b69ad` |
