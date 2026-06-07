# Label Materialization

`alpha_system.labels.engine` plans and executes local-only label
materialization for approved governance-bound label definitions. It turns one
accepted DatasetVersion partition into `LabelValueRecord` rows and writes JSONL
outputs only under `ALPHA_DATA_ROOT`.

The engine does not define labels, read provider files, call external
providers, register labels, expose labels as features, or make alpha,
tradability, profitability, strategy, backtest, portfolio, broker, live, or
paper-trading claims.

## Objects

`LabelMaterializationPlan` records the approved label contracts, accepted
DatasetVersion id, partition id, optional instrument filter, `ALPHA_DATA_ROOT`,
output path, label-version ids, label-spec ids, dry-run flag, governance
metadata, and deterministic plan/idempotency keys.

`LabelMaterializationInputs` carries one FLF-P01 `AcceptedDatasetVersion`
handle plus canonical in-memory OHLCV, BBO, or dense-grid row mappings. The
engine reconstructs input views through `alpha_system.features.consumption` and
the canonical `from_mapping` loaders only.

`LabelMaterializationResult` reports the plan, produced `LabelValueRecord`s,
dry-run state, planned input and label counts, output path, runtime, and
whether a local output write changed the file.

## Admission

Materialization fails closed unless every input definition is an approved label
family definition from `labels.families.fixed_horizon`,
`labels.families.cost_adjusted`, `labels.families.path`, or
`labels.families.event`. Those definitions must carry a validated governed
`lspec_` `LabelSpec`, a matching `LabelContractSpec`, and a matching
`LabelVersion`.

The label lifecycle gate is explicit: `label_lifecycle_state` must be
`MATERIALIZATION_ALLOWED`. The DatasetVersion lifecycle must be `VERSIONED` or
`READY_FOR_RESEARCH`.

The label-only boundary is enforced before planning and execution. Each
contract must declare `labels_only` as the legal consumer, must keep
forward-looking data legal only for labels, and must expose a
`label_available_ts` derivation rule. Attempts to route a label into live
feature inputs are rejected through the existing governance leakage guard.

## Dataset And Partition Boundary

The accepted DatasetVersion boundary is enforced by requiring an
`AcceptedDatasetVersion` handle and by using `build_ohlcv_input_view`,
`build_bbo_input_view`, or `dense_grid_bars_from_mappings`. The engine never
reads raw provider files or local data paths.

Partition use is routed through
`require_governance_metadata_for_locked_partition_use(...)` via the consumption
adapter. Locked-test and latest-shadow use requires substantive governance
contamination metadata.

## Execution

`build_label_materialization_plan(...)` validates the definitions, accepted
DatasetVersion handle, partition gate, label-only consumer, and output path.
Output paths are deterministic:

```text
$ALPHA_DATA_ROOT/labels/materialized/<label_set_id>/<dataset_version_id>/<partition_id>/values.jsonl
```

`materialize_labels(...)` validates the plan and definitions. If
`plan.dry_run` is true, it reports intended scope without computing or writing
values. Non-dry-run execution builds canonical input views, dispatches each
definition to its existing family calculator, validates the returned
`LabelValueRecord`s, and writes deterministic JSONL atomically. Re-running the
same plan with the same inputs leaves identical output unchanged.

## `label_available_ts`

Each family computes `label_available_ts` from the governed `LabelSpec`
availability policy, label horizon, and path or terminal-row availability. The
engine validates every emitted record again:

- `label_available_ts` must be present and timezone-aware.
- `label_available_ts` must be at or after `horizon_end_ts`.
- `label_available_ts` must not precede governed `LabelSpec.availability_time`.

Future data is legal only inside label-family horizon/path calculations. A
materialized label remains a research target, not a live feature and not a
promoted candidate.

## Storage Tier

The `values.jsonl` output is the **audit/small tier** of the two-tier value
storage policy in [ADR-0006](../../decisions/0006-feature-label-value-storage.md):
deterministic JSONL is sanctioned for tiny fixtures, audit/debug output, MVP
smoke, and small seed packs. The **research-scale tier is local Parquet**
(`values.parquet` + sidecar manifest, read via Polars), now implemented by
`FEATURE_LABEL_PARQUET_SINK_V1` through `core/value_store.py`. Select the tier
with `alpha label materialize --execute --value-store {jsonl,parquet,dual}`
(default `dual` writes both). The LabelRegistry stores only metadata and the
value-path pointers (`parquet_path`, output path, `value_store_format`,
`value_content_hash`), never the values.

## Boundary

Materialized label values are local-only and are never committed. This phase
adds no LabelStore or LabelRegistry persistence, no label audit module, no
quality/coverage bundle, no provider call, no strategy/backtest/portfolio
behavior, no broker/live/paper scope, and no alpha, profitability, or
tradability claim.
