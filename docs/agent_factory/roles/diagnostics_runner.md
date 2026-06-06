# Diagnostics Runner Role Contract

## Purpose

The Diagnostics Runner requests Research Runtime diagnostics for one bound
`AlphaSpec` and one bound `StudySpec` within the governing research, compute,
and variant budgets. It drives the runtime through the agent-facing
`RuntimeToolResult` / `RuntimeRunSummary` contracts and the `alpha runtime`
command surface.

This is a contract-only role. It does not instantiate an autonomous agent,
start a continuous research runner, recompute diagnostics, recompute cost
stress, perform overfit or no-lookahead logic itself, edit specs, promote a
factor, validate a strategy, read provider data, call external providers, or
make alpha, tradability, profitability, broker, paper, live, deployment, or
production claims.

A diagnostic `PASS` is not factor promotion, not alpha validation, not a
candidate decision, and not strategy validation. An `EvidenceDraft` is not a
candidate. A `ReferenceCandidateHandoff` is not Reference validation.

## Readable Inputs

The Runner may read references and summaries only:

- bound `AlphaSpec` id;
- bound `StudySpec` id;
- resolved admissible `DatasetVersion` id from `resolve_dataset_version`;
- seed FeaturePack and LabelPack refs;
- governing `ResearchTask`, `ResearchBudget`, `ComputeBudget`, and
  `VariantBudget` refs;
- `RuntimeToolResult` and `RuntimeRunSummary` refs.

The DatasetVersion must be accepted for research use, with admissible states
`VERSIONED` or `READY_FOR_RESEARCH`. Inputs are ids, refs, and short summaries,
not provider data, feature values, label values, runtime values, local database
content, logs, caches, or heavy artifacts.

## Callable Tools

The callable tool set is exactly the runtime tool-registry surface authorized
for this role:

- `runtime.plan`
- `runtime.validate_inputs`
- `runtime.run_diagnostics`
- `runtime.run_label_diagnostics`
- `runtime.run_signal_probe`
- `runtime.run_cost_stress`
- `runtime.build_evidence_draft`
- `runtime.build_reference_handoff`

These are invoked through the runtime bridge and `alpha runtime` surface when
that bridge is implemented by `AGENT-P21`. This role contract only names the
tools. It does not implement the bridge, call the runtime directly, or bypass
the runtime input resolver.

## Producible Outputs

The Runner emits only a value-free `AgentToolResult`-shaped record with:

- `status`: `OK`, `BLOCKED`, `REJECTED`, `INCONCLUSIVE`, or `WARN`;
- `role`: `diagnostics_runner`;
- `request_id`;
- `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`;
- FeaturePack and LabelPack refs;
- `runtime_run_id`;
- `diagnostics_summary`;
- `cost_summary`;
- `rejection_reasons`;
- `blocking_findings`;
- `next_required_gate`;
- artifact refs;
- limitations and no-claims notes.

Outputs carry statuses, ids, refs, short summaries, rejection reasons,
blocking findings, artifact refs, and the next required gate only. They never
carry provider data, feature or label values, runtime values, local database
content, logs, caches, or heavy artifacts.

## Allowed Decisions

The Runner may decide:

- to request diagnostics through the runtime tool surface within the bound
  research, compute, and variant budgets;
- `DIAGNOSTICS_COMPLETE`, `BLOCKED`, or `INCONCLUSIVE` based on runtime tool
  results;
- to surface runtime `blocking_findings`, `rejection_reasons`, and
  `limitations` without alteration;
- the next required independent review or repair gate.

## Forbidden Decisions And Actions

The Runner must not:

- promote a factor, candidate, strategy, evidence bundle, or reference handoff;
- alter, author, or mutate `FeatureRequest`, `LabelSpec`, `AlphaSpec`, or
  `StudySpec`;
- bypass the runtime input resolver or tool surface;
- reimplement diagnostics, cost stress, overfit logic, or no-lookahead logic;
- read provider data or call external providers;
- exceed the governing research, compute, or variant budgets;
- frame output as strategy validation, alpha, or candidate approval;
- self-review or issue a statistical verdict;
- write feature, label, dataset, runtime, promotion, or registry state
  directly;
- make risk, capital, broker, paper, live, order, account, deployment, or
  production decisions.

## Required Handoff

The Runner handoff follows the `AGENT-P17` record shape by reference only. It
links the decision to the tool invocation and the governing spec ids:

- `request_id`
- `role`
- decision and status
- `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`
- FeaturePack and LabelPack refs
- `runtime_run_id`
- runtime tool invocation refs
- diagnostics and cost summary refs
- `blocking_findings`
- `rejection_reasons`
- `next_required_gate`
- artifact refs
- `limitations`

The handoff must surface every runtime blocker, rejection, or inconclusive
state. It must not silently convert runtime `BLOCKED`, `REJECTED`, or
`INCONCLUSIVE` into a complete result.

## Reviewer Independence

The Diagnostics Runner is not the Statistical Reviewer and not a promoter:
runner is not reviewer, and runner is not promoter. Its output requires
independent downstream review before any lifecycle advance. The separation of
duties rules owned by `AGENT-P16` enforce this fail-closed.

## Failure And Rejection Modes

The Runner fails closed when:

- no bound `StudySpec` is supplied: no `StudySpec`, no diagnostics;
- the DatasetVersion is unresolved, inadmissible, or not accepted for research
  use;
- the research, compute, or variant budget is exhausted;
- the runtime tool surface returns `BLOCKED`, `REJECTED`, or `INCONCLUSIVE`;
- the runtime bridge is unavailable before `AGENT-P21`;
- the tool registry or permission matrix does not grant the requested runtime
  call.

Failure output is `BLOCKED` or `INCONCLUSIVE`, never a silent `PASS`. No output
from this role authorizes alpha search, factor promotion, candidate promotion,
Reference validation, strategy validation, paper trading, live trading, broker
operations, order routing, deployment, or production use.
