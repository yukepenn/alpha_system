# Materialization Plan

`FUTSUB-P05` pins the restart-safe, chunked materialization contract consumed by
`FUTSUB-P06` through `FUTSUB-P13` and `FUTSUB-P16` through `FUTSUB-P20`.

The full plan is recorded in
`research/futures_substrate_scaleout_v1/materialization/batch_plan.md`.

## Contract

- Batch grain is bounded to governed families only: eight FeaturePack families
  and five LabelPack groups over ES, NQ, RTY and years 2018 through 2026.
- Feature units are `family x symbol x year`; label units add `horizon` or
  `event_horizon`.
- Every unit has a deterministic `mbu_` identity derived from canonical
  value-free metadata and the accepted DatasetVersion id or ids.
- Research-scale values must be Parquet. JSONL is not allowed for full-window
  research-scale materialization.
- Checkpoints, manifests, registry backups, Parquet values, and SQLite
  registries are local-only under `ALPHA_DATA_ROOT`.
- A unit is skipped on resume only when completion marker, registry record,
  DatasetVersion id, and value content hash all match.
- Registry writes are serialized by `resource_class: materialization_registry`
  and by the local per-run registry guard.

## Budgets

- Feature materialization budget: `216` units, `118,800,000` output rows, `216`
  Parquet files.
- Label materialization budget: `729` units, `400,950,000` output rows, `729`
  Parquet files.
- Total governed budget: `945` units and `945` research-scale Parquet value
  files.

## Dataset Gate

The committed P02 acceptance summary currently records `0` accepted and `27`
blocked DatasetVersions. Later materialization phases must therefore resolve the
local acceptance lock and fail closed unless the exact DatasetVersion state is
`ACCEPTED` or `ACCEPTED_WITH_WARNINGS`. Registered-only ids are not executable.

## Safety

`FUTSUB-P05` is dry-run / plan only. It did not execute materialization, write
values, write SQLite registries, write checkpoint markers, call providers, or
make live, paper, broker, order, deployment, profitability, or tradability
claims.
