# Runtime Bridge

## Purpose

`alpha_system.agent_factory.runtime_bridge` is the Agent Factory boundary that
adapts Research Runtime structured outputs into `AgentToolResult`. It consumes
`RuntimeToolResult` and `RuntimeRunSummary`; it does not run diagnostics,
recompute runtime logic, read provider files, materialize feature or label
values, write registries, instantiate an agent, or create a continuous runner.

The bridge is the single runtime-output adapter in Agent Factory. It imports
the runtime and the dataset-version resolver, never edits runtime, governance,
research, feature, label, or data-foundation primitive packages.

## Field Mapping

| Runtime field | AgentToolResult field |
| --- | --- |
| `status` | `status`: `BLOCKED`, `REJECTED`, and `INCONCLUSIVE` map directly; other runtime decision states map to `OK` as value-free forward outcomes. |
| caller-supplied role | `role` |
| caller-supplied request id | `request_id` |
| caller-supplied bound AlphaSpec id | `alpha_spec_id` |
| caller-supplied bound StudySpec id | `study_spec_id` |
| `version_ids.dataset_version_id` | `dataset_version_id` after `resolve_dataset_version` succeeds |
| `version_ids.feature_pack_ids` | `feature_pack_refs` |
| `version_ids.label_pack_ids` | `label_pack_refs` |
| `run_id` | `runtime_run_id` |
| `diagnostics_summary.report_refs`, `coverage_summary_json`, `quality_summary_json` | `diagnostics_summary` as a compact string of refs and summary JSON only |
| `cost_summary` | `cost_summary` as compact scalar summary text, or `None` |
| `rejection_reasons` | `rejection_reasons` as short structured reason strings |
| terminal runtime reasons | `blocking_findings` as short structured blocking strings |
| `next_required_gate` | `next_required_gate` |
| `artifacts` | `artifacts` as artifact refs only |
| `diagnostics_summary.limitations` | `limitations` |

`RuntimeToolResult` and `RuntimeRunSummary` follow the same mapping path.

## Outcome Handling

The bridge handles every runtime decision state defensively. Runtime `BLOCKED`,
`REJECTED`, and `INCONCLUSIVE` remain non-success `AgentToolResult` statuses and
keep their visible runtime reasons and blocking findings. Forward runtime states
produce an `OK` envelope only to indicate that the adapter produced a structured
result; the runtime `next_required_gate` still controls what may happen next.

`cost_summary=None`, empty report refs, empty artifacts, and empty limitations
are valid and remain empty or `None`. Missing bound `AlphaSpec` or `StudySpec`
ids are rejected by the bridge before adaptation; the bridge does not invent
spec references.

## Dataset Boundary

Dataset inputs resolve only through
`alpha_system.data.foundation.version_registry.resolve_dataset_version`. A
resolved DatasetVersion is admissible only when its supplied or record-provided
lifecycle state is `VERSIONED` or `READY_FOR_RESEARCH`. Missing registry
records, id mismatches, missing lifecycle state, and any other lifecycle state
produce a fail-closed `BLOCKED` `AgentToolResult` with
`next_required_gate=resolve_dataset_version`.

The bridge never opens raw provider files and never reads canonical, feature,
label, cache, or database artifacts.

## Value-Free Guarantee

Outputs carry only ids, refs, short summaries, rejection or blocking strings,
artifact refs, limitations, and the next required gate. They do not carry raw
bars, BBO records, feature values, label values, provider responses, dataframe
objects, report objects, local database rows, logs, caches, or heavy payloads.

The final construction step is `AgentToolResult`, so the existing AGENT-P05
value-free validation still rejects raw/heavy markers, bytes, dataframe or array
objects, duplicate refs, and heavy artifact suffixes.

## No-Claims Boundary

A runtime diagnostic PASS or completed runtime state adapted by this bridge is
not factor promotion, alpha validation, candidate approval, Reference
validation, strategy validation, tradability evidence, profitability evidence,
paper-trading approval, live-trading approval, broker authorization, deployment
approval, or production readiness.

An adapted `EvidenceDraft` is not a candidate. An adapted
`ReferenceCandidateHandoff` is not Reference validation. Human review and the
existing Frontier gates remain required.
