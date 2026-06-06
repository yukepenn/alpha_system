# Real DatasetVersion Runtime Smoke

`alpha_system.runtime.smoke` is a local-only runtime smoke for RT-P21. It
exercises the assembled Research Runtime against one accepted local
Feature/Label Foundation `DatasetVersion` when the operator has already
materialized and registered the data locally.

Exact operator command:

```bash
ALPHA_DATA_ROOT=/abs/local/alpha_data ALPHA_DATASET_VERSION_ID=dsv_... ALPHA_FEATURE_PACK_REFS=fver_... ALPHA_LABEL_PACK_REFS=lver_... python -m alpha_system.runtime.smoke
```

Optional explicit governance-handle overrides are
`ALPHA_FEATURE_REQUEST_IDS`, `ALPHA_LABEL_SPEC_IDS`,
`ALPHA_RUNTIME_SMOKE_PARTITION_ID`, and
`ALPHA_RUNTIME_SMOKE_SESSION_SCOPE`. If the feature, label, or partition
metadata is not supplied explicitly, the smoke attempts read-only discovery from
`$ALPHA_DATA_ROOT/registry/features.sqlite` and
`$ALPHA_DATA_ROOT/registry/labels.sqlite`.

The smoke does this bounded path only:

```text
resolve_dataset_version
  -> RuntimeEntryRequest / StudyInputPack
  -> RuntimeInputPack with FeatureStore and LabelStore handles
  -> Tier 0 factor diagnostics
  -> Tier 0 label diagnostics
  -> cost stress including double_cost
  -> no-lookahead audit
  -> EvidenceDraft
  -> RuntimeToolResult / RuntimeRunSummary
```

It makes no external Databento or IBKR call, does not read raw provider files,
and does not read `.dbn`, `.zst`, parquet, arrow, or feather files. It consumes
only the local DatasetVersion registry plus registered Feature/Label handles.
The diagnostic observations are tiny deterministic smoke inputs used to verify
wiring; they are not alpha evidence and are not committed.

If `ALPHA_DATA_ROOT`, `$ALPHA_DATA_ROOT/registry/datasets.sqlite`, the
FeatureStore registry, the LabelStore registry, an admissible DatasetVersion, or
the selected Feature/Label handles are absent, the smoke returns
`PASS_WITH_WARNINGS` with the reason and exits successfully. This keeps CI and
clean checkouts safe while preserving the exact command an operator can run on a
machine with local accepted data.

Accepted DatasetVersion posture:

- The DatasetVersion is resolved through
  `alpha_system.data.foundation.version_registry.resolve_dataset_version`.
- The lifecycle state must be `VERSIONED` or `READY_FOR_RESEARCH`.
- Feature inputs must carry `available_ts`; label inputs must carry
  `label_available_ts`.
- Labels are never exposed as live feature inputs.
- The smoke emits value-free summaries only and writes no runtime artifacts.

This smoke is not alpha validation, not Reference truth, not a strategy
candidate, not a factor promotion path, and not evidence of tradability,
profitability, paper readiness, live readiness, or production readiness.
