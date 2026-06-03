# Promotion Gate

`PromotionDecision` is the governance record for a controlled lifecycle transition
after review. It is metadata and protocol machinery only. It does not run studies,
compute factors or labels, ingest data, route orders, allocate capital, approve live
use, or mark production readiness.

## PromotionDecision

The required fields are:

- `promotion_id`
- `alpha_spec_id`
- `evidence_bundle_id`
- `trial_ledger_refs`
- `previous_state`
- `next_state`
- `decision`
- `rationale`
- `reviewer_verdict_id`
- `warnings`
- `timestamp`

`promotion_id` is a deterministic `prom_...` governance ID recomputed from all
non-ID content during validation. Unknown fields, missing fields, null fields,
wrong ID prefixes, invalid lifecycle states, prohibited MVP states, empty trial
references, duplicate trial references, vague rationale text, malformed timestamps,
and mismatched content IDs fail closed with `GovernanceValidationError`.

`previous_state` must be `REVIEWED`. `next_state` and `decision` must match one of
`REJECTED`, `WATCH`, `CANDIDATE`, or `VALIDATED`.

## Candidate And Validated Gate

`REVIEWED -> CANDIDATE` and `REVIEWED -> VALIDATED` require:

- a valid `PromotionDecision`;
- a valid `EvidenceBundle`;
- complete validated `TrialLedgerRecord` metadata;
- matching `alpha_spec_id` and `evidence_bundle_id` between the decision and bundle;
- matching `reviewer_verdict_id` / `reviewer_verdict_reference` links to an
  independent `ReviewerVerdict`;
- a `PASS` or `PASS_WITH_WARNINGS` verdict;
- matching trial reference sets across the decision, evidence bundle, and ledger;
- no omitted failed or abandoned trial records;
- explicit locked-test contamination metadata when any trial records contamination.

Missing trial refs, missing evidence, failed-run omission, and unrecorded locked-test
contamination block promotion. The gate validates metadata only; it does not inspect
or materialize evidence artifacts.

## Rejection Gate

`any -> REJECTED` requires a valid `RejectedIdeaRecord` and an explicit rejection
reason. `REVIEWED -> REJECTED` also requires a matching `PromotionDecision`, because
the reviewed boundary is governed by the promotion-decision protocol.

## Reviewer Verdict

`EVIDENCE_READY -> REVIEWED` requires a full `ReviewerVerdict`, not an ID-only
placeholder. The verdict must validate fail closed, include a non-empty
`independence_statement`, and pass the independence rule: `reviewer_id` must differ
from `implementer_id`, and `role` must differ from `implementer_role`.

`REVIEWED -> REJECTED | WATCH | CANDIDATE | VALIDATED` requires the independent
verdict referenced by the `PromotionDecision`. Candidate and validated promotion
also require the verdict to be merge eligible. A self-review, missing verdict,
missing implementer identity, role match, ID mismatch, or non-merge-eligible
verdict blocks the transition.

## Safety Boundary

The prohibited MVP state names `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and
`PRODUCTION_READY` are unreachable. A valid `PromotionDecision`, `CANDIDATE`, or
`VALIDATED` status does not imply live approval, capital allocation, production
readiness, profitability, tradability, or market truth.
