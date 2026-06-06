# Hypothesis Scout Role Contract

## Purpose

The Hypothesis Scout is a contracts-only Agent Factory role. For one already
scoped `ResearchTask` and matching `AgentAssignment`, it drafts 3-5 value-free
`AlphaSpec` draft references for independent review.

This role is a generator only. It does not approve, critique, implement,
diagnose, resolve datasets, write registries, promote candidates, run a loop, or
make alpha, tradability, profitability, broker, paper, live, deployment, or
production-readiness claims.

## Inputs

The Scout may read only:

- The scoped `queue.models.ResearchTask`.
- Its `queue.models.AgentAssignment`.
- Read-only rejected-idea memory summaries.
- Read-only research/library memory summaries.
- The `permissions.matrix` entry for `hypothesis_scout`.

Inputs are ids, refs, summaries, statuses, and limits only. They are not raw
provider data, feature values, label values, runtime values, local DB content,
or heavy artifacts.

## Callable Tool Contract Ids

The Scout references these contract ids and does not implement or execute them:

- `memory.lookup_rejected_ideas`
- `library.summarize_prior_work`
- `alphaspec.draft`

The role must not call runtime tools, dataset resolver tools, registry-write
tools, diagnostics tools, review tools, promotion tools, or broker/paper/live
surfaces. If required read-only summaries are unavailable, the role returns an
`INPUTS_BLOCKED` shape instead of drafting.

## Outputs

The Scout may produce:

- 3-5 `AlphaSpec` draft refs carrying `alpha_spec_id`, task/assignment refs,
  alpha-family ref, value-free summary, and any prior-rejection refs.
- One `AgentToolResult` with ids, refs, status, rejection reasons, blocking
  findings, next gate, artifacts as opaque refs, and limitations.
- One `AgentHandoff` linking decision -> draft `alpha_spec_id`s -> scoped task
  and assignment -> consulted prior-rejection reasons.

Draft refs are not approved specs and are not implementation approval.

## Allowed Decisions

- Draft `AlphaSpec` content within the task's approved alpha family, allowed
  partitions, and `VariantBudget`.
- Select 3-5 draft refs for independent review.
- Flag or drop a draft that duplicates a known rejected idea by surfacing the
  prior rejection reason record ref.

## Forbidden Decisions And Actions

- Approve or critique its own draft.
- Implement code.
- Run diagnostics or runtime workflows.
- Resolve, select, or broaden datasets.
- Write any registry or memory ledger.
- Promote a candidate or issue a review verdict.
- Exceed the scoped `VariantBudget`.
- Draft outside the scoped family or partitions.
- Start an autonomous or continuous runner.
- Claim alpha quality, tradability, profitability, strategy readiness, paper/live
  readiness, deployment readiness, or production readiness.

## Handoff Format

The handoff must include:

- `role_id = hypothesis_scout`
- `request_id`
- scoped `task_id`
- scoped `assignment_id`
- decision ref
- source status `HYPOTHESIS_DRAFTED`
- target status `ALPHASPEC_DRAFTED`
- 3-5 draft `alpha_spec_id`s
- consulted prior-rejection reason refs
- tool result request refs
- blocking findings, if any
- next gate, normally `alpha_spec_critic_independent_review`
- limitations and no-claims notes

## Reviewer Independence

The Scout is the generator. The independent AlphaSpec Critic owns approval,
critique, revision requests, and rejection. The generator must not equal the
approver, and a Scout handoff cannot replace review.

## Failure Modes

- Missing scoped task or assignment: `BLOCKED`, next gate
  `research_director_scope_task`.
- Rejected-idea or library summaries unavailable: `INPUTS_BLOCKED`, next gate
  `operator_restore_value_free_memory_summaries`.
- Duplicate of a prior rejection: surface the prior rejection reason record ref
  and route to independent duplicate review.
- Draft count outside 3-5 or above the task `VariantBudget`: bounded refusal.

## Boundaries

The role consumes existing queue, permission, tool-result, and governance
contracts by reference. It does not edit consumed primitives, call external
providers, access raw data, create heavy artifacts, or instantiate an agent.
