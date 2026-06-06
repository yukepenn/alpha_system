# EvidenceDraft

`alpha_system.runtime.evidence` builds the Research Runtime `EvidenceDraft`: a
descriptive, immutable, hashable evidence-input object for the governance
`EvidenceBundle` surface. It is Tier 3 runtime output for one approved study
run. It is not a candidate, not a finalized governance bundle, not Reference
truth, and not alpha validation.

## Boundary

The draft assembles already-produced runtime outputs by reference and scalar
summary only:

- factor, label, session/regime split, and cross-market diagnostics reports;
- the cost-sensitivity report, including `base` and `double_cost` profiles;
- a signal-probe report when present;
- a bounded-grid run record and `VariantBudget` outcome when present;
- a no-lookahead runtime audit result;
- `StudyRunManifest`, `StudyRunRecord`, version ids, code/config hashes, and
  local-only artifact references;
- `RuntimeDecision` plus visible `RejectionReasonRecord` values for
  `REJECTED`, `INCONCLUSIVE`, and `BLOCKED` outcomes;
- explicit limitations and non-promotional labels.

The builder consumes existing primitives. It imports and validates through
`alpha_system.governance.evidence_bundle.create_evidence_bundle` and accepts
trial ids or `alpha_system.governance.trial_ledger.TrialLedgerRecord` values.
It does not re-implement governance ID, evidence-bundle, or trial-ledger logic.

## Fields

`EvidenceDraft` stores:

- `draft_id`, `draft_hash`, `run_id`, `alpha_spec_id`, `study_spec_id`, and
  `trial_ids`;
- the runtime `decision` and visible terminal rejection reasons;
- ordered `EvidenceSectionSummary` records for diagnostics, cost, probe, grid,
  audit, or terminal-decision visibility;
- declared `limitations`;
- governance-compatible artifact manifest entries;
- `governance_evidence_bundle_id` and a canonical
  `governance_evidence_input_json` payload accepted by the governance
  `EvidenceBundle` primitive.

The object also carries explicit flags:

- `descriptive_only=True`;
- `not_a_candidate=True`;
- `not_reference_truth=True`;
- `not_finalized_evidence_bundle=True`;
- `promotion_basis_allowed=False`.

## Governance Relationship

The draft feeds governance; it does not replace governance. The builder creates
the evidence-input payload by calling the real governance
`create_evidence_bundle` function. `EvidenceDraft.validate_with_governance_evidence_bundle()`
re-validates the stored input with `EvidenceBundle.from_mapping`.

This acceptance check proves the payload is shaped for governance, but the draft
itself remains a runtime evidence input. Yellow-lane review, verdict parsing,
merge gates, and any later Reference handoff are separate Workflow 2 steps.

## Decision Coupling

A clean run that reaches the builder is represented as
`EVIDENCE_DRAFT_READY`. That state is descriptive only. It does not promote a
factor, create a candidate, or validate an alpha.

Terminal outcomes stay terminal:

- `REJECTED` keeps its `RejectionReasonRecord` values visible;
- `INCONCLUSIVE` keeps its `RejectionReasonRecord` values visible;
- `BLOCKED` keeps its `RejectionReasonRecord` values visible.

The draft never hides failed or inconclusive runs behind a forward state.

## Cost Discipline

A forward `EVIDENCE_DRAFT_READY` draft requires a cost-sensitivity summary. A
draft that references a `SignalProbeReport` also requires the matching
`CostSensitivityReport` reference. The cost section requires both `base` and
`double_cost` profiles, carries slippage as a labeled proxy, and records that
cost stress is not a promotion basis. Zero-cost diagnostic metadata cannot be
used as a promotion basis.

## Data And Artifact Policy

The draft is metadata only: version ids, hashes, statuses, scalar summaries,
references, limitations, and rejection reasons. It does not embed runtime
values, feature or label payloads, market observations, provider responses, or
heavy artifacts. Local artifact references remain local-only; `runs/**` files
are not commit-eligible.

No CLI command is added in RT-P16.
