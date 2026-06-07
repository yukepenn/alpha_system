# Feature Materialization

`alpha_system.features.engine` plans and executes local-only feature
materialization for an approved `FeatureSetSpec`. It turns accepted
DatasetVersion partition inputs into `FeatureValueRecord` rows and writes JSONL
outputs only under `ALPHA_DATA_ROOT`.

The engine does not define feature formulas, read provider files, call external
providers, register features, create a FeatureStore, or make alpha/tradability
claims.

## Objects

`FeatureMaterializationPlan` records the resolved `FeatureSetSpec`, accepted
DatasetVersion id, partition id, `ALPHA_DATA_ROOT`, output path, feature-version
ids, governance metadata, and deterministic plan/idempotency keys.

`FeatureMaterializationInputs` carries one FLF-P01 `AcceptedDatasetVersion`
handle plus canonical in-memory OHLCV, BBO, or dense-grid row mappings. The
engine reconstructs records through the consumption adapter and canonical
`from_mapping` loaders.

`FeatureMaterializationResult` reports the plan, produced
`FeatureValueRecord`s, dry-run state, output path, and whether a write changed
the local output file.

## Admission

Materialization fails closed unless every feature in the `FeatureSetSpec` is an
implementation-eligible `FeatureSpec` with a causal, live-compatible window and
an explicit `available_ts` rule. The engine also requires an approved family
definition for every feature. Those definitions carry the FLF-P05
`FeatureRequestGateDecision`; the engine consumes that decision and rejects
missing, mismatched, or non-admitted definitions.

The accepted DatasetVersion boundary is enforced by requiring an
`AcceptedDatasetVersion` handle and by using `build_canonical_input_views`,
`build_ohlcv_input_view`, `build_bbo_input_view`, or
`dense_grid_bars_from_mappings`. The engine does not read raw files or provider
artifacts.

Partition use is routed through
`require_governance_metadata_for_locked_partition_use(...)` via the consumption
adapter. Locked-test partition access requires governance contamination
metadata.

## Execution

`build_feature_materialization_plan(...)` validates the feature set, accepted
DatasetVersion handle, partition gate, and output path. Output paths are
deterministic:

```text
$ALPHA_DATA_ROOT/features/materialized/<feature_set_id>/<feature_set_version>/<dataset_version_id>/<partition_id>/values.jsonl
```

`materialize_features(..., dry_run=True)` validates the plan and approved
definitions without writing values. Non-dry-run execution dispatches each
feature to its approved family calculator and validates that every output is a
`FeatureValueRecord` whose `available_ts` is present and does not precede
`event_ts`.

Outputs are rendered as deterministic JSONL and written atomically. Re-running
the same plan with the same inputs leaves identical output unchanged.

## Semantics

BBO rows retain `missing_bbo` and `bbo_quarantined` flags from FLF-P04 family
logic; there is no quote filling or interpolation in the engine. Dense-grid
synthetic no-trade rows must carry the canonical no-trade signature before they
are converted to OHLCV input rows, so downstream trade-bar logic still treats
them as gaps rather than trades.

Session-context features (`rth_flag`, `eth_flag`, `session_minute`) declare
their canonical `session_label` input as `SESSION_METADATA` through
`FeatureInputSpec.input_metadata.field_roles`. The runtime no-lookahead guard
therefore treats `session_label` as point-in-time session metadata, not a label
input.

## Storage Tier

The `values.jsonl` output is the **audit/small tier** of the two-tier value
storage policy in [ADR-0006](../../decisions/0006-feature-label-value-storage.md):
deterministic JSONL is sanctioned for tiny fixtures, audit/debug output, MVP
smoke, and small seed packs. JSONL is **not** the permanent large-scale research
store; multi-year, multi-symbol research-scale value matrices are intended to
move to local Parquet (read via DuckDB/Polars) under the deferred follow-up
`FEATURE_LABEL_PARQUET_SINK_V1`. The FeatureRegistry stores only metadata and a
value-path pointer, never the values.

## Boundary

Materialized feature values are local-only and are never committed. This phase
adds no FeatureStore or FeatureRegistry persistence, no quality/coverage report,
no provider call, no strategy/backtest/portfolio behavior, no broker/live/paper
scope, and no alpha, profitability, or tradability claim.
