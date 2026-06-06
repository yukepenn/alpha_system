# Research Runtime Naming Conventions

This document is the authoritative naming source for the Research Runtime MVP.
Later phases extend the names below additively and keep behavior in the mapped
runtime modules. Names are descriptive contracts for one approved study at a
time; they do not imply alpha, tradability, profitability, promotion,
Reference validation, strategy readiness, portfolio readiness, paper readiness,
live readiness, broker operation, or production readiness.

## Package Layout

The runtime package root is `alpha_system.runtime`. RT-P02 creates only package
namespaces needed for clean imports:

- `alpha_system.runtime.contracts`
- `alpha_system.runtime.diagnostics`
- `alpha_system.runtime.diagnostics.factor`
- `alpha_system.runtime.diagnostics.label`
- `alpha_system.runtime.diagnostics.splits`
- `alpha_system.runtime.diagnostics.cross_market`
- `alpha_system.runtime.cost`

Reserved single-module homes for later phases are documented here but are not
created by RT-P02: `input_resolver`, `probe`, `grid`, `audit`, `decisions`,
`evidence`, `handoff`, `artifact_policy`, `tool_results`, and `reports`.

## Object Model

Runtime object names use PascalCase. Module names use lowercase snake_case.
Object names describe the artifact or contract, not an outcome claim. The
module mapping below is the source of truth for future phase file placement.

| Object | Future module home |
| --- | --- |
| `RuntimeRequest` | `alpha_system.runtime.contracts.request` |
| `RuntimePlan` | `alpha_system.runtime.contracts.plan` |
| `RuntimeInputPack` | `alpha_system.runtime.input_resolver` |
| `StudyRunSpec` | `alpha_system.runtime.contracts.run_spec` |
| `StudyRunRecord` | `alpha_system.runtime.contracts.run_record` |
| `StudyRunManifest` | `alpha_system.runtime.contracts.manifest` |
| `RuntimeArtifactManifest` | `alpha_system.runtime.contracts.artifacts` |
| `DiagnosticsRunSpec` | `alpha_system.runtime.diagnostics.contracts` |
| `DiagnosticsRunRecord` | `alpha_system.runtime.diagnostics.contracts` |
| `FactorDiagnosticsReport` | `alpha_system.runtime.diagnostics.factor.report` |
| `LabelDiagnosticsReport` | `alpha_system.runtime.diagnostics.label.report` |
| `RegimeSplitSpec` | `alpha_system.runtime.diagnostics.splits.report` |
| `RegimeSplitReport` | `alpha_system.runtime.diagnostics.splits.report` |
| `SessionSplitReport` | `alpha_system.runtime.diagnostics.splits.report` |
| `CrossMarketDiagnosticsReport` | `alpha_system.runtime.diagnostics.cross_market.report` |
| `DiagnosticsQualityGate` | `alpha_system.runtime.diagnostics.quality_gate` |
| `SignalProbeSpec` | `alpha_system.runtime.probe` |
| `SignalProbeReport` | `alpha_system.runtime.probe` |
| `BoundedGridSpec` | `alpha_system.runtime.grid` |
| `BoundedGridRunRecord` | `alpha_system.runtime.grid` |
| `VariantBudget` | `alpha_system.runtime.grid` |
| `CostModelVersion` | `alpha_system.runtime.cost.model` |
| `CostStressSpec` | `alpha_system.runtime.cost.stress` |
| `CostSensitivityReport` | `alpha_system.runtime.cost.stress` |
| `NoLookaheadRuntimeAudit` | `alpha_system.runtime.audit` |
| `RejectionReasonRecord` | `alpha_system.runtime.decisions` |
| `RuntimeStopCondition` | `alpha_system.runtime.decisions` |
| `EvidenceDraft` | `alpha_system.runtime.evidence` |
| `ReferenceCandidateHandoff` | `alpha_system.runtime.handoff` |
| `RuntimeToolResult` | `alpha_system.runtime.tool_results` |
| `RuntimeRunSummary` | `alpha_system.runtime.reports` |
| `RuntimeReportCard` | `alpha_system.runtime.reports` |
| `RuntimeCachePolicy` | `alpha_system.runtime.artifact_policy` |
| `RuntimeConcurrencyPolicy` | `alpha_system.runtime.artifact_policy` |
| `FeatureLabelPackResolver` | `alpha_system.runtime.input_resolver` |

