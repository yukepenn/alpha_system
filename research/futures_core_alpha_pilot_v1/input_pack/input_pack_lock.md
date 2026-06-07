# FUTCORE-P03 Input Pack Lock

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P03`  
Lock type: registry-resolved, value-free input references  
Recorded on: 2026-06-07

This lock pins the DatasetVersion, FeaturePack, and LabelPack references that
downstream StudySpecs and data-contract audits must bind against. It records
only ids, registry metadata, hashes, schema versions, and registry-reported
reference strings. It does not copy or read value rows, Parquet files, SQLite
registries, raw provider files, provider responses, or run-local artifacts into
the repository.

`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml` and
`research/futures_core_alpha_pilot_v1/scope/scope_contract.md` pin the pilot
universe to `ES`, `NQ`, and `RTY`. If this input lock disagrees with those
scope files, downstream execution should stop until the disagreement is
repaired.

## Resolution Evidence

| Surface | Registry reference | Result |
| --- | --- | --- |
| DatasetVersion resolver | `alpha_system.data.foundation.version_registry.resolve_dataset_version('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite', 'dsv_databento_ohlcv_05404069799decb0')` | Resolved one accepted ES/NQ/RTY Databento OHLCV DatasetVersion. |
| FeaturePack list | `alpha feature list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite --json` | Resolved two registered FeatureVersion refs. |
| LabelPack list | `alpha label list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite --json` | Resolved one registered LabelVersion ref. |
| Runtime pack resolver | `FeatureLabelPackResolver(alpha_data_root='/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke')` | Validated dataset-version and partition binding for the locked feature and label refs. |

The registry paths above are opaque local registry references reported by the
preflight substrate. They are not committed files.

## DatasetVersion Lock

| Field | Locked reference |
| --- | --- |
| DatasetVersion id | `dsv_databento_ohlcv_05404069799decb0` |
| Registry path | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite` |
| Source | `dsrc_databento_historical` |
| Symbol universe | `ES`, `NQ`, `RTY` |
| Bar size | `1 min` |
| What to show | `TRADES` |
| Created at | `2026-06-05T05:08:19+00:00` |
| Manifest hash | `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31` |
| Code hash | `87fb8de7760c3635fb883948971bc12ee21ed64562713975bb20028ae3f92139` |
| Config hash | `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b` |
| Quality report hash | `7e46966bdc6921a0bb338097fa82ec94fcdf401e1913d81b288052bd6c9c66b4` |
| Coverage report hash | Registry record returned `null`; carry to `FUTCORE-P13` as an audit observation. |

## FeaturePack Lock

Research-scale consumers must bind to the `parquet_path` side of each registry
record. The registry reports `value_store_format=dual`, meaning the pack has a
JSONL sidecar and a Parquet side. JSONL is not locked as a research-scale input
and is reserved for audit, smoke, or small-tier inspection only.

| Feature id | FeatureVersion id | Feature set | DatasetVersion | Partition | `value_store_format` | `parquet_path` | `value_content_hash` | `value_schema_version` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_ohlcv_rth_flag` | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` | `fset_es_session_ctx_smoke` / `v1_rth_flag` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_rth_flag/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:58c42ab7515299d64ea4f90348290e88e3510849b3f31490a22f5a56638c7705` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_session_minute` | `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` | `fset_es_session_ctx_smoke` / `v1_session_minute` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_session_minute/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:d953e7f4bd32998b0fc5d3db7e28b968dc25bf0896bc491b8fb5ba6442fc8278` | `alpha_system.features.materialization.v1` |

Additional value-free metadata:

| FeatureVersion id | FeatureRequest id | Materialization plan id | Lifecycle | Event window | Available window |
| --- | --- | --- | --- | --- | --- |
| `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` | `freq_67991722245329f35c0fa612` | `fmat_7fc558435b563192a8b83f11c56c28f26cbe4b5ba0b8bdd00d153446c1312106` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |
| `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` | `freq_76147d2e3318292d48004696` | `fmat_9aa8b9343108c2ce33d181f1457998bc5a36a3eca0397e8af7974b111f465f4d` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` |

## LabelPack Lock

Research-scale consumers must bind to the `parquet_path` side of the registry
record. The registry reports `value_store_format=dual`; the JSONL side is not
locked as a research-scale input.

| Label id | LabelVersion id | LabelSpec id | DatasetVersion | Partition | `value_store_format` | `parquet_path` | `value_content_hash` | `value_schema_version` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fwd_ret_5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `lspec_cd6523694c850c9943b2067e` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/labels/materialized/lset_355b408d6516452304866be98b0371ea7239f39657c4b33276dc81fee3db918d/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f` | `alpha_system.labels.materialization.v1` |

Additional value-free metadata:

| LabelVersion id | Materialization plan id | Lifecycle | Event window | Label available window |
| --- | --- | --- | --- | --- |
| `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `lmat_e9fa63fe8a9a5f966f2a157390b1ef265e93048b82767ac96d060d7003725b94` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-08T23:55:00+00:00` | `2024-01-02T00:06:05+00:00` to `2024-01-09T00:00:05+00:00` |

## Universe To Pack Mapping

| Universe member | DatasetVersion binding | Locked FeaturePack refs | Locked LabelPack refs | Notes |
| --- | --- | --- | --- | --- |
| `ES` | `dsv_databento_ohlcv_05404069799decb0` | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`, `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | DatasetVersion universe includes `ES`; pack ids are locked by registry binding. |
| `NQ` | `dsv_databento_ohlcv_05404069799decb0` | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`, `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | DatasetVersion universe includes `NQ`; symbol-level pack coverage remains a `FUTCORE-P13` audit item. |
| `RTY` | `dsv_databento_ohlcv_05404069799decb0` | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`, `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | DatasetVersion universe includes `RTY`; symbol-level pack coverage remains a `FUTCORE-P13` audit item. |

## Carried-Forward Observations For `FUTCORE-P13`

- The locked feature set id is `fset_es_session_ctx_smoke`; `FUTCORE-P13` must
  audit whether these refs provide complete ES/NQ/RTY symbol-level coverage for
  each approved StudySpec. This phase does not fill any coverage gap.
- The locked records report `value_store_format=dual`. `FUTCORE-P13` must audit
  that research-scale scans bind to the Parquet pointers and never to JSONL.
- The locked pack partition is `development_partition`. Any validation,
  locked, or shadow partition pack binding must be separately audited before
  downstream use.
- The locked label set contains only `fwd_ret_5m`. Other primary or extended
  horizons from the P02 scope are not added here; missing labels must route
  through later FeatureRequest/LabelSpec work, especially `FUTCORE-P15`.

## Boundaries

- No raw provider file, provider response, Parquet value file, SQLite registry,
  feature value, or label value is committed by this lock.
- No external provider API call was made for this phase.
- No `src/alpha_system/**` consumed primitive was edited.
- No AlphaSpec, diagnostic, profitability, tradability, strategy-readiness,
  broker, live, paper, order, account, deployment, or production claim is made.
