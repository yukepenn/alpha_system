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
  `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f`,
  `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978`
- LabelPack ref:
  `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395`

The pack records report `value_store_format=dual` and expose Parquet reference
strings, content hashes, and schema versions. Research-scale consumers must use
the Parquet side of the locked records; JSONL is not a research-scale input.

## Binding Rules

- The universe remains `ES`, `NQ`, `RTY` per
  `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`.
- `FUTCORE-P13` audits symbol-level and partition coverage before downstream
  diagnostics rely on the lock.
- `FUTCORE-P14` binds StudySpecs to these DatasetVersion, FeaturePack, and
  LabelPack ids unless a later reviewed phase explicitly changes the input pack.
- Missing features or labels are observations only here and route to later
  FeatureRequest/LabelSpec work.

This page is value-free. It does not commit market data, materialized feature or
label values, Parquet files, SQLite registries, provider responses, or run-local
artifacts.
