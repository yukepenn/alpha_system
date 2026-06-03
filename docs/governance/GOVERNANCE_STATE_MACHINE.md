# Governance State Machine

The governance lifecycle implemented for this MVP is:

```text
DRAFT
REGISTERED
IMPLEMENTATION_ALLOWED
IMPLEMENTED
DIAGNOSTICS_ALLOWED
DIAGNOSTICS_RUN
EVIDENCE_READY
REVIEWED
REJECTED
WATCH
CANDIDATE
VALIDATED
```

These are the only reachable states. `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and
`PRODUCTION_READY` are future-only names in the campaign contract and are not
reachable by any implemented transition.

## Transitions

```text
DRAFT -> REGISTERED
REGISTERED -> IMPLEMENTATION_ALLOWED
IMPLEMENTATION_ALLOWED -> IMPLEMENTED
IMPLEMENTED -> DIAGNOSTICS_ALLOWED
DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN
DIAGNOSTICS_RUN -> EVIDENCE_READY
EVIDENCE_READY -> REVIEWED
REVIEWED -> REJECTED | WATCH | CANDIDATE | VALIDATED
any -> REJECTED
```

`validate_governance_transition(...)` in
`alpha_system.governance.promotion_gate` validates these transitions using
`PromotionGateContext`.

## Gate Preconditions

`DRAFT -> REGISTERED` requires a valid linked `HypothesisCard` and `AlphaSpec`.

`REGISTERED -> IMPLEMENTATION_ALLOWED` requires a valid `AlphaSpec` and explicit
duplicate/leakage clearance metadata.

`IMPLEMENTATION_ALLOWED -> IMPLEMENTED` requires an explicit scoped implementation
handoff reference.

`IMPLEMENTED -> DIAGNOSTICS_ALLOWED` requires a valid `StudySpec`.

`DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN` requires at least one valid
`TrialLedgerRecord`.

`DIAGNOSTICS_RUN -> EVIDENCE_READY` requires a valid `EvidenceBundle` with a
manifest and trial references.

`EVIDENCE_READY -> REVIEWED` requires a `reviewer_verdict_id` seam. P11 validates
the opaque `rver_...` ID; P12 implements the independent `ReviewerVerdict` object
and self-approval block.

`REVIEWED -> REJECTED/WATCH/CANDIDATE/VALIDATED` requires a valid
`PromotionDecision`. Candidate and validated transitions additionally require the
complete evidence and trial-ledger gate described in `PROMOTION_GATE.md`.

`any -> REJECTED` requires a valid `RejectedIdeaRecord` and explicit reason.

## Blocks

The state machine fails closed for undeclared transitions, unknown states,
prohibited MVP states, missing `AlphaSpec`, missing `StudySpec`, missing
`TrialLedger` records, missing `EvidenceBundle`, missing `PromotionDecision`,
missing `RejectedIdeaRecord`, failed-run omission, and locked-test contamination
without explicit metadata.

Promotion is governance status only. `VALIDATED` is not production approval,
`CANDIDATE` is not capital allocation, and no transition in this MVP creates live,
paper, broker, order-routing, alpha-search, profitability, tradability, or
production-deployment behavior.
