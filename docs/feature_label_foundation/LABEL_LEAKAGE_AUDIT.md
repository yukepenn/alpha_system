# Label Leakage And Availability Audit

`alpha_system.labels.leakage_audit` audits registered labels after local
materialization and registry integration. It produces a
`LabelLeakageAuditReport` for each `LabelRegistryRecord` and fails closed when a
label can be reached as a live feature, overlaps a forbidden feature reference,
or cannot prove correct `label_available_ts` ordering.

The module is descriptive substrate only. It does not calculate labels,
materialize values, persist registries, read raw provider files, call external
providers, expose labels as features, or make alpha, tradability, profitability,
strategy, backtest, portfolio, broker, live, paper, order, account, deployment,
or production-readiness claims.

## Governance Consumption

The audit consumes the existing governance
`alpha_system.governance.label_leakage_guard.check_label_leakage(...)` and the
governance `LabelSpec` snapshot bound inside the registered label contract. It
does not edit or re-implement `label_leakage_guard.py`, `label_spec.py`,
`study_spec.py`, `feature_request.py`, or `duplicate_exposure.py`.

For each registered label, the audit passes caller-supplied live feature
references to the governance guard. The guard enforces:

- `label_as_feature`: live feature references must not match
  `LabelSpec.forbidden_feature_overlap`.
- `availability_time`: live feature information time must precede the governed
  label `availability_time`.

The report stores the governance result and converts every governance finding
into a blocking audit finding.

## Label Identity Boundary

The audit also checks that live feature references do not directly expose the
registered label identity. A reference to the registered label id, label version
id, or governed label spec id is blocking even when the feature's information
time is otherwise earlier than the label availability boundary.

This check prevents a materialized label series from becoming reachable as a
feature by name or version handle.

## `label_available_ts` Audit

The registry stores metadata only, so the audit requires the caller to supply
the local in-memory `LabelValueRecord`s, or equivalent value mappings, for the
registered label version. Missing value records are blocking because the audit
cannot prove per-row availability ordering from metadata alone.

For every supplied value record, the audit checks:

- `label_version_id` matches the registered `LabelVersion`.
- optional `label_spec_id` matches the registered governance `lspec_`.
- `event_ts`, `horizon_end_ts`, and `label_available_ts` are present and
  timezone-aware.
- `horizon_end_ts >= event_ts`.
- `label_available_ts >= event_ts`.
- `label_available_ts >= horizon_end_ts`, so joins cannot make the label usable
  before the forward outcome is known.
- `label_available_ts >= LabelSpec.availability_time`.

The audit also checks the registry summary timestamps
`first_label_available_ts` and `last_label_available_ts` against the governed
availability time. Any missing, malformed, mismatched, or too-early timestamp is
blocking.

## Status

`LabelLeakageAuditReport.status` is `CLEAN` only when there are no blocking
findings. Any leakage, missing metadata, unavailable value rows, or availability
ordering violation returns `BLOCKED`.

The report exposes both `blocking_findings` and `non_blocking_findings`. FLF-P23
currently uses blocking findings for all leakage and availability violations;
the non-blocking channel is reserved for future descriptive warnings without
weakening fail-closed behavior.

## Scope Boundary

The audit layer consumes already-local, accepted-DatasetVersion-derived
materialization outputs and registry records. It does not read `.dbn`, `.zst`,
parquet, arrow, feather, provider responses, raw/canonical data directories, or
local registry DBs directly.

`LabelLeakageAuditReport` is a safety and availability audit. A clean report
does not imply alpha value, profitability, tradability, strategy readiness,
backtest validity, portfolio suitability, broker readiness, live readiness, or
production readiness.
