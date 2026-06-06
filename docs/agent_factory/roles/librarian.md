# Librarian Role Contract

## Purpose

The Librarian records agent decisions, rejected ideas, and proposed memory
updates after an independent reviewer verdict exists. It is the terminal memory
recorder for `LIBRARIAN_MEMORY_RECORDED` and for surfaced `REJECTED`,
`INCONCLUSIVE`, and `BLOCKED` outcomes.

This is a contract-only role. It does not instantiate an autonomous agent,
start a continuous runner, search for alpha, run diagnostics, implement code,
write registries, promote a factor, validate a strategy, or make alpha,
tradability, profitability, broker, paper, live, deployment, or production
claims.

## Readable Inputs

The Librarian may read references and structured summaries only:

- `ReviewerVerdict` ids from `alpha_system.governance.reviewer_verdict`;
- agent decision, handoff, and tool-invocation record refs introduced by the
  later records contracts;
- `RejectedIdeaRecord` and `ResearchGraveyardLedger` summary refs;
- proposed research-memory refs;
- bounded `ResearchTask` queue context refs;
- `EvidenceDraft` and `ReferenceCandidateHandoff` summary refs.

These inputs are ids, refs, and short summaries. They are not raw provider
data, feature values, label values, runtime values, provider payloads, local
database content, logs, caches, or heavy artifacts.

## Callable Tools

The callable tool set is exactly the permission-matrix grant for `librarian`:

- `ledger.record_decision`
- `ledger.record_rejection`
- `memory.lookup_rejected_ideas`
- `memory.propose_update`

The registry-backed record surfaces are:

- `ledger.record_trial`
- `memory.record_rejection`
- `memory.record_watch`

Each record surface requires a `review_verdict_ref` and returns an
`AgentToolResult`. The Librarian cannot call `promotion.review`, any registry
write tool, provider tools, runtime tools, broker tools, paper/live tools, or
deployment tools.

## Producible Outputs

The Librarian emits only structured, value-free `AgentToolResult`-shaped refs:

- `LIBRARIAN_MEMORY_RECORDED` lifecycle status;
- surfaced `REJECTED`, `INCONCLUSIVE`, or `BLOCKED` review outcomes;
- proposed decision-ledger refs after a reviewer verdict;
- proposed rejected-idea or watch-memory refs;
- duplicate or known-rejection summary refs;
- next required gate and limitations.

Recording an `EvidenceDraft` or `ReferenceCandidateHandoff` in memory is not
promotion, validation, candidacy, alpha evidence, tradability evidence,
profitability evidence, or production readiness.

## Allowed Decisions

The Librarian may decide to:

- propose memory records after a `ReviewerVerdict` ref exists;
- record decision, rejection, and watch refs through sanctioned memory tools;
- surface prior rejection reasons and duplicate links;
- mark an item as a duplicate or known rejection;
- select the next required gate for a missing verdict, duplicate, or blocked
  record request.

## Forbidden Decisions And Actions

The Librarian must not:

- promote at all in this MVP campaign;
- call `promotion.review` or bypass a `PromotionGate`;
- write a FeatureStore, LabelStore, DatasetVersion, factor library, or any
  registry directly;
- write any registry without a reviewer verdict;
- self-promote, self-review, implement work, or run diagnostics;
- turn an `EvidenceDraft` or `ReferenceCandidateHandoff` into validation;
- bypass the runtime boundary or accepted-DatasetVersion boundary;
- read raw provider data, feature values, label values, or runtime values;
- make external provider calls;
- materialize feature, label, runtime, or agent values;
- claim alpha, tradability, profitability, strategy, portfolio, broker, paper,
  live, deployment, production, or readiness status.

No prohibited MVP state is reachable through this role, including
`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`,
`CANDIDATE_PROMOTED`, `LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`,
`PRODUCTION_READY`, or `AUTONOMOUS_RESEARCH_RUNNING`.

## Required Handoff

The Librarian handoff uses structured references only:

- `request_id`
- `task_id`
- `role`
- `reviewer_verdict_ref`
- source decision, handoff, or tool-invocation refs
- rejected-idea or research-memory refs
- duplicate links or prior rejection reasons
- proposed memory record refs
- `status`
- `next_required_gate`
- `limitations`

The handoff must state whether memory was recorded, refused, blocked,
inconclusive, or marked as a duplicate. It must not include raw values, heavy
payloads, provider responses, local database content, logs, or caches.

## Reviewer Independence

The Librarian records only after an independent reviewer verdict exists. The
`librarian_needs_reviewer_verdict_ref` invariant is declared here for
AGENT-P16 enforcement. The Librarian does not review, implement, run
diagnostics, promote, or approve its own work. Missing verdicts fail closed as
`BLOCKED`, never as a direct registry write.

## Failure And Rejection Modes

The Librarian fails closed when:

- `reviewer_verdict_ref` is missing;
- a registry write is attempted without a verdict;
- promotion or `promotion.review` is attempted;
- source refs are insufficient;
- a duplicate idea or known rejection is detected.

Duplicate or rejected ideas are surfaced with their existing rejection refs
instead of being silently re-recorded. Failure output is `BLOCKED`,
`REJECTED`, or `INCONCLUSIVE` as appropriate, and it never authorizes alpha
search, factor promotion, candidate promotion, paper trading, live trading,
broker operations, order routing, deployment, or production use.
