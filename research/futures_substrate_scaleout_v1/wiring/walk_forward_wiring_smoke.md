# FUTSUB-P24 Walk-Forward Wiring Smoke

Phase: `FUTSUB-P24`  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Artifact class: value-free wiring smoke summary

## Scope

This smoke summary records that purged / embargoed walk-forward metadata is
available through runtime diagnostics by calling the existing
`alpha_system.experiments.splits` primitives.

No market data, feature values, label values, provider payloads, local registry
rows, Parquet files, SQLite files, logs, caches, or run-local artifacts are
embedded here.

## Callable Path

- `alpha_system.runtime.diagnostics.splits.build_walk_forward_split_plan`
- `alpha_system.runtime.diagnostics.splits.build_walk_forward_split_plan_for_observations`
- `alpha_system.runtime.diagnostics.factor.build_factor_diagnostics_report`
  with opt-in `walk_forward_config`
- `alpha_system.runtime.diagnostics.factor.build_factor_diagnostics_run`
  with opt-in `walk_forward_config`

## Protocol Coverage

The runtime exposes bounded, overridable hooks for:

| Protocol | Runtime enum |
| --- | --- |
| STRUCTURAL | `DiagnosticsHalfLifeProtocol.STRUCTURAL` |
| MEDIUM | `DiagnosticsHalfLifeProtocol.MEDIUM` |
| FAST | `DiagnosticsHalfLifeProtocol.FAST` |

The protocol names are configuration labels only and make no validity,
promotion, profitability, tradability, or production claim.

## Smoke Case

Synthetic in-memory observations request:

```text
half_life_protocol = FAST
train_window = 5
validation_window = 2
step_size = 2
purge_gap = 1
embargo_gap = 1
min_fold_count = 2
sample_count = 12
```

Expected value-free fold metadata:

```text
fold_count = 3
fold_0 train_indices = [0, 1, 2, 3]
fold_0 validation_indices = [5, 6]
fold_1 train_indices = [2, 3, 4, 5]
fold_1 validation_indices = [7, 8]
```

Too-small input is expected to fail closed with
`walk_forward_split_unavailable` and no unsplit fallback.

## Validation Results

Validation results are recorded in
`handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P24.md`.
