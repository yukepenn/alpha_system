# Reviewer Independence

`ReviewerVerdict` records an independent semantic review of governance artifacts.
It is metadata only. It does not compute factor values, run diagnostics, validate
market truth, assert profitability, approve tradability, or mark production
readiness.

## ReviewerVerdict

The serialized required fields are:

- `reviewer_id`
- `role`
- `independence_statement`
- `verdict`
- `blocking_issues`
- `warnings`
- `checked_artifacts`
- `checked_commands`
- `timestamp`

Validation is fail closed. Missing fields, null fields, unknown fields, invalid
types, empty reviewer identity, empty role, empty independence statement, invalid
timestamp, empty checked artifact lists, empty checked command lists, non-string
list items, and duplicate list items raise `GovernanceValidationError`.

The closed verdict vocabulary is:

- `PASS`
- `PASS_WITH_WARNINGS`
- `REWORK`
- `BLOCKED`

Only `PASS` and `PASS_WITH_WARNINGS` are merge-eligible verdicts. The deterministic
`rver_...` ID is generated from the serialized verdict content using the shared
governance ID and canonical serialization primitives.

## Independence Rule

The promotion gate requires implementer identity metadata before accepting a
review:

- `implementer_id`
- `implementer_role`

The reviewer must be independent by both identity and role. A verdict fails closed
when `reviewer_id` equals `implementer_id`, or when `role` equals
`implementer_role`. Missing implementer identity or role also fails closed because
independence cannot be established.

## Gate Wiring

`EVIDENCE_READY -> REVIEWED` requires a present, validated, independent
`ReviewerVerdict`. The transition records the verdict's computed `rver_...` ID.

`REVIEWED -> REJECTED | WATCH | CANDIDATE | VALIDATED` requires a valid
`PromotionDecision` and the same independent `ReviewerVerdict` referenced by the
decision. `CANDIDATE` and `VALIDATED` additionally require a merge-eligible verdict,
a matching `EvidenceBundle.reviewer_verdict_reference`, complete TrialLedger
metadata, complete evidence metadata, failed-run visibility, and recorded
locked-test contamination metadata when applicable.

These checks preserve the existing promotion-gate blocks: missing TrialLedger
records, missing EvidenceBundle, failed-run omission, unrecorded locked-test
contamination, prohibited MVP states, and unsupported promotion targets remain
blocked.

## No-Claims Posture

A `ReviewerVerdict`, including `PASS` or `PASS_WITH_WARNINGS`, means only that an
independent semantic review accepted the governance metadata under this protocol.
It does not imply market truth, alpha validity, profitability, tradability, live
approval, capital allocation, production readiness, broker behavior, paper trading,
order routing, real-data ingestion, or deployment readiness.
