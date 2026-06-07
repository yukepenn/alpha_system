# FUTCORE-P03 Input Pack Lock

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P03`  
Lock type: registry-resolved, value-free input references  
Recorded on: 2026-06-07

This lock pins the DatasetVersion, FeaturePack, and LabelPack references that
downstream AlphaSpecs, StudySpecs, audits, and diagnostics must bind against.
It records only ids, registry metadata, hashes, schema versions, availability
windows, and registry-reported pointer strings. It does not copy or read value
rows, Parquet files, raw provider files, provider responses, or run-local
artifacts into the repository.

`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml` and
`research/futures_core_alpha_pilot_v1/scope/scope_contract.md` pin the pilot
universe to `ES`, `NQ`, and `RTY`. If this input lock disagrees with those
scope files, downstream execution should stop until the disagreement is
repaired.

## Resolution Evidence

| Surface | Registry reference | Result |
| --- | --- | --- |
| DatasetVersion resolver | `alpha_system.data.foundation.version_registry.resolve_dataset_version('/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite', 'dsv_databento_ohlcv_05404069799decb0')` | Resolved one accepted ES/NQ/RTY Databento OHLCV DatasetVersion. |
| FeaturePack list | `alpha feature list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/features.sqlite --json` | Resolved eight registered FeatureVersion refs. |
| LabelPack list | `alpha label list --registry-path /home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/labels.sqlite --json` | Resolved three registered LabelVersion refs. |
| Runtime pack resolver | `FeatureLabelPackResolver(feature_store=FeatureStore(FeatureRegistry(...)), label_registry=LabelRegistry(...))` | Resolved eight FeaturePack handles and three LabelPack handles by explicit local registry facade. |

The registry paths above are opaque local registry references reported by the
preflight substrate. They are not committed files.

## DatasetVersion Lock

| Field | Locked reference |
| --- | --- |
| DatasetVersion id | `dsv_databento_ohlcv_05404069799decb0` |
| Registry path | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/registry/datasets.sqlite` |
| Source | `dsrc_databento_historical` |
| Symbol universe | `ES`, `NQ`, `RTY` |
| Contract universe | `contract_databento_es_v_0_front`, `contract_databento_nq_v_0_front`, `contract_databento_rty_v_0_front` |
| Bar size | `1 min` |
| What to show | `TRADES` |
| Time span | `2024-01-01T00:00:00+00:00` to `2025-01-01T00:00:00+00:00` |
| Created at | `2026-06-05T05:08:19+00:00` |
| Manifest hash | `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31` |
| Code hash | `87fb8de7760c3635fb883948971bc12ee21ed64562713975bb20028ae3f92139` |
| Config hash | `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b` |
| Quality report hash | `7e46966bdc6921a0bb338097fa82ec94fcdf401e1913d81b288052bd6c9c66b4` |
| Coverage report hash | Registry DatasetVersion mapping did not expose a `coverage_report_hash`; carry to `FUTCORE-P13` as an audit observation. |

## FeaturePack Lock

Research-scale consumers must bind to the `parquet_path` side of each registry
record. The registry reports `value_store_format=dual`, meaning each pack has a
JSONL sidecar and a Parquet side. JSONL is not locked as a research-scale input
and is reserved for audit, smoke, or small-tier inspection only.

