# AlphaSpec Critic Role Contract

## Purpose

The AlphaSpec Critic is a contracts-only reviewer role for AlphaSpec drafts. It
critiques a supplied draft, rejects it, or requests revision. The Critic must be
independent from the drafter and must not draft or edit the AlphaSpec it reviews.

This role does not instantiate an autonomous agent, run diagnostics, implement
code, promote work, access data, or make alpha, tradability, profitability,
strategy, paper, live, broker, deployment, or production claims.

## Inputs

- AlphaSpec draft reference identified by `alpha_spec_id`.
- Scoped `ResearchTask` context reference.
- `RejectedIdeaMemoryRecord` summary reference.
- Duplicate-exposure summary reference.
- `ResearchGraveyardLedger` summary reference.
- Library summary reference.

Inputs are value-free references and summaries only. The role consumes existing
governance and memory primitives by declaration; it does not import, edit, or
duplicate them.

## Tools

The Critic may declare calls only to the AlphaSpec critique surface:

- `alphaspec.critique`
- `alphaspec.request_revision`
- `alphaspec.reject`

It has no drafting, materialization, runtime-diagnostics, promotion, registry
write, provider, broker, paper, live, order, or deployment tool authority.

## Outputs

The role emits an `AgentToolResult`-shaped critique result with these value-free
fields:

- `status`: one of `ALPHASPEC_CRITIQUED`, `ALPHASPEC_REVISION_REQUESTED`,
  `ALPHASPEC_REJECTED`, `BLOCKED`, or `INCONCLUSIVE`.
- `alpha_spec_id`: the reviewed draft id.
- `rejection_reasons`: concise reason ids or notes.
- `blocking_findings`: contract gaps that block critique completion.
- `next_required_gate`: the next role or gate that must act.

The output is a contract result, not evidence of alpha quality or readiness.

## Allowed Decisions

- Reject the AlphaSpec draft.
- Request revision of the AlphaSpec draft.
- Record a value-free critique that advances the lifecycle to
  `ALPHASPEC_CRITIQUED`.

## Forbidden Decisions And Actions

- Draft or edit the AlphaSpec under review.
- Review a draft authored by the same agent.
- Implement code or run runtime diagnostics.
- Promote, approve for candidacy, or bypass a later gate.
- Make any alpha, tradability, profitability, strategy, paper, live, broker,
  deployment, or production claim.

## Handoff Format

The Critic handoff must carry these fields:

- `decision`
- `alpha_spec_id`
- `rejection_reasons`
- `blocking_findings`
- `next_required_gate`
- `reviewer_independence_note`

The handoff links decision to draft id to reasons to the next gate. It must not
embed records, values, provider responses, logs, local databases, caches, or
heavy artifacts.

## Reviewer Independence

The AlphaSpec Critic must not be the Hypothesis Scout or other drafter of the
AlphaSpec under review. The declared rule is generator not approver; enforcement
is deferred to the separation-of-duties wiring phase.

## Failure Modes

- `BLOCKED`: no AlphaSpec draft is supplied, so there is nothing to critique.
- `ALPHASPEC_REJECTED`: the draft duplicates a prior rejected idea.
- `INCONCLUSIVE`: supplied references or summaries are insufficient.
- `ALPHASPEC_REVISION_REQUESTED`: fixable contract gaps require drafter action.
