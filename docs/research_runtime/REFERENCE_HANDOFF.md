# Reference Candidate Handoff

`alpha_system.runtime.handoff` builds a `ReferenceCandidateHandoff`: a
reference-only package for a future, separately authorized Reference validation
step. It is not Reference validation, not promotion, not a candidate creation
step, and not alpha, profitability, tradability, strategy, backtest, portfolio,
paper, live, broker, order, account, or production evidence.

The most advanced state the builder can emit is `REFERENCE_HANDOFF_READY`.

## Contract

The handoff consumes already-produced runtime contracts and bundles them by
reference:

- upstream `EvidenceDraft` id and hash;
- diagnostics, cost, signal-probe, grid, and audit report or record refs;
- `StudyRunManifest` id/hash and reference-only dataset, feature-pack,
  label-pack, code, config, and cost lineage;
- `RuntimeArtifactManifest` id/hash;
- `CostModelVersion` id/hash plus scalar refs for the required `base` and
  `double_cost` cost profiles;
- explicit limitations;
- `ReferenceRequirement` with `next_required_gate =
  REFERENCE_VALIDATION_REQUIRED`.

The payload is metadata only: IDs, hashes, states, refs, scalar cost-profile
metadata, limitations, and visible rejection reasons. It does not embed raw
provider data, market values, feature values, label values, runtime value
tables, local DBs, or heavy artifacts.

## Preconditions

For `REFERENCE_HANDOFF_READY`, the builder fails closed unless:

- the upstream `EvidenceDraft` decision is `EVIDENCE_DRAFT_READY`;
- a `CostSensitivityReport` is present;
- the cost report carries a `CostModelVersion`;
- both `base` and `double_cost` cost profiles are present;
- slippage remains labeled as a proxy;
- a `NoLookaheadRuntimeAudit` result is present and passed with
  `POINT_IN_TIME_SAFE`.

Missing cost stress or a missing/passing audit does not create a forward
handoff. It yields a terminal `BLOCKED` handoff with a visible
`RejectionReasonRecord`.

## Decision States

Clean survivor:

- `REFERENCE_HANDOFF_READY`

Terminal outcomes:

- `REJECTED`
- `INCONCLUSIVE`
- `BLOCKED`

Terminal outcomes always carry `RejectionReasonRecord` values. An upstream
terminal `EvidenceDraft` stays terminal in the handoff and does not get recast
as ready.

## Reference Requirements

Every handoff carries:

- `strategy_not_validated = True`
- `reference_validation_performed = False`
- `future_authorization_required = True`
- `next_required_gate = REFERENCE_VALIDATION_REQUIRED`
- `handoff_only = True`

These fields are deliberately conservative. They make the next required gate
visible without running Reference validation or implying that a strategy exists.

## Safety Boundary

The handoff package is an orchestration and packaging layer. It consumes
existing runtime, governance, cost, audit, diagnostics, probe, grid, manifest,
and artifact contracts. It does not re-implement research, experiments,
governance, backtest, feature, label, or data primitives. It does not add CLI
wiring in RT-P17.
