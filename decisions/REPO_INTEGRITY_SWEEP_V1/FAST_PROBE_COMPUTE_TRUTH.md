# Repo Integrity Sweep V1 - Fast Probe Compute Truth

## Today

`fast_probe` is a read path over already materialized local parquet values. It
does not compute feature/label values on demand and does not write registry
records.

Current path:

1. `SliceSpec` carries fver/lver, relative paths, DatasetVersion, partition, and
   bounded probe metadata.
2. `FeatureLabelPackResolver` resolves registered feature/label handles
   value-free through the registries.
3. `fast_probe` loads parquet values via `load_parquet_values`.
4. Missing/unloadable inputs return an unresolved readout; no values are
   fabricated and no shot should be interpreted as spent.

## Clarified Failure Classes

| Condition | Current behavior |
| --- | --- |
| Missing dependency | `MISSING_DEPENDENCY` unresolved readout |
| Missing data root | `ALPHA_DATA_ROOT_MISSING` unresolved readout |
| Registry/resolver unavailable | `REGISTRY_UNAVAILABLE` where the resolver provides that typed reason |
| Deprecated pack pin | `DEPRECATED_PACK_PIN` |
| DatasetVersion mismatch | `DATASET_VERSION_MISMATCH` |
| Materialized parquet missing | `VALUE_FILE_MISSING` |
| Pack/reference absent from registry | `TRUE_DATA_GAP` |

## Compute-On-Demand Boundary

Compute-on-demand is not implemented here. A future fast lane must be a separate
approved feature with these constraints:

- parity-gated against the reference materialization engine;
- ephemeral scratch only unless a separate materialization command writes
  registry-backed values;
- no second truth for value/accounting math;
- no registry write from exploratory fast-probe execution;
- same public failure vocabulary as this sweep.
