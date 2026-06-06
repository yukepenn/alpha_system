# Agent Factory Handoff and Record Contracts

`alpha_system.agent_factory.records.models` defines passive, value-free record
contracts for Agent Factory activity. They make agent work auditable without
instantiating agents, starting runners, executing tools, writing registries,
reading raw data, or creating alpha, tradability, profitability, broker, paper,
live, order, deployment, or production behavior.

## Record Model

- `AgentRunRecord` records one bounded role run for a `request_id`, queue ref,
  task ref, run status, start/end refs, summary, and limitations.
- `AgentDecisionRecord` records one role decision, its allowed-or-forbidden
  classification, rationale summary, next required gate, and optional
  `SeparationRuleResult` refs from `agent_factory.separation`.
- `ToolInvocationRecord` records one agent-facing tool call. It validates the
  tool name and caller against `agent_factory.tools.registry` and stores the
  structured `AgentToolResult` from `agent_factory.tools.results`.
- `AgentHandoff` links one `AgentDecisionRecord` to one or more
  `ToolInvocationRecord` objects and to the referenced `alpha_spec_id`,
  `study_spec_id`, `dataset_version_id`, FeaturePack refs, LabelPack refs, and
  `runtime_run_id`.
- `AgentAuditLog` carries ordered run, decision, tool-invocation, handoff, and
  version refs so the lifecycle can be reconstructed by ref.
- `AgentPromptVersion`, `AgentRoleVersion`, and `AgentPermissionVersion` stamp
  prompt, role, and permission changes by role, version label, approval ref,
  effective-time ref, superseded version ref, summary, and limitations.

The contracts consume existing Agent Factory primitives by import path:
`permissions.matrix.ROSTER_ROLE_IDS`, `queue.models.ResearchTaskStatus`,
`separation.enforcement.SeparationRuleResult`,
`tools.registry.resolve`, and `tools.results.AgentToolResult`. They do not
duplicate those primitives and do not edit runtime, governance, research,
feature, label, data, CLI, broker, live, paper, order, or strategy packages.

## Decision to Tool to Spec Link

An `AgentHandoff` is valid only when:

- the decision role and request match the handoff role and request;
- every linked tool invocation was made by that same role for that same request;
- every linked tool invocation validates against the allowed-tool registry;
- each handoff spec/runtime ref is present in at least one linked
  `AgentToolResult`; and
- pack refs on the handoff are a subset of pack refs returned by linked tool
  results.

This makes the chain explicit:

```text
AgentDecisionRecord
  -> ToolInvocationRecord(s)
  -> AgentToolResult refs
  -> AlphaSpec / StudySpec / DatasetVersion / FeaturePack / LabelPack /
     RuntimeRun refs
  -> next required gate
```

The record does not store raw values, arrays, provider responses, reports, DB
rows, parquet/arrow/feather/dbn/zst files, SQLite/DB paths, caches, logs, or
heavy artifacts.

## Audit Log

`AgentAuditLog` is append-style. It stores declared refs and an
`ordered_activity_refs` sequence. All run, decision, tool-invocation, and
handoff refs must appear in the ordered sequence. Version refs can also be
attached so prompt, role, and permission versions used by the run are traceable.

The audit log is a record, not a writer. It does not persist itself, write a
ledger, update memory, write the FeatureStore/LabelStore, update DatasetVersion
registries, or call a provider.

## Value-Free Contract

Record fields accept only short strings, ids, refs, summaries, statuses, nested
record contracts, and tuples of refs. They fail closed on:

- bytes, mutable collections, dataframe/array objects, or embedded value arrays;
- raw/provider payload markers, file-content markers, DB-row markers, or
  dataframe/array markers;
- raw/canonical/factor/label/cache/data/metadata/artifact paths; and
- heavy file suffixes such as parquet, arrow, feather, dbn, zst, sqlite, db,
  wal, npy, npz, pickle, joblib, onnx, and log.

Summaries must remain explanatory only. A diagnostic PASS, evidence draft, or
reference handoff recorded here is not factor promotion, candidate validation,
strategy validation, alpha evidence, tradability evidence, or approval for
paper/live/broker/order activity.
