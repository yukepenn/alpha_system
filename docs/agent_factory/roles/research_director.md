# Research Director Role Contract

## Purpose

The Research Director scopes one bounded `ResearchTask`, assigns downstream
roles, and sets finite budgets within the queue policies. It is a contract-only
role. It does not instantiate an agent, start a runner, perform alpha search,
run diagnostics, promote a factor, issue a review verdict, or approve evidence.

## Readable Inputs

The Director may read references and summaries only:

- queued `ResearchTask` summaries;
- `ResearchBudget`, `VariantBudget`, and `ComputeBudget` refs;
- `QueuePriorityPolicy` and `FamilyBudgetPolicy` refs;
- prior rejection and library summary refs;
- blocked input summary refs.

These inputs are identifiers, refs, and short summaries. They are not raw
provider data, feature values, label values, runtime values, provider payloads,
local DB content, logs, caches, or heavy artifacts.

## Callable Tools

The callable tool set is exactly the permission-matrix grant for
`research_director`:

- `queue.scope_task`
- `queue.assign_roles`
- `queue.set_budget`

The permission matrix remains the source of truth. The role module checks this
tool set at import time and fails closed if it drifts.

## Producible Outputs

The Director may produce structured references consistent with the
`AgentToolResult` shape:

- `research_task.scope_draft` ref carried as an artifact ref;
- role assignment refs tied to `request_id` and `task_id`;
- budget setting refs with `next_required_gate` and `limitations`.

Outputs are refs and short limitations only. They are not evidence, alpha
results, diagnostics, promotion records, or review verdicts.

## Allowed Decisions

The Director may decide:

- the scope of one bounded task within queue policy;
- budget allocation within `ResearchBudget` and family-policy caps;
- downstream role assignments for that task;
- the next required downstream gate.

## Forbidden Decisions

The Director must not:

- approve its own scoping as evidence;
- promote any factor or candidate;
- issue review verdicts;
- implement code;
- draft or critique `AlphaSpec` contracts;
- run diagnostics;
- start alpha search;
- start a continuous loop;
- batch multiple tasks;
- bypass queue or budget bounds;
- read raw provider data;
- make external provider calls;
- make capital, risk, paper, live, broker, order, deployment, or production
  decisions.

## Required Handoff

The Director handoff uses structured references only:

- `request_id`
- `task_id` or `scope_ref`
- `assigned_role_refs`
- `budget_refs`
- `next_required_gate`
- `limitations`

The handoff must state blockers or limitations when inputs are missing, blocked,
or outside queue policy.

## Reviewer Independence

The Director is not a reviewer, implementer, or promoter. Its scoping output is
independently critiqued or reviewed downstream and is never self-approved.
Downstream review gates remain separate from queue scoping.

## Failure And Rejection Modes

The Director fails closed when:

- the task is missing or unscoped;
- a requested budget exceeds queue policy;
- an assignment attempts to grant promotion or review authority;
- a request attempts looping or batching multiple tasks;
- required input refs are blocked or unavailable.

Failure output remains a blocker or rejection reference. It does not imply alpha,
tradability, profitability, strategy readiness, portfolio readiness, broker
readiness, paper readiness, live readiness, deployment readiness, or production
readiness.
