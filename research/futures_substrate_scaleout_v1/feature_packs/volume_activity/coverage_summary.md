# volume_activity Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P11`
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

- Family: `volume_activity`
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

## Volume / Activity Primitive Bindings

- `participation` is represented by existing rolling-volume and
  volume-zscore primitives; no new participation formula is introduced.
- `time_of_day_relative_volume` binds to existing volume-zscore plus
  session-minute context.
- `volume_regime` binds to existing rolling-volume and volume-zscore
  primitives.
- `activity_bursts` binds to existing volume-zscore plus rolling-range
  activity context.
- `effort_result_proxies` binds to existing rolling-volume, range-position,
  trendiness, close-location, and wick-rejection primitives.
- All bindings are deterministic OHLCV-derived primitives emitted at
  the current row `available_ts`; no volume feature zoo is introduced.

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
| `full_window` | 2019 | `ES` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 2796256 |
| `full_window` | 2019 | `NQ` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 2798760 |
| `full_window` | 2019 | `RTY` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ohlcv_1m:dsv_databento_ohlcv_a483cc0cc282474b` | `completed` | 2630728 |
| `full_window` | 2020 | `ES` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 2796864 |
| `full_window` | 2020 | `NQ` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 2791432 |
| `full_window` | 2020 | `RTY` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ohlcv_1m:dsv_databento_ohlcv_bac95e92f1bb1850` | `completed` | 2704680 |
| `full_window` | 2021 | `ES` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 2826904 |
| `full_window` | 2021 | `NQ` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 2827144 |
| `full_window` | 2021 | `RTY` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ohlcv_1m:dsv_databento_ohlcv_8aeb50fb409fc691` | `completed` | 2719160 |
| `full_window` | 2022 | `ES` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 2832952 |
| `full_window` | 2022 | `NQ` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 2832896 |
| `full_window` | 2022 | `RTY` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ohlcv_1m:dsv_databento_ohlcv_dc7c86c813fe0dfe` | `completed` | 2761296 |
| `full_window` | 2023 | `ES` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 2825224 |
| `full_window` | 2023 | `NQ` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 2826864 |
| `full_window` | 2023 | `RTY` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ohlcv_1m:dsv_databento_ohlcv_ec144f9a02a64774` | `completed` | 2739488 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 2774864 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 2775936 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 2668320 |
| `full_window` | 2025 | `ES` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 2756488 |
| `full_window` | 2025 | `NQ` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 2756232 |
| `full_window` | 2025 | `RTY` | `dsv_databento_ohlcv_35ffead770498acd` | `ohlcv_1m:dsv_databento_ohlcv_35ffead770498acd` | `completed` | 2668456 |
| `full_window` | 2026 | `ES` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 1125112 |
| `full_window` | 2026 | `NQ` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 1124880 |
| `full_window` | 2026 | `RTY` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ohlcv_1m:dsv_databento_ohlcv_a0342ee6a412622b` | `completed` | 1108744 |

## Bounded-Real FeatureVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
FeatureVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | FeatureVersion ids |
| --- | --- |
| `ES` | `fver_a240b2d57c39cc45a34c2d08426d920d8c2e0b6d46d9fc5a4abec06adb36d47b`, `fver_252de7f4b1487d540516e6eded6930643af36647fa1eb5b2f957ab9b46caf273`, `fver_b604e3b216307c18b34ef1fab7f6f9d7be7b2983595282b817e6498b646f9eb7`, `fver_fb96276fdd47ecec30a013beb6ee59afe98851c7f2d8c3a5b120c67889bfc923`, `fver_3c166eb0eeae1b4ccd82380d54bc7a4f2d5926935327955d85a0f161c1148454`, `fver_f1c738dcf0ec11a37df0ae2f8bba03f2eb1b2a87402ba82abdb4f27288742334`, `fver_a5077422924e247fffa00b8427cd0b1cb77be1ff616eb58c803dc0a682367ec0`, `fver_f29069d6ed8e7d1f45bc82e3326490695204249a20f0c44dfa453f453b94a3ab` |
| `NQ` | `fver_4b7a92476f031619d99a257d71855f137f983347674e975bfddf5ab0d9d236b7`, `fver_6ddc0f9abdd3cd6c1c53b5d019b4f35d16bad8b375247758f5812b72f9c22107`, `fver_861b6fa4818fd8475c93872c10241b94ccd17c686a026151f3dd058dbcaf0de6`, `fver_629646c3f727ae9ae70f21a3fc1c8acf6d3c1a482b7692518f7beedbb6569f1c`, `fver_47b8ac9e5fc284c9212b71faea2add592e805ba814ab2e7c7b9a15bc68808e33`, `fver_048856a43a91225c3c584d63b54b95df195ef6db076dc89c80eb54ca7d59f6f6`, `fver_cb6c7240d629537c74e6d8e6ab8407be950e80d20585572d8d649863a1565ab5`, `fver_f6aa820c308459917f5cf6de2d8c5bf68116ac189523f35fe5f28f9107eb4d99` |
| `RTY` | `fver_f8d0867bcf19a7b5438bf59a311d25ea1f0f1ae92344d69988112f326afeba13`, `fver_53dd213c8b8cf0419a8e74b8ddeb5f28de7257c7f0ad859cae01b3a8ee87ac35`, `fver_21cf409a6e34f130d0703ad954c3f4a42cdcd7f40a3a0f5343c4e281a60f043f`, `fver_6405eda8cb99fcfbf453f68c5425523ea824c9303417efbc8a030ebb71628d0f`, `fver_47b9e07dcab76fdc918935a1a4abdfc761c809de042fe320d70dfa3c2a42a080`, `fver_334d29abce3c6b56baf48c885ba9b10d694c6c3f7b1cfc2ae165e1d316e9d936`, `fver_dc18b36b9d051ed9784bb9e5d204d4f615ba284532524755a4842fde5df638fb`, `fver_4df1a9e27a3371501dcaa84e57881a8f175ba68e61ceaa05a4a1afb3472ba6d4` |