| Feature id | FeatureVersion id | Feature set | DatasetVersion | Partition | `value_store_format` | `parquet_path` | `value_content_hash` | `value_schema_version` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base_ohlcv_log_returns` | `fver_7ac2429f12ce6f7d494b7c0ab968446f2455da51863ebe471ddd8a224b6fa9f9` | `fset_es_ohlcv_session_smoke` / `v1_log_returns` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_ohlcv_session_smoke/v1_log_returns/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:5958b475409b9275c5982935de6d3487d2c01fe6845f31eee5781b3f1f0d812a` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_range_position` | `fver_862f9b2d36e10b58d362afffe69c72cfc4231e562d96e1cb923aca649c1b2f5d` | `fset_es_ohlcv_session_smoke` / `v1_range_position` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_ohlcv_session_smoke/v1_range_position/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:7056759e0577f5a3f57426944f48602bf6f5589d7d79597270e7db543aa8dc73` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_returns` | `fver_a6390d478bc31576bce270eadb93f8adfe215833ab403aba2e69af53e120eb8a` | `fset_es_ohlcv_session_smoke` / `v1_returns` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_ohlcv_session_smoke/v1_returns/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:0a8d29b9284d85e5306d76e0482ce6925c8384e9bb28247dc9564be02360ed90` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_rolling_range` | `fver_74ba4d642ce7b24dbdc06bc5bd16ce9c05bae3def8052056c439b3b6cdbc9169` | `fset_es_ohlcv_session_smoke` / `v1_rolling_range` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_ohlcv_session_smoke/v1_rolling_range/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:c9e133ed324b2b2ea168fa2b2672e99050161c91e34ea919f82eae2be2f96077` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_rolling_volatility` | `fver_18b5841a0d7f2fd7b86e5d650a21742190c1517dacc40dbb90854a1188191147` | `fset_es_ohlcv_session_smoke` / `v1_rolling_volatility` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_ohlcv_session_smoke/v1_rolling_volatility/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:1ad59e668cbed859460cb3dc672293cfc03f55d600d185477b46cfe1e9c1ec67` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_rth_flag` | `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9` | `fset_es_session_ctx_smoke` / `v1_rth_flag` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_rth_flag/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:29a64bad4966f696b1c18e72432ef2e5e00fff9ed767b6cd968493a7d4a6fa79` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_session_minute` | `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858` | `fset_es_session_ctx_smoke` / `v1_session_minute` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_session_ctx_smoke/v1_session_minute/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:94430bbd52270daf8a7e043c9a0e1c45b98e1f84b0f9ff0439d7119ddb3ef0ad` | `alpha_system.features.materialization.v1` |
| `base_ohlcv_volume_zscore` | `fver_759ee1b9da77fefb78aa5440b3de66dd217922ac576241858960cf1e8cef8a91` | `fset_es_ohlcv_session_smoke` / `v1_volume_zscore` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/features/materialized/fset_es_ohlcv_session_smoke/v1_volume_zscore/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:5c4ff7e2cbcbe4165a25c654d01466937c74b52560a53193f9c422256c84bbdf` | `alpha_system.features.materialization.v1` |

Additional value-free metadata:

| FeatureVersion id | FeatureRequest id | Materialization plan id | Lifecycle | Event window | Available window | Duplicate exposure status |
| --- | --- | --- | --- | --- | --- | --- |
| `fver_7ac2429f12ce6f7d494b7c0ab968446f2455da51863ebe471ddd8a224b6fa9f9` | `freq_658fe17db11d23540e4ed17d` | `fmat_1e11f0a487107b1f8522a242d30c327e860f6374b40f8be7174cb39f5a19cc7f` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |
| `fver_862f9b2d36e10b58d362afffe69c72cfc4231e562d96e1cb923aca649c1b2f5d` | `freq_e44777a9b6c5685aed764c32` | `fmat_6a15e7af1d5f0f41ba8d7c04f400d5af1aa39f44816008911a5c90f64583d0be` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |
| `fver_a6390d478bc31576bce270eadb93f8adfe215833ab403aba2e69af53e120eb8a` | `freq_7644d195221963a725953a50` | `fmat_ad16acddd211782555dfea0215f4e391c2ecffa443d41a1303006a7fb745b0ac` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |
| `fver_74ba4d642ce7b24dbdc06bc5bd16ce9c05bae3def8052056c439b3b6cdbc9169` | `freq_cd75d0b4aa48ba48c04e970b` | `fmat_c548138c1da279f401996416e4e634e91ebcff71bb329ac0836924e44294f7d2` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |
| `fver_18b5841a0d7f2fd7b86e5d650a21742190c1517dacc40dbb90854a1188191147` | `freq_af690f30c36a7bbd12b6d730` | `fmat_e9799e29b405e3fed943b97c5c9314a534ad6bed131da5d5f0c76f7dd7bc01d4` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |
| `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9` | `freq_67991722245329f35c0fa612` | `fmat_da18877497262c0ac7d33c744029214ab3f715fb89b38e101365de991158310a` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `NO_FINDINGS` |
| `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858` | `freq_f7d4e9c2f4c60c5c25f15ce2` | `fmat_a6ad8dc7369ed3a36fedb29ac0ce4bb63370c9cf540d78490cc9ff8e4fb53e20` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |
| `fver_759ee1b9da77fefb78aa5440b3de66dd217922ac576241858960cf1e8cef8a91` | `freq_c74b47e119cb7095e86dc709` | `fmat_099685c34d16e36c5049dfb5ff5c769ecb7ca841855be03e07bf4555bb822862` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-09T00:00:00+00:00` | `2024-01-02T00:01:05+00:00` to `2024-01-09T00:00:05+00:00` | `EQUIVALENCE_RECORDED` |

