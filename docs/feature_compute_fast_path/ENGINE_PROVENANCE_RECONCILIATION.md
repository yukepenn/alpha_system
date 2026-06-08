# Engine Provenance And Reconciliation

FCFP-P12 records producer provenance as registry metadata, separate from
content-addressed feature or label identity.

## Registry Fields

Feature registry records now carry:

- `producer_engine_id`: the engine that produced the value series.
- `value_schema_version`: the value payload schema emitted by the value store.

Reference feature registrations default to:

```text
alpha_system.features.reference.materializer.v1
```

Fast feature registrations use:

```text
alpha_system.features.fast.pack_materializer.v1
```

Fast label registrations already thread label provenance through
`LabelRegistry.register_materialized_label` registry metadata and lineage:

```text
producer_engine_id = alpha_system.labels.fast.pack_materializer.v1
value_schema_version = alpha_system.labels.fast.values.v1
```

These fields are descriptive provenance. They do not enter
`FeatureVersion.derive(FeatureSpec)` or `LabelVersion.derive(LabelContractSpec)`,
and they do not weaken exact resolver semantics.

## Reconciliation Policy

Reference-engine outputs that already exist remain the parity reference. V1 may
reconcile against them, but it must not silently overwrite or interleave values
inside the same logical series.

Allowed branches:

- identical or within documented tolerance: keep the existing valid reference
  output, tag producer provenance, and do not overwrite;
- beyond documented tolerance: block silent mixing. Treat the difference as a V1
  bug, explicitly bump `value_schema_version`, or re-materialize through the
  official keystone path under a governed phase.

The reconciliation helper in `alpha_system.features.fast.reconciliation` reads
Parquet value stores through `core.value_store.load_parquet_values` when file
inputs are used and emits only aggregate statistics: counts, tolerances,
max/median absolute diffs, classifications, and decisions. It writes no feature
or label values and performs no direct SQLite writes.

## Identity Boundary

Producer provenance is not an identity input:

- `feature_version_id` remains derived only from `FeatureSpec` content.
- `label_version_id` remains derived only from `LabelContractSpec` content.
- request provenance and producer provenance are excluded from keystone identity.
- a same-identity existing reference record refuses a fast overwrite without an
  explicit provenance/schema boundary.

The unit test
`tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py::test_feature_store_records_reference_and_fast_provenance_without_changing_identity`
asserts the feature identity invariant across reference and fast producer
provenance.
