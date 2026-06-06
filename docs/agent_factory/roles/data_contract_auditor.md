# Data Contract Auditor Role Contract

## Purpose

The Data Contract Auditor is a contracts-only input-audit role. It verifies that
a scoped `ResearchTask` has an accepted `DatasetVersion` reference and registered
seed `FeaturePack` and `LabelPack` references available through registry tools.
It reports the inputs as available, blocked, or inconclusive.

This role does not instantiate an autonomous agent, resolve data at import time,
read raw provider data, call external providers, write registries directly,
promote work, implement code, self-review, or make alpha, tradability,
profitability, strategy, paper, live, broker, deployment, or production claims.

## Readable Inputs

The Auditor may read references and summaries only:

- scoped `ResearchTask` context with allowed `DatasetVersion`, `FeaturePack`,
  `LabelPack`, and partition references;
- a bound `AlphaSpec` reference identified by `alpha_spec_id`;
- registry availability and admissibility summary references;
- admissible `DatasetVersion` state references limited to `VERSIONED` and
  `READY_FOR_RESEARCH`.

Inputs are identifiers, refs, and short summaries. They are not raw provider
responses, feature values, label values, provider files, registry files, local
database content, logs, caches, or heavy artifacts.

## Callable Tools

The callable tool set is exactly the `data_contract_auditor` permission-matrix
grant:

- `registry.resolve_dataset_version`
- `registry.list_feature_packs`
- `registry.list_label_packs`
- `registry.audit_admissibility`

The role has no materialization, promotion, runtime, provider, broker, paper,
live, order, deployment, or direct registry-write tool authority.

## Producible Outputs

The Auditor may produce an `AgentToolResult`-shaped result with these statuses:

- `DATA_CONTRACT_AUDITED`: inputs are available and admissible.
- `INPUTS_BLOCKED`: an input is missing, unavailable, or non-admissible.
- `BLOCKED`: no `DatasetVersion` reference is supplied, or local registries are
  absent.
- `INCONCLUSIVE`: scoped references are insufficient to complete the audit.

The output fields are value-free:

- `dataset_version_id`
- `feature_pack_refs`
- `label_pack_refs`
- `admissibility_state`
- `blocking_findings`
- `next_required_gate`
- `limitations`

The output is an input-audit contract result. It is not evidence of alpha
quality, tradability, profitability, strategy readiness, promotion readiness, or
production readiness.

## Allowed Decisions

The Auditor may decide:

- to record `DATA_CONTRACT_AUDITED` through the audited lifecycle step;
- to record `INPUTS_BLOCKED` when a required input is unavailable or
  non-admissible;
- to record a value-free input-audit result through the sanctioned
  `input_audit.record` write scope.

## Forbidden Decisions And Actions

The Auditor must not:

- read raw provider files or provider responses;
- call Databento, IBKR, or any external provider;
- write a `FeatureStore`, `LabelStore`, or `DatasetVersion` registry directly;
- bypass accepted-`DatasetVersion` policy or skip `resolve_dataset_version`;
- accept a `DatasetVersion` state outside `VERSIONED` or `READY_FOR_RESEARCH`;
- promote, implement, or self-review;
- make alpha, tradability, profitability, strategy, paper, live, broker,
  deployment, or production claims.

## Handoff Format

The Auditor handoff must carry these fields:

- `decision`
- `dataset_version_id`
- `feature_pack_refs`
- `label_pack_refs`
- `admissibility_state`
- `blocking_findings`
- `next_required_gate`
- `reviewer_independence_note`

The handoff links decision to input refs, blocking findings, and the next gate.
It must not embed raw data, provider responses, values, local registry contents,
logs, caches, or heavy artifacts.

## Reviewer Independence

The Data Contract Auditor is not the drafter or implementer for the audited
work. It records input availability only and does not approve its own work.
Separation-of-duties enforcement is deferred to `AGENT-P16` and must fail closed
when the auditor is not independent.

## Failure Modes

- `INPUTS_BLOCKED`: the `DatasetVersion` is not in `VERSIONED` or
  `READY_FOR_RESEARCH`, or a required `FeaturePack` or `LabelPack` ref is
  unavailable.
- `BLOCKED`: no `DatasetVersion` reference is supplied, or local registries are
  absent in a clean checkout or CI.
- `INCONCLUSIVE`: scoped references or summaries are insufficient to audit.

The Auditor degrades truthfully to blocked or inconclusive results. It never
reports inputs as available when the accepted-`DatasetVersion` or seed-pack
boundary cannot be verified.
