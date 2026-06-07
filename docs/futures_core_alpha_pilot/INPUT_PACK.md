# Futures Core Alpha Pilot Input Pack

`FUTCORE-P03` locks the registry-resolved input pack for
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` by reference only. The canonical lock is:

- `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`

Downstream data-contract audit and StudySpec phases bind to that lock rather
than resolving arbitrary paths or ad hoc pack ids.

## Locked References

- DatasetVersion:
  `dsv_databento_ohlcv_05404069799decb0`
- FeaturePack refs:
  `fver_7ac2429f12ce6f7d494b7c0ab968446f2455da51863ebe471ddd8a224b6fa9f9`,
  `fver_862f9b2d36e10b58d362afffe69c72cfc4231e562d96e1cb923aca649c1b2f5d`,
  `fver_a6390d478bc31576bce270eadb93f8adfe215833ab403aba2e69af53e120eb8a`,
  `fver_74ba4d642ce7b24dbdc06bc5bd16ce9c05bae3def8052056c439b3b6cdbc9169`,
  `fver_18b5841a0d7f2fd7b86e5d650a21742190c1517dacc40dbb90854a1188191147`,
  `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9`,
  `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858`,
  `fver_759ee1b9da77fefb78aa5440b3de66dd217922ac576241858960cf1e8cef8a91`
- LabelPack refs:
  `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`,
  `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941`,
  `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a`

The pack records report `value_store_format=dual` and expose Parquet reference
strings, content hashes, schema versions, and point-in-time availability
windows. Research-scale consumers must use the Parquet side of the locked
records; JSONL is not a research-scale input.

## Coverage Notes

- The DatasetVersion universe remains `ES`, `NQ`, `RTY` per
  `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`.
- All locked FeaturePacks carry `available_ts`; all locked LabelPacks carry
  `label_available_ts`.
- Locked session features expose session provenance through the registry field
  `session_label` with role `SESSION_METADATA`; `exchange_trade_date` is not a
  named locked-pack input field and remains a downstream audit item.
- Primary horizons `5m`, `10m`, and `30m` resolve. Primary horizon `15m` does
  not resolve in this lock and must be planned around by `FUTCORE-P13` /
  `FUTCORE-P14`.

This page is value-free. It does not commit market data, materialized feature or
label values, Parquet files, SQLite registries, provider responses, or run-local
artifacts.
