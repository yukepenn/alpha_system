# Governance Overview

`ALPHA_RESEARCH_GOVERNANCE_MVP` installs the admissibility protocol for future AI alpha research in `alpha_system`. The protocol is a governance and evidence layer, not an alpha search layer. It defines the metadata objects, lifecycle states, review records, and artifact discipline that future research must satisfy before a result can be treated as admissible evidence.

This phase establishes the overview only. It does not add source code, tests, configs, templates, command-line tools, broker integrations, real-data ingestion, paper trading, live trading, order routing, optimization, or portfolio allocation.

## Protocol Purpose

The admissibility protocol exists to keep future research from becoming a post-hoc search for appealing results. Every research idea must have a visible path from hypothesis and pre-registration through study control, trial accounting, evidence packaging, independent review, and promotion decision.

The governance layer owns evidence and process. It does not certify alpha validity, market value, tradability, profitability, live readiness, or production readiness.

## Governance Objects

The governance objects are the durable records used by the protocol:

- `HypothesisCard` captures the research rationale and falsification anchor.
- `AlphaSpec` records the pre-registered alpha research specification.
- `FeatureRequest` records requested inputs and duplicate-exposure checks.
- `LabelSpec` records label definitions and leakage checks.
- `StudySpec` records the diagnostics plan, budget, and locked-test policy.
- `TrialLedgerRecord` records each attempt, including failed or abandoned attempts.
- `EvidenceBundle` records a manifest-backed evidence package.
- `RejectedIdeaRecord` keeps rejected ideas visible as first-class records.
- `PromotionDecision` records controlled lifecycle transitions.
- `ReviewerVerdict` records independent semantic review.
- `NegativeControlResult` records whether known-bad controls fail closed.
- `AlphaBookRecord` is a future-compatibility pointer stub only.

The exact object fields and acceptance criteria live in the campaign contract bundle.

## Lifecycle State Model

The MVP lifecycle state model is:

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

The intended transition summary is:

```text
DRAFT -> REGISTERED
REGISTERED -> IMPLEMENTATION_ALLOWED
IMPLEMENTATION_ALLOWED -> IMPLEMENTED
IMPLEMENTED -> DIAGNOSTICS_ALLOWED
DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN
DIAGNOSTICS_RUN -> EVIDENCE_READY
EVIDENCE_READY -> REVIEWED
REVIEWED -> REJECTED | WATCH | CANDIDATE | VALIDATED
any state -> REJECTED
```

The state model is intentionally conservative. Missing prerequisites block transitions:

- missing `AlphaSpec` blocks code;
- missing `StudySpec` blocks diagnostics;
- missing `TrialLedger` blocks promotion;
- missing `EvidenceBundle` blocks candidate status;
- missing `ReviewerVerdict` blocks factor library entry;
- self-review blocks promotion;
- locked-test contamination without metadata blocks promotion;
- failed-run omission blocks promotion;
- unsupported claims block merge.

## Prohibited MVP States

The names `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and `PRODUCTION_READY` are listed by the campaign only as future, non-MVP concepts. They are not valid reachable states in this governance MVP.

`VALIDATED` is not production approval. `CANDIDATE` is not capital allocation. A `PromotionDecision` is a governance record, not live-trading authorization.

## Evidence Governance Posture

The campaign posture is:

```text
Be aggressive about evidence governance.
Be conservative about market claims and trading scope.
```

Aggressive evidence governance means the protocol should make missing prerequisites, weak evidence, self-approval, unrecorded failed attempts, uncontrolled variants, duplicate exposures, leakage, locked-test contamination, and unsupported claims visible and blockable.

Conservative market scope means this campaign must not introduce real data, alpha search, broker connectivity, paper or live trading, order routing, capital allocation, production deployment behavior, or claims about alpha, profitability, tradability, or production readiness.

## Contract References

The durable campaign contract bundle is:

- `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/GOAL.md`
- `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/PHASE_PLAN.md`
- `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/campaign.yaml`
- `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/ACCEPTANCE.md`
- `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RISK_REGISTER.md`
- `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/RUNBOOK.md`

These files remain the source of truth for phase scope, acceptance gates, risk controls, and operating procedure.
