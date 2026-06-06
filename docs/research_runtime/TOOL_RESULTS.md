# Agent-Facing Tool Result Contracts

RT-P22 adds `alpha_system.runtime.tool_results`, the structured-output contract
surface that a later, separately authorized Agent Factory can consume when it
drives an approved `AlphaSpec` and `StudySpec` through the local research
runtime.

This phase only defines immutable, serializable contracts. It does not create an
autonomous agent, agent loop, runner, harness, scheduler, provider call, broker
operation, paper-trading path, live-trading path, PR action, merge action, or
deployment behavior.

## Contract Shape

`RuntimeToolResult` is the compact result for one approved runtime tool surface.
`RuntimeRunSummary` is the same value-free shape for the current state of a
bounded run. Both payloads carry only:

- `status`, normalized through `RuntimeDecisionState`;
- `run_id`;
- `version_ids`, extracted from `StudyRunManifest` or supplied as dataset,
  feature-pack, label-pack, code, and config version identifiers;
- `diagnostics_summary`, assembled from existing `DiagnosticsReport` summaries
  and report references;
- `cost_summary`, assembled from `CostSensitivityReport` with slippage labeled
  as a proxy;
- `rejection_reasons`, as visible `RejectionReasonRecord` payloads;
- `artifacts`, as summary artifact references only;
- `next_required_gate`.

The contracts consume existing runtime objects by their real import paths:
`StudyRunRecord`, `StudyRunManifest`, `RuntimeArtifactManifest`,
`RuntimeArtifactEntry`, `RuntimeArtifactRef`, `DiagnosticsReport`,
`DiagnosticsReportRef`, `CostSensitivityReport`, and `RejectionReasonRecord`.
They do not redefine those primitives or duplicate their validation ownership.

## Status Surface

`status` uses the closed runtime decision-state surface. Forward states include
the runtime lifecycle and descriptive runtime outcomes already used by the
campaign, such as input resolution, plan validation, diagnostics completion,
signal-probe completion, cost-stress completion, evidence-draft readiness, and
reference-handoff readiness.

Terminal non-success states are:

- `REJECTED`
- `INCONCLUSIVE`
- `BLOCKED`

Terminal results must carry at least one matching `RejectionReasonRecord`.
Forward states must not carry rejection reasons. The prohibited MVP states
`ALPHA_VALIDATED`, `FACTOR_PROMOTED`, `STRATEGY_READY`, `PORTFOLIO_READY`,
`LIVE_READY`, `PAPER_READY`, `PROFITABLE`, `TRADABLE`, and
`PRODUCTION_READY` are not representable.

## No Raw Or Heavy Data

Tool results are summaries and references, not data containers. They reject
raw/value/heavy fields in mapping inputs, including feature or label value
arrays, canonical bars, provider payloads, provider rows, raw values, data-frame
or series payloads, and heavy artifact paths such as Parquet, Arrow, Feather,
DBN, ZST, SQLite/DB/WAL, NumPy, pickle, joblib, ONNX, and log files.

Artifact entries in a tool result are normalized to `artifact_id`, relative
`location`, and `content_hash` references. They cannot carry artifact payloads
or provider responses. Heavy and value-bearing runtime outputs remain governed
by the runtime artifact policy and stay local-only.

## Interpretation

The contracts are agent-facing orchestration surfaces only. A diagnostic PASS is
not alpha validation. A signal probe is not a strategy candidate. A bounded grid
is not promotion. An `EvidenceDraft` is not a candidate. A
`ReferenceCandidateHandoff` is not Reference validation or Reference truth. The
fast path is not Reference truth.

The module makes no alpha, tradability, profitability, strategy, portfolio,
paper, live, broker, order-routing, deployment, or production-readiness claim.