## LabelPack Lock

Research-scale consumers must bind to the `parquet_path` side of each registry
record. The registry reports `value_store_format=dual`; the JSONL side is not
locked as a research-scale input.

| Label id | LabelVersion id | LabelSpec id | DatasetVersion | Partition | `value_store_format` | `parquet_path` | `value_content_hash` | `value_schema_version` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fwd_ret_10m` | `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` | `lspec_15c26c4368bb432b0b0dc6e9` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/labels/materialized/lset_d17606e17ca9be56c06a70c21c6176ec214c61a957dc8c1cd88fa40aa89604fd/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:d691193911a2f72a821da02846dbc3bab377ad810b67b0761de72b83bbac1489` | `alpha_system.labels.materialization.v1` |
| `fwd_ret_30m` | `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` | `lspec_65ba5b5c9b4fa37e0e42b6ef` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/labels/materialized/lset_d17606e17ca9be56c06a70c21c6176ec214c61a957dc8c1cd88fa40aa89604fd/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:d691193911a2f72a821da02846dbc3bab377ad810b67b0761de72b83bbac1489` | `alpha_system.labels.materialization.v1` |
| `fwd_ret_5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `lspec_cd6523694c850c9943b2067e` | `dsv_databento_ohlcv_05404069799decb0` | `development_partition` | `dual` | `/home/yuke_zhang/alpha_data/alpha_system_parquet_smoke/labels/materialized/lset_355b408d6516452304866be98b0371ea7239f39657c4b33276dc81fee3db918d/dsv_databento_ohlcv_05404069799decb0/development_partition/values.parquet` | `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f` | `alpha_system.labels.materialization.v1` |

Additional value-free metadata:

