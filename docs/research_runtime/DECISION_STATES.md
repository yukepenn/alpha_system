# Runtime Decision States

RT-P15 adds `alpha_system.runtime.decisions`, the canonical visibility layer for
failed, inconclusive, and blocked research-runtime outcomes.

The package does not run diagnostics, cost stress, bounded grids, audits, data
resolution, provider access, or broker operations. It consumes existing upstream
reason objects and records a value-free decision surface.

## Terminal Decisions

The terminal non-success decision states are:

- `REJECTED`
- `INCONCLUSIVE`
- `BLOCKED`

Any terminal decision must carry at least one `RejectionReasonRecord`. A
terminal decision with zero reasons raises a contract error. Forward lifecycle
states such as `RUNTIME_REQUESTED`, `INPUTS_RESOLVED`, `PLAN_VALIDATED`,
`DIAGNOSTICS_COMPLETE`, `SIGNAL_PROBE_COMPLETE`, `COST_STRESS_COMPLETE`,
`EVIDENCE_DRAFT_READY`, and `REFERENCE_HANDOFF_READY` must not carry rejection
reasons.

The runtime decision surface consumes existing `RuntimeLifecycleState`,
`StudyRunResultState`, and `RuntimeEntryStatus` values. Existing lifecycle states
remain forward states. Existing `StudyRunResultState.DIAGNOSTICS_FAILED` maps to
the terminal decision `REJECTED` so failures are not represented as a separate
hidden end state.

## Reason Records

`RejectionReasonRecord` is immutable and hashable. Its stable payload contains
only:

- canonical reason code;
- human-readable non-promotional message;
- terminal decision state;
- originating stage;
- upstream source code and optional source id.

It does not copy expected/actual values, rows, feature values, label values,
provider payloads, artifacts, or raw/heavy data references.

The closed canonical reason codes are:

- `data_unavailable`
- `leakage_risk`
- `weak_diagnostics`
- `cost_fragile`
- `low_sample`
- `variant_budget_exceeded`
- `duplicate_exposure`
- `blocked_by_policy`
- `inconclusive`

Adapters preserve the upstream reason code as `source_code` while mapping the
canonical `code` to the closed category set.

## Consumed Upstream Shapes

The decisions package consumes and normalizes:

- `RunRejectionReason` from `alpha_system.runtime.contracts.run_record`;
- `RuntimeEntryReason` from `alpha_system.runtime.entry_contract`;
- `NoLookaheadAuditReason` from `alpha_system.runtime.audit.no_lookahead`;
- bounded-grid rejection reasons from `alpha_system.runtime.grid.contracts`.

The producer modules remain the owners of their stage-specific validation logic.
The decisions package does not duplicate IC, cost, grid, audit, governance,
backtest, feature, label, or data primitives.

## Runtime Stop Condition

`RuntimeStopCondition` is a runtime decision object for "this run cannot
proceed." It maps to `BLOCKED` and carries a visible `RejectionReasonRecord`.

It is not the Workflow 2 operator file `runs/<run_id>/STOP`, does not create that
file, and does not control Ralph's STOP/resume mechanism.

## Safety Boundaries

The decision-state surface defines no alpha validation, factor promotion,
strategy, portfolio, live, paper, profitable, tradable, or production-ready
state. It introduces no broker, live, paper, order, account, provider-call,
deployment, PR, merge, or CLI behavior.
