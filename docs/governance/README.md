# Governance Docs

This directory is the durable documentation root for the `ALPHA_RESEARCH_GOVERNANCE_MVP` campaign. It describes the admissibility and evidence-governance layer for future AI alpha research at a high level.

The governance layer decides what future research results are allowed to be treated as admissible evidence. It does not search for alpha, ingest real data, connect to brokers, route orders, run live or paper trading, allocate capital, or make alpha/profitability/tradability/production-readiness claims.

## Campaign Contract Bundle

The campaign source of truth lives in `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

Use the repository-level `ACTIVE_CAMPAIGN.md` as the active-campaign pointer. Do not create `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACTIVE_CAMPAIGN.md`.

## Hard Governance Rules

- No `AlphaSpec` means no code.
- No `StudySpec` means no diagnostics.
- No `EvidenceBundle` means no candidate.
- No `TrialLedger` means no promotion.
- No `ReviewerVerdict` means no factor library entry.
- Failed ideas remain visible.
- Rejected ideas are first-class records.
- Variant mining is visible.
- Locked-test reuse is recorded as contamination metadata.
- The implementation agent cannot approve itself.
- Promotion is not live approval.
- `VALIDATED` is not production.
- `CANDIDATE` is not capital allocation.

## Governance Objects

The MVP governance object list is:

- `HypothesisCard` — hypothesis rationale and falsification anchor.
- `AlphaSpec` — pre-registered alpha research specification.
- `FeatureRequest` — feature or factor input request with duplicate-exposure checks.
- `LabelSpec` — explicit label definition and leakage guard.
- `StudySpec` — diagnostics plan, research budget, and locked-test policy.
- `TrialLedgerRecord` — record of each attempt, including failures.
- `EvidenceBundle` — manifest-backed evidence package.
- `RejectedIdeaRecord` — first-class research graveyard record.
- `PromotionDecision` — controlled lifecycle state-transition decision.
- `ReviewerVerdict` — independent semantic review record.
- `NegativeControlResult` — record that known-bad controls fail closed.
- `AlphaBookRecord` — future-compatibility pointer stub only.

Each object must stay within its stated purpose. None of these objects implies market truth, live approval, capital allocation, or production readiness.

## Lifecycle Summary

Future governance objects move research ideas through a controlled lifecycle:

```text
DRAFT
  -> REGISTERED
  -> IMPLEMENTATION_ALLOWED
  -> IMPLEMENTED
  -> DIAGNOSTICS_ALLOWED
  -> DIAGNOSTICS_RUN
  -> EVIDENCE_READY
  -> REVIEWED
  -> REJECTED | WATCH | CANDIDATE | VALIDATED
```

Any lifecycle state may move to `REJECTED` when a `RejectedIdeaRecord` and reason exist.

The prohibited MVP state names `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and `PRODUCTION_READY` are future-only concepts for this campaign. They must remain unreachable in the MVP governance protocol.

## Posture

The campaign posture is aggressive about evidence governance and conservative about market claims and trading scope. The layer is meant to make weak evidence, missing prerequisites, self-approval, hidden failures, uncontrolled variants, duplicate exposures, leakage, and unsupported claims detectable and blockable before future research campaigns expand scope.
