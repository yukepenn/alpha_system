# fixed_horizon Scaleout Summary

Value-free scaleout summary. It contains no raw rows, canonical values,
feature values, label values, provider responses, SQLite content, or Parquet payloads.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P16`
- Engine: `reference`
- Rollout: `full-window`
- Dry run: `no`
- Targeting active: `yes`
- Accepted unit count: `18`
- Bounded-real year: `2024`
- Bounded-real unit count: `18`
- Planned: `0`
- Completed: `0`
- Skipped: `18`
- Failed: `0`
- Requested workers: `1`
- Effective workers: `1`
- Threads per worker: `16`

## Target

- Family: `fixed_horizon`
- Feature ids: `config default`
- Feature groups: `none`
- Label ids: `none`
- Label groups: `none`
- Symbols: `ES, NQ, RTY`
- Years: `2024`
- DatasetVersion ids: `accepted grid default`

## Acceptance States

| State | Unit count |
| --- | ---: |
| `ACCEPTED` | 18 |

## Window Policy

- Eligible DatasetVersion states are `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.
- Dataset-level fallback is used for 2018: the blocked 2018 `ohlcv_1m`
  DatasetVersion is excluded rather than fabricating per-symbol acceptance.
- 2019 warning metadata and 2026 partial-year warning metadata are preserved
  through the accepted/warned DatasetVersion state.
- Multi-input units require every configured input schema/year to carry an
  accepted or accepted-with-warnings DatasetVersion before execution.

## Point-In-Time Guard

- Feature values are emitted at the current source row `available_ts`;
  label values carry `label_available_ts` at or after the forward terminal.
- Rolling, expanding, prior-boundary, and derived-state inputs may use only
  source rows whose `available_ts` is less than or equal to the output
  `available_ts`.
- Accepted DatasetVersion gates fail closed before canonical rows are
  loaded or values are written.

## Fixed-Horizon Label Guards

- Label compute uses the reference label engine via `run_seed_label_pack`.
- Forward terminals are keyed by `series_id+contract_id+event_ts`.
- Roll-splice windows use the wired roll guard with policy `drop`.
- Daily maintenance-break crossings use policy `drop`.
- Label materialization is Parquet-first; JSONL is not used for
  research-scale values in this phase.

## Materialized Value Evidence

- This summary is value-free and does not include per-row label values.
- In dry-run mode, Parquet paths, value content hashes, registry row
  fields, materialized row counts, checkpoint markers, and observed
  `label_available_ts` min/max are unavailable.
- When `--execute` succeeds, the driver verifies Parquet-backed registry
  rows for `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, and
  `label_version_id` through `LabelRegistry.register_materialized_label`.

## Unit Outcomes

| Stage | Year | Symbol | Primary DatasetVersion | Input DatasetVersions | Status | Rows |
| --- | ---: | --- | --- | --- | --- | ---: |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 340876 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 340368 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 339866 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 338605 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 337345 |
| `full_window` | 2024 | `ES` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 333575 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 341137 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 340630 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 340126 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 338865 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 337607 |
| `full_window` | 2024 | `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 333832 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 318399 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 317532 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 317000 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 315630 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 314293 |
| `full_window` | 2024 | `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `ohlcv_1m:dsv_databento_ohlcv_05404069799decb0` | `skipped` | 310617 |

## Bounded-Real LabelVersion Preview

The bounded-real dry-run preview is write-free. It records deterministic
LabelVersion ids that execution is expected to register for the same
unit identities; content hashes are unavailable until Parquet values are
written.

| Symbol | Label | LabelVersion ids |
| --- | --- | --- |
| `ES` | `fwd_ret_1m` | `lver_663227cc9655c6515c7f2f88417687504cb492f4cad463e2183541dc969266f5` |
| `ES` | `fwd_ret_3m` | `lver_f38e2e11ef95c5039045081e3c7a37e5b817a630697f39e0313c5cfd3961fef4` |
| `ES` | `fwd_ret_5m` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` |
| `ES` | `fwd_ret_10m` | `lver_c67970063cc8aa52155e165679cdb7747f183dc51dabf5c0b788f6f51f639242` |
| `ES` | `fwd_ret_15m` | `lver_242006233681016574f34436d1003ab1cb4b732afb1f4597d172dda1d9381bed` |
| `ES` | `fwd_ret_30m` | `lver_91db9a025b106bea1c51bff6770a9d7a77d53afa64e0da0c80e2627ef6ec1f19` |
| `NQ` | `fwd_ret_1m` | `lver_1f7aabcd39e00f342703e621e3210e35f96b8c0a48b695de78d2684abaacbf3f` |
| `NQ` | `fwd_ret_3m` | `lver_df430e02bc852f5e44735b63a5f83d02a10fa981d6fd103d1954c5f4965e3e07` |
| `NQ` | `fwd_ret_5m` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` |
| `NQ` | `fwd_ret_10m` | `lver_ec7069c1ec29ef28e245e3659fddaa9b2df45b5c08224ff131e227005903c198` |
| `NQ` | `fwd_ret_15m` | `lver_04e2150bc8420808f9fde0953e5bc5da49bc69cc62e8733c31edb05ea4d60856` |
| `NQ` | `fwd_ret_30m` | `lver_16a3ba95f61d0afcd2fee8296a3524193d1f9f4dcea10cf4d7f56a4c53194aac` |
| `RTY` | `fwd_ret_1m` | `lver_cafa799da35f6a4261707630d3ad8e72093c38c14ae8cc0f8d4aac849b888fb1` |
| `RTY` | `fwd_ret_3m` | `lver_843c2c918438bfddbce2f168ab7b4759eb23ecf6368d28e9b7df5f8ccd6aa88b` |
| `RTY` | `fwd_ret_5m` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` |
| `RTY` | `fwd_ret_10m` | `lver_18014db3ea57945e08c336897f337fe623b65de1fef2508be135484d15738dfd` |
| `RTY` | `fwd_ret_15m` | `lver_eacae68aa8c390cabefb9ec45a8c2d3ffe0e187ae308f8479da4433eb24207a0` |
| `RTY` | `fwd_ret_30m` | `lver_486615c1020dd2506007c63118ad8f0448967a410ad01a0a0f71942ef9a64e8f` |