The RT-P01 `RuntimeEntryRequest`, `RuntimeEntryResult`, `RuntimeEntryStatus`,
`RuntimeEntryReason`, `RuntimeEntryOutcome`, and
`evaluate_runtime_entry_request` names remain in
`alpha_system.runtime.entry_contract` and continue to be re-exported from
`alpha_system.runtime`.

## Lifecycle States

Lifecycle state names are uppercase snake case. Runtime records may only use
the lifecycle names below until a later reviewed phase amends this document.
The ordinary lifecycle is:

```text
RUNTIME_REQUESTED
INPUTS_RESOLVED
PLAN_VALIDATED
DIAGNOSTICS_READY
DIAGNOSTICS_RUNNING
DIAGNOSTICS_COMPLETE
SIGNAL_PROBE_READY
SIGNAL_PROBE_COMPLETE
COST_STRESS_COMPLETE
EVIDENCE_DRAFT_READY
REFERENCE_HANDOFF_READY
```

`DIAGNOSTICS_FAILED` is the named diagnostics failure branch. Failed,
inconclusive, and blocked runs must remain visible through one of these
terminal states:

```text
REJECTED
INCONCLUSIVE
BLOCKED
```

`REFERENCE_HANDOFF_READY` is the most advanced non-terminal successful state in
the MVP. It names a handoff being ready for later review, not Reference
validation.

## Prohibited MVP States

These names are reserved only as explicit must-never-be-reachable concepts in
the MVP. Runtime transition code, records, reports, tools, and docs must not
emit them as reachable states:

```text
ALPHA_VALIDATED
FACTOR_PROMOTED
STRATEGY_READY
PORTFOLIO_READY
LIVE_READY
PAPER_READY
PROFITABLE
TRADABLE
PRODUCTION_READY
```

## Decision And Rejection Names

Decision and rejection names describe why a run stopped or why evidence is
incomplete. They use lowercase snake_case codes, stable fields, and neutral
language. A `RejectionReasonRecord` names a visible condition such as a missing
approved spec, inadmissible DatasetVersion, missing availability timestamp,
variant-budget breach, cost-stress failure, locked-test metadata gap, or
artifact-policy violation.

Decision names must not encode success claims. Prefer `diagnostics_complete`,
`cost_stress_complete`, `evidence_draft_ready`, and `reference_handoff_ready`.
Do not introduce names that imply validation, promotion, profitability,
tradability, strategy status, live scope, paper scope, broker scope, order
routing, account scope, portfolio scope, or production status.

## Report Card Names

Report cards are descriptive summaries. Use `RuntimeReportCard` for a compact
runtime-facing summary and family-specific `*DiagnosticsReport` names for
diagnostic views. Report text must describe checks, inputs, caveats, rejection
reasons, blocked conditions, and artifact references. It must not present a
diagnostic pass, signal probe, bounded-grid result, evidence draft, or handoff
as alpha validation, factor promotion, strategy validation, tradability,
profitability, or production readiness.

## Module Naming Rules

- Keep runtime modules under `alpha_system.runtime`; do not duplicate consumed
  primitives from governance, research, experiments, backtest, data, features,
  or labels.
- Use singular module names for one contract family, such as `probe`, `grid`,
  `audit`, `evidence`, `handoff`, `tool_results`, and `reports`.
- Use package namespaces only where later phases need families of modules:
  `contracts`, `diagnostics`, and `cost`.
- Keep new names additive. If a later phase needs a new runtime object, update
  this document with its exact future module before adding behavior.
