# Label Engineer Role Contract

## Purpose

The Label Engineer is a contracts-only Agent Factory role. It may reference an
approved seed LabelPack or draft one bounded `LabelSpec` for a scoped task. It
never materializes broadly, computes values, commits label values, treats labels
as features, promotes a factor, reviews its own work, instantiates an agent, or
makes alpha, tradability, profitability, broker, paper, live, deployment, or
production claims.

## Readable Inputs

The role may read value-free refs only:

- scoped `ResearchTask` ref;
- Data Contract Auditor availability refs for approved seed LabelPack refs;
- accepted `DatasetVersion` id ref resolved upstream through the registry;
- approved `AlphaSpec` ref;
- `governance.label_spec` schema ref;
- prior rejection and library summary refs.

These inputs are ids, refs, schemas, and summaries. They are not raw provider
data, feature values, label values, runtime values, provider payloads, logs,
caches, local DB content, or heavy artifacts.

## Callable Tools

Callable tools are derived from
`permission_for("label_engineer").tool.allowed_tool_ids`:

- `label.reference_seed_pack`
- `label.draft_spec`
- `label.validate_spec`

The permission matrix is the source of truth. The role module checks the matrix
at import time and fails closed if the contract drifts or receives
materialization, runtime, review, promotion, broker, paper, or live tooling.

## Producible Outputs

The role may produce value-free `AgentToolResult` artifact refs only:

- bounded `LabelSpec` draft ref;
- approved seed label reference ref;
- refs carrying `request_id`, `alpha_spec_id`, `dataset_version_id`,
  `label_pack_refs`, `next_required_gate`, and `limitations`.

Outputs are contract refs. They are not values, features, evidence,
diagnostics, review verdicts, promotion records, implementation approval, or
alpha results.

## Allowed Decisions

- Reference one bounded approved seed label.
- Draft one bounded `LabelSpec` inside the scoped task and budget.
- Select the next required gate for downstream independent review.

## Forbidden Decisions And Actions

- Self-review or self-approval.
- Promotion or candidate approval.
- Large-scale or broad label materialization.
- Label value commits.
- Label-as-feature or treating a label as a feature.
- Bypassing accepted-`DatasetVersion` policy.
- Weakening the leakage guard.
- Reading raw provider data or making external provider calls.
- Runtime bypass or diagnostics execution.
- Session-context feature dependencies before `SESSION_LABEL_GUARD_FIX_V1`.
- Value-consuming scans before `FEATURE_LABEL_PARQUET_SINK_V1`.
- Alpha, tradability, profitability, strategy, paper/live, broker, deployment,
  or production claims.

## Required Handoff

The handoff uses refs only:

- `request_id`
- `task_id` or `scope_ref`
- `alpha_spec_id`
- `label_spec_ref` or `label_pack_ref`
- `dataset_version_id`
- `next_required_gate`
- `limitations`

## Reviewer Independence

The Label Engineer is an implementer. It is never the reviewer or approver of
its own label spec or seed reference. Downstream independent review remains
required, and the role never self-approves.

## Failure And Rejection Modes

The role fails closed when inputs are blocked, refs are not admissible, a
preflight blocker is active, or the request exceeds bounded task or budget scope.
It returns a structured blocked or limited result ref with limitations and the
next gate. It does not silently pass.

## Boundaries

This role consumes existing governance, registry, permission, and tool-result
contracts by reference. It does not edit or duplicate those primitives, resolve
datasets itself, access raw data, create heavy artifacts, materialize values,
start an autonomous runner, weaken leakage guards, or call broker/paper/live/
external provider surfaces.
