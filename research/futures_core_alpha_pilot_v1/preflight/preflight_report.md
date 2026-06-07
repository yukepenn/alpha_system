# FUTCORE-P01 Preflight Readiness Report

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P01`  
Report type: value-free readiness contract  
Recorded on: 2026-06-07

This report records the entry gates consumed by the Futures Core Alpha Pilot.
It records ids, registry references, hashes, status flags, and command summaries
only. It does not copy market data, value rows, Parquet files, SQLite files,
provider responses, or run-local artifacts into the repository.

The executor does not assign the phase verdict. Review, staging, commit, PR,
CI, merge, and done-check are Ralph-owned.

## Gate Table

| Gate | Expected condition | Observed status | Evidence reference | Note |
| --- | --- | --- | --- | --- |
| Consumed primitive imports | `alpha_system.governance`, `alpha_system.runtime`, and `alpha_system.agent_factory` import cleanly. | `PASS` | Project research venv import command returned `imports_ok`; source-layout check with `PYTHONPATH=src` also returned `imports_ok`. | No consumed primitive source was edited. |
| `FEATURE_LABEL_PARQUET_SINK_V1` complete | Dual JSONL+Parquet value sink exists; registries record `value_store_format`, `parquet_path`, `value_content_hash`, and `value_schema_version`. | `PASS` | `handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`; `configs/agent_factory/preflight.toml`; feature/label registry metadata under `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/`. | Registry metadata reports `value_store_format=dual` and Parquet pointer/hash/schema fields for the referenced smoke packs. |
| `SESSION_LABEL_GUARD_FIX_V1` complete | Role-aware `session_label` guard accepts declared point-in-time session metadata and still blocks true labels / forward-looking fields. | `PASS` | `handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`; `configs/agent_factory/preflight.toml`; `docs/research_runtime/SESSION_LABEL_GUARD.md`. | Config records `session_label_guard_fixed=true`; prior handoff records the guard smoke as landed. |
| Research Runtime real-data smoke status | Recorded real DatasetVersion runtime smoke status exists by reference; no live acquisition is re-run here. | `PASS` | `handoffs/PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1.md`; `configs/agent_factory/preflight.toml`; `docs/research_runtime/REAL_SMOKE.md`. | Prior recorded smoke: `status PASS`, `input_resolution_status=INPUTS_RESOLVED`, `real_dataset_version_smoke_ran=True`, `external_provider_call=false`, `raw_file_read=false`. |
| Accepted DatasetVersion resolvable | Accepted DatasetVersion id resolves through `resolve_dataset_version`. | `PASS` | `resolve_dataset_version('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite', 'dsv_databento_ohlcv_05404069799decb0')`. | Resolved id `dsv_databento_ohlcv_05404069799decb0`; source `dsrc_databento_historical`; symbols `ES`, `NQ`, `RTY`; bar size `1 min`; what-to-show `TRADES`; manifest hash `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31`. |
| Parquet FeaturePack / LabelPack availability by reference | Registry-resolved FeaturePack and LabelPack records expose Parquet metadata fields by reference only. | `PASS` | Read-only feature and label registry APIs over `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/{features,labels}.sqlite`. | Two feature records and one label record are registered for `development_partition`; metadata references are listed below. |
| Agent Factory preflight | Roles, permissions, queue contracts, and separation-of-duties wiring import; preflight gates pass with the referenced local registry root and landed blockers. | `PASS` | `evaluate_agent_factory_preflight(...)` returned `PREFLIGHT_PASS`; imports of `roles`, `permissions`, `queue`, and `separation` modules succeeded. | The evaluator was given `alpha_data_root=/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke`, `real_dataset_version_smoke_ran=true`, `parquet_sink_landed=true`, `session_label_guard_fixed=true`, large-scale value request `true`, and session-context request `rth_flag, session_minute`. |

## DatasetVersion Reference

| Field | Reference |
| --- | --- |
| DatasetVersion id | `dsv_databento_ohlcv_05404069799decb0` |
| Registry resolver | `alpha_system.data.foundation.version_registry.resolve_dataset_version` |
| Registry path | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite` |
| Source | `dsrc_databento_historical` |
| Symbol universe | `ES`, `NQ`, `RTY` |
| Bar size | `1 min` |
| What to show | `TRADES` |
| Manifest hash | `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31` |
| Config hash | `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b` |
| Created at | `2026-06-05T05:08:19+00:00` |

## FeaturePack References

| Feature id | FeatureVersion id | Feature set | DatasetVersion | Partition | `value_store_format` | `parquet_path` | `value_content_hash` | `value_schema_version` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_ohlcv_rth_flag` | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` | `fset_es_session_ctx_smoke` / `v1_rth_flag` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_rth_flag/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:58c42ab7515299d64ea4f90348290e88e3510849b3f31490a22f5a56638c7705` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_session_minute` | `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` | `fset_es_session_ctx_smoke` / `v1_session_minute` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_session_minute/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:d953e7f4bd32998b0fc5d3db7e28b968dc25bf0896bc491b8fb5ba6442fc8278` | `alpha_system.features.materialization.v1` |

## LabelPack References

| Label id | LabelVersion id | LabelSpec id | DatasetVersion | Partition | `value_store_format` | `parquet_path` | `value_content_hash` | `value_schema_version` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fwd_ret_5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `lspec_cd6523694c850c9943b2067e` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/labels/materialized/lset_355b408d6516452304866be98b0371ea7239f39657c4b33276dc81fee3db918d/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f` | `alpha_system.labels.materialization.v1` |

## Boundary Confirmation

- No external provider call was made.
- No live, paper, broker, order, account, deployment, or production operation was
  performed.
- No raw provider file, Parquet value file, or value row was opened or copied
  into the repo.
- Local-only SQLite registries were queried only through registry/resolver APIs
  to obtain ids and metadata references.
- No `src/alpha_system/**` consumed primitive was edited.
- No alpha, profitability, tradability, strategy, portfolio, paper, live, or
  production claim is made.
