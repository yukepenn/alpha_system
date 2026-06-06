# End-to-End Runtime Dry Run

RT-P25 adds `alpha_system.runtime.dry_run`, a local orchestration smoke for the
Research Runtime. It runs only tiny synthetic fixtures and in-memory synthetic
resolvers. It does not call external providers, read raw provider files,
materialize runtime values, or write heavy artifacts.

## Pipeline Order

The dry run sequences existing runtime surfaces in this order:

```text
AlphaSpec + StudySpec + StudyInputPack
  -> RuntimeEntryRequest
  -> RuntimeInputPack through resolve_runtime_input_pack
  -> RuntimeRequest / RuntimePlan / StudyRunSpec
  -> factor diagnostics
  -> label diagnostics
  -> session, regime, RTH, ETH split diagnostics
  -> cross-market diagnostics
  -> simple signal probe
  -> cost stress with base and double_cost
  -> bounded VariantBudget grid guard
  -> NoLookaheadRuntimeAudit
  -> EvidenceDraft
  -> ReferenceCandidateHandoff
  -> RuntimeToolResult / RuntimeRunSummary
```

The most advanced forward state is `REFERENCE_HANDOFF_READY`. Terminal
non-success states are `REJECTED`, `INCONCLUSIVE`, and `BLOCKED`, each with
visible `RejectionReasonRecord` payloads.

## Synthetic Fixtures

The dry run reuses committed synthetic fixtures under `tests/fixtures/runtime/`:

- `probe/synthetic_signal_probe_rows.json`
- `diagnostics/splits/synthetic_observations.json`
- `diagnostics/cross_market/synthetic_observations.json`

It also uses private in-memory synthetic `DatasetVersion`, FeatureStore, and
LabelRegistry stand-ins so the input resolver exercises the accepted
DatasetVersion and Feature/Label pack boundary without requiring local market
data. These stand-ins are metadata only and are not market evidence.

## Local Command

From the repository root:

```bash
PYTHONPATH=src python -c "from alpha_system.runtime.dry_run import run_runtime_dry_run; result = run_runtime_dry_run(); print(result.dry_run_status, result.terminal_decision_state.value)"
```

In a normal editable install, `PYTHONPATH=src` is not needed.

## Warning Path

Clean runners usually do not have a local registry or materialized data. When
the configured registry path is absent, the dry run records
`PASS_WITH_WARNINGS` for the dry-run smoke and states that it used in-memory
synthetic resolvers. This is not a phase verdict and not evidence that local
real data exists. It is a truthful wiring result for the synthetic dry run.

## Interpretation

This dry run is an orchestration smoke only. A diagnostic PASS is not alpha
validation. A signal probe is not a strategy candidate. A bounded grid is not
promotion. An `EvidenceDraft` is not a candidate. A
`ReferenceCandidateHandoff` is not Reference validation, and the next required
gate remains `REFERENCE_VALIDATION_REQUIRED`.

The module makes no alpha, tradability, profitability, broker, paper, live,
order-routing, account, deployment, or production-readiness claim.
