# Producer Path Integration

`FCFP-P14` routes the local scaleout producer path to the V1 fast
materializer by default while keeping the reference engine selectable as the
oracle/fallback.

## Engine Selection

`alpha scaleout feature-pack` accepts:

```bash
--engine v1
--engine reference
```

The default is `v1`. Reference execution remains available with
`--engine reference`; it is not deleted or weakened.

Engine selection affects only the producer implementation. It does not enter
`feature_version_id`, `label_version_id`, unit identity, or request identity.
V1 materializes values for the existing governed identities.

## V1 Driver Path

In execute mode the scaleout driver dispatches selected units to
`PackMaterializer` when `engine=v1`. The V1 path:

- builds the same governed feature definitions used for identity preview;
- resolves the family pack with `build_fast_feature_pack`;
- writes Parquet-backed values through the shared value-store helpers;
- registers features through `PackMaterializer.register_pack` and
  `FeatureStore`;
- verifies the official registry round trip after registration.

The reference path remains selectable and continues to use the per-family
reference executors.

## Idempotency

Completed units skip only when checkpoint evidence and official registry truth
agree. The registry-truth check is engine-aware: a reference-produced registry
record is not sufficient evidence that a V1 unit has completed, and a
V1-produced record is not sufficient evidence for a reference-engine rerun.

If a checkpoint is absent but the official registry resolves every previewed
feature identity to existing values for the selected engine, the driver records
a checkpoint marker and skips the completed unit. Partial or mismatched
registry evidence fails closed into normal execution.

## Resolver Smoke Procedure

The resolver smoke materializes a bounded-real representative slice through the
default V1 path, then resolves exact feature/label locks through the official
runtime resolver:

1. Back up local registries under `ALPHA_DATA_ROOT`.
2. Run selected bounded-real feature units with `--engine v1`.
3. Materialize at least one governed label horizon through the V1 label
   materializer on matching accepted DatasetVersions.
4. Resolve exact `fver_...` and `lver_...` locks with
   `evaluate_runtime_entry_request` and `resolve_runtime_input_pack`.
5. Verify stale or fuzzy controls fail closed with exact-id errors.

The smoke report is value-free. It records counts, statuses, engine routing,
identity stability, and registry-write path confirmation only.