| LabelVersion id | Materialization plan id | Lifecycle | Event window | Label available window | Exposure status |
| --- | --- | --- | --- | --- | --- |
| `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` | `lmat_5414f37fcd79928e69e8fcf53c4208f3dc07136c50002e50cab1124446ebed8e` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-08T23:50:00+00:00` | `2024-01-02T00:11:05+00:00` to `2024-01-09T00:00:05+00:00` | `NO_FINDINGS` |
| `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` | `lmat_5414f37fcd79928e69e8fcf53c4208f3dc07136c50002e50cab1124446ebed8e` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-08T23:30:00+00:00` | `2024-01-02T00:31:05+00:00` to `2024-01-09T00:00:05+00:00` | `NO_FINDINGS` |
| `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `lmat_e9fa63fe8a9a5f966f2a157390b1ef265e93048b82767ac96d060d7003725b94` | `REGISTERED` | `2024-01-02T00:01:00+00:00` to `2024-01-08T23:55:00+00:00` | `2024-01-02T00:06:05+00:00` to `2024-01-09T00:00:05+00:00` | `NO_FINDINGS` |

## Universe, Provenance, And Quality Reference

| Reference area | Locked status | Notes |
| --- | --- | --- |
| Universe coverage | DatasetVersion `dsv_databento_ohlcv_05404069799decb0` resolves with symbol universe `ES`, `NQ`, `RTY`. | FeaturePack and LabelPack records bind to that DatasetVersion and `development_partition`; symbol-level value coverage is not inspected in this phase and remains a `FUTCORE-P13` audit item. |
| `available_ts` presence | Present for every locked FeaturePack record. | All eight FeatureVersion records carry non-empty first/last `available_ts` windows. |
| `label_available_ts` presence | Present for every locked LabelPack record. | All three LabelVersion records carry non-empty first/last `label_available_ts` windows. |
| Session provenance | Present by registry contract for session features through input field `session_label` with role `SESSION_METADATA`. | `base_ohlcv_rth_flag` and `base_ohlcv_session_minute` expose this field. This is the registry's session-segment naming in the locked pack metadata. |
| `exchange_trade_date` provenance | Not exposed as a named FeaturePack or LabelPack input field in the locked registry records. | The DatasetVersion covers exchange-traded ES/NQ/RTY OHLCV bars, but this phase does not inspect value rows; downstream P13/P14 must confirm any required `exchange_trade_date` binding before diagnostics rely on it. |
| Quality flags | Present in every locked FeaturePack and LabelPack input contract as `quality_flags`. | DatasetVersion also carries `quality_report_hash`. |
| Missingness / gap flags | Recorded as gap semantics in input metadata, not as a separate materialized missingness summary in this lock. | Feature records cite `no_trade rows are gaps for trade logic`; label records cite dense-grid `no_trade` rows as gaps. P13/P14 must plan around any unresolved symbol or horizon cells. |

## Primary Horizon Coverage

| Pilot primary horizon | Locked LabelPack resolution | Status for downstream P13/P14 |
| --- | --- | --- |
| `5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` / `fwd_ret_5m` | Resolved. |
| `10m` | `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` / `fwd_ret_10m` | Resolved. |
| `15m` | none | Unresolved in the locked LabelPack set; P13/P14 must route around this gap or plan a later LabelSpec/FeatureRequest path. |
| `30m` | `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` / `fwd_ret_30m` | Resolved. |

## Universe To Pack Mapping

| Universe member | DatasetVersion binding | Locked FeaturePack refs | Locked LabelPack refs | Notes |
| --- | --- | --- | --- | --- |
| `ES` | `dsv_databento_ohlcv_05404069799decb0` | All eight FeatureVersion refs in this lock. | `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_30m`; no `fwd_ret_15m`. | DatasetVersion universe includes `ES`; pack ids are locked by registry binding. |
| `NQ` | `dsv_databento_ohlcv_05404069799decb0` | All eight FeatureVersion refs in this lock. | `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_30m`; no `fwd_ret_15m`. | DatasetVersion universe includes `NQ`; symbol-level pack coverage remains a `FUTCORE-P13` audit item. |
| `RTY` | `dsv_databento_ohlcv_05404069799decb0` | All eight FeatureVersion refs in this lock. | `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_30m`; no `fwd_ret_15m`. | DatasetVersion universe includes `RTY`; symbol-level pack coverage remains a `FUTCORE-P13` audit item. |

## Carried-Forward Observations For `FUTCORE-P13` / `FUTCORE-P14`

- The locked records report `value_store_format=dual`; downstream research-scale
  scans must consume the Parquet pointer side and never use JSONL as the
  research-scale value source.
- The locked pack partition is `development_partition`. Validation, locked, or
  shadow partition pack binding must be separately audited before use.
- The primary `15m` label horizon does not resolve in this lock. This phase
  records the gap only and does not fill it.
- `exchange_trade_date` is not exposed as a named input field in the locked
  FeaturePack or LabelPack registry contracts. Any downstream study that needs
  that field must prove the binding through an authorized later audit.
- Symbol-level pack coverage for ES/NQ/RTY is registry-bound through the
  DatasetVersion but not value-inspected here.

## Boundaries

- No raw provider file, provider response, Parquet value file, SQLite registry,
  feature value, or label value is committed by this lock.
- No external provider API call was made for this phase.
- No `src/alpha_system/**` consumed primitive was edited.
- No AlphaSpec, diagnostic, profitability, tradability, strategy-readiness,
  broker, live, paper, order, account, deployment, or production claim is made.
