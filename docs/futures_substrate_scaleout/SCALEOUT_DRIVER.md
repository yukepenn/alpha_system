# Scaleout Materialization Driver

`FUTSUB-P06` adds the reusable FeaturePack scaleout driver for the futures
substrate materialization phases. The driver is orchestration only: feature
formulas remain in the approved family modules, canonical rows are loaded
through `data.foundation.canonical_loader`, and registry writes flow through
`FeatureStore.register_materialized_feature` via the governed seed-pack
operator.

## Command

Dry-run planning is the default and writes no values:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/base_ohlcv.json \
  --rollout bounded-real \
  --json
```

Execution is explicit and local-only:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack \
  --config configs/features/scaleout/base_ohlcv.json \
  --rollout bounded-then-full \
  --execute \
  --alpha-data-root "$ALPHA_DATA_ROOT" \
  --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite"
```

`bounded-then-full` runs the 2024 ES/NQ/RTY bounded-real units first. Full-window
expansion is skipped if any bounded-real unit fails. `full-window` materializes
the accepted window directly, and `bounded-real` runs only the bounded set.

## Acceptance Gate

The planning grid is built from
`configs/features/scaleout/dataset_version_inventory.json` plus the value-free
P02 acceptance summary. Execution still requires an exact persisted
DatasetVersion acceptance lock in the local dataset registry. Missing locks,
`BLOCKED` locks, or lock states that disagree with the planning summary fail
closed before canonical rows are loaded or feature values are written.

The base OHLCV phase uses DatasetVersion-level fallback for 2018: the blocked
2018 `ohlcv_1m` DatasetVersion is excluded rather than fabricating per-symbol
acceptance. The full accepted materialization window for this phase is therefore
2019 through 2026 for ES, NQ, and RTY. 2019 and 2026 retain their warning
metadata through `ACCEPTED_WITH_WARNINGS`.

## Values And Ledger

Research-scale values are Parquet-only. JSONL is used only for local checkpoint
ledger records under `ALPHA_DATA_ROOT`, not as the research-scale feature store.
The ledger records each unit's family, schema, symbol, year, DatasetVersion id,
FeatureSet, status, Parquet path, content hash, and row count. Completed units
are skipped on rerun; missing or incomplete completion evidence fails closed
instead of silently rematerializing.

Registry writes are serial inside the driver. Workflow 2 still owns the outer
`materialization_registry` resource serialization across phases.

## Boundaries

The driver does not call providers, read raw provider data, open broker/live/
paper-trading surfaces, route orders, deploy, create PRs, or make profitability
or tradability claims. Values, SQLite registries, checkpoint ledgers, and
Parquet manifests stay local-only under `ALPHA_DATA_ROOT`.
