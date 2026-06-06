# Agent Handoff Template

Synthetic, value-free placeholder template for Agent Factory handoffs. This is
not an agent run, runtime request, alpha claim, data read, provider call,
strategy validation, factor promotion, broker action, paper action, live action,
order action, deployment, or production action.

## Index

1. Record Identity
2. Decision Link
3. Tool Invocation Links
4. Spec and Runtime Refs
5. Findings and Next Gate
6. Version Refs
7. Limitations

## 1. Record Identity

- `handoff_id`: `agent_handoff:placeholder`
- `request_id`: `request:placeholder`
- `from_role_id`: `diagnostics_runner`
- `to_role_id`: `statistical_reviewer`

## 2. Decision Link

- `decision_id`: `agent_decision:placeholder`
- `run_id`: `agent_run:placeholder`
- `decision_kind`: `request_runtime_diagnostics`
- `classification`: `ALLOWED`
- `rationale_summary`: `Bounded task refs and accepted DatasetVersion refs only.`
- `next_required_gate`: `statistical_reviewer_independent_review`

## 3. Tool Invocation Links

- `tool_invocation_id`: `tool_invocation:placeholder_runtime_diagnostics`
- `tool_name`: `runtime.run_diagnostics`
- `caller_role_id`: `diagnostics_runner`
- `input_refs`:
  - `study_spec:placeholder`
  - `dataset_version:placeholder_versioned`
- `result_status`: `OK`
- `result_artifact_refs`:
  - `artifact_ref:placeholder_diagnostics_summary`

## 4. Spec and Runtime Refs

- `alpha_spec_id`: `alpha_spec:placeholder`
- `study_spec_id`: `study_spec:placeholder`
- `dataset_version_id`: `dataset_version:placeholder_versioned`
- `feature_pack_refs`:
  - `feature_pack:placeholder_seed`
- `label_pack_refs`:
  - `label_pack:placeholder_seed`
- `runtime_run_id`: `runtime_run:placeholder`

## 5. Findings and Next Gate

- `blocking_findings`: []
- `rejection_reasons`: []
- `summary`: `Decision, tool invocation, and spec refs are linked for review.`
- `next_required_gate`: `statistical_reviewer_independent_review`

## 6. Version Refs

- `prompt_version_ref`: `prompt_version:placeholder_v1`
- `role_version_ref`: `role_version:diagnostics_runner_v1`
- `permission_version_ref`: `permission_version:diagnostics_runner_v1`

## 7. Limitations

- `contract_only`
- `refs_and_summaries_only`
- `no_raw_or_heavy_payloads`
- `not_alpha_evidence`
- `not_factor_promotion`
- `not_strategy_validation`
