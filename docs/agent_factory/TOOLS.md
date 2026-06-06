# Agent Factory Tool Contracts

## Purpose

`alpha_system.agent_factory.tools` defines the contracts-only agent-facing tool
surface for `ALPHA_AGENT_FACTORY_MVP`. The package declares which tools exist,
which roster roles may call each one, what inputs are required, what every tool
must return, what side effects are forbidden, and how failures are represented.

This phase does not implement any tool execution. It does not import the runtime,
governance, data registry, FeatureStore, LabelStore, provider, broker, live,
paper, order, account, deployment, strategy, backtest, or portfolio surfaces.
The runtime bridge that adapts real runtime outputs into `AgentToolResult` is
deferred to `AGENT-P21`.

## Modules

| Module | Contract |
| --- | --- |
| `tools.contracts` | `ToolContract`, `ToolGroup`, `ToolArtifactPolicy`, and `ToolContractStatus`. |
| `tools.registry` | Default-deny registry loaded from `configs/agent_factory/tools/registry.toml`. |
| `tools.results` | `AgentToolResult`, the single structured result type all tools must return. |

The registry is read-only after construction. `resolve(tool_name, caller_role)`
returns a contract only when the tool is registered and the caller is explicitly
listed in that contract's `allowed_callers`. Unknown tools and disallowed callers
fail closed. Discovery helpers (`tool_names`, `groups`, `list_by_group`,
`contract_for`, `all_contracts`) describe the contract table but do not grant
authority to call a tool.

## Candidate Tool Groups

| Group | Tools | Allowed callers |
| --- | --- | --- |
| `registry` | `registry.list_datasets`, `registry.resolve_dataset_version`, `registry.list_feature_packs`, `registry.list_label_packs` | `data_contract_auditor` |
| `feature_label` | `feature.request`, `feature.validate_spec`, `feature.materialize`, `label.validate_spec`, `label.materialize` | `feature_engineer`, `label_engineer` |
| `runtime` | `runtime.plan`, `runtime.validate_inputs`, `runtime.run_diagnostics`, `runtime.run_label_diagnostics`, `runtime.run_signal_probe`, `runtime.run_cost_stress`, `runtime.build_evidence_draft`, `runtime.build_reference_handoff` | `diagnostics_runner` |
| `review` | `review.no_lookahead_audit`, `review.statistical_audit` | `no_lookahead_auditor`, `statistical_reviewer` |
| `ledger_memory_promotion` | `ledger.record_trial`, `evidence.build_bundle`, `memory.record_rejection`, `memory.record_watch`, `promotion.review` | `diagnostics_runner`, `statistical_reviewer`, `librarian` |

Each contract also records the AGENT-P04 permission-matrix tool ids that justify
its allowed callers. The P05 names are the agent-facing contract surface; some
map to broader P04 permission ids because implementations are intentionally
deferred.

## Tool Contract Fields

Each `ToolContract` declares:

- `name` and `group`
- `allowed_callers`
- `permission_matrix_refs`
- `required_inputs`
- `output_schema`, always `AgentToolResult`
- `forbidden_side_effects`
- `artifact_policy`, always `local_only`
- `failure_states`
- `required_reviewer`
- `reviewer_independence_note`
- `status`, one of `mvp`, `target`, or `future`

Every contract forbids direct registry writes, raw provider access, external
provider calls, raw/heavy result payloads, value materialization in this MVP,
and broker/paper/live/order scope. `promotion.review` is future contract-only
and still cannot promote anything without human approval.

## AgentToolResult

`AgentToolResult` has exactly these fields:

| Field | Meaning |
| --- | --- |
| `status` | One of `OK`, `BLOCKED`, `REJECTED`, `INCONCLUSIVE`, or `WARN`. |
| `role` | Calling roster role id. |
| `request_id` | Stable request id for traceability. |
| `alpha_spec_id` | Optional AlphaSpec id. |
| `study_spec_id` | Optional StudySpec id. |
| `dataset_version_id` | Optional accepted DatasetVersion id. |
| `feature_pack_refs` | FeaturePack refs only, never values. |
| `label_pack_refs` | LabelPack refs only, never values. |
| `runtime_run_id` | Optional runtime run id. |
| `diagnostics_summary` | Short value-free diagnostics summary. |
| `cost_summary` | Short value-free cost summary. |
| `rejection_reasons` | Structured rejection reason ids or short notes. |
| `blocking_findings` | Structured blocking findings. |
| `next_required_gate` | Next contract gate that must review or act. |
| `artifacts` | Opaque artifact refs only. |
| `limitations` | Short limitations and non-claim notes. |

Construction validates value-freeness. The result rejects bytes, dataframe or
array objects, mutable collection fields, duplicated refs, raw/provider payload
markers, embedded file contents, raw market record markers, and heavy artifact
references such as parquet, arrow, feather, DBN, zstd, SQLite/DB/WAL, model, log,
pickle, NumPy, and ONNX files.

## Boundaries

These contracts drive the existing registry, governance, and runtime primitives;
they do not duplicate or edit them. No tool in this phase resolves a real
DatasetVersion, executes diagnostics, materializes feature or label values,
builds an evidence bundle, writes a registry, reads provider data, calls an
external provider, or promotes a factor.

An `AgentToolResult` is not an alpha result, tradability claim, profitability
claim, promotion decision, production-readiness claim, broker instruction, or
approval to run paper/live trading. It is a structured envelope for later
contract gates.
