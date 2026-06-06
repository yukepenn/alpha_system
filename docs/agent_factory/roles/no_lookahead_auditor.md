# No-Lookahead Auditor Role Contract

## Purpose

The No-Lookahead Auditor audits Research Runtime output refs for
point-in-time integrity. It consumes the existing
`alpha_system.runtime.audit.no_lookahead` audit and the
`alpha_system.governance.label_leakage_guard` guard through the sanctioned tool
surface, then emits a value-free lookahead `PASS` or `BLOCKED` decision.

This is a contract-only role. It does not instantiate an autonomous agent, run
diagnostics, retry runtime work, edit runtime or governance code, read provider
data, promote a factor, validate a strategy, or make alpha, tradability,
profitability, broker, paper, live, deployment, or production claims.

## Readable Inputs

The Auditor may read references and summaries only:

- `RuntimeToolResult` and `RuntimeRunSummary` refs;
- `NoLookaheadAuditResult` summary refs;
- `LabelLeakageResult` and `LabelLeakageFinding` summary refs;
- bound `AlphaSpec` and `StudySpec` ids;
- `dataset_version_id`, FeaturePack refs, and LabelPack refs;
- availability, same-bar-fill, and locked-test discipline refs.

These inputs are identifiers, refs, and short summaries. They are not raw
provider data, feature values, label values, runtime values, provider
payloads, local database content, logs, caches, or heavy artifacts.

## Callable Tools

The callable tool set is exactly the permission-matrix grant for
`no_lookahead_auditor`:

- `runtime.audit_no_lookahead`
- `governance.check_label_leakage`

The agent-facing review tool contract maps these matrix refs to the
`review.no_lookahead_audit` surface. The role module checks the matrix-derived
tool set at import time and fails closed if it drifts.

## Producible Outputs

The Auditor emits only an `AgentToolResult`-shaped record with value-free
fields:

- `status`: lookahead `PASS` carried as `OK`, or `BLOCKED` for leakage,
  missing fields, same-bar-fill, or locked-test failures;
- `role`: `no_lookahead_auditor`;
- `request_id`;
- `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`;
- FeaturePack and LabelPack refs;
- `blocking_findings`;
- `rejection_reasons`;
- `next_required_gate`;
- artifact refs;
- limitations and no-claims notes.

The output is an integrity gate result. It is not evidence of alpha quality,
tradability, profitability, candidate readiness, strategy validity, broker
readiness, paper readiness, live readiness, deployment readiness, or production
readiness.

## Allowed Decisions

The Auditor may decide:

- lookahead `PASS` when the supplied runtime audit and label-leakage guard refs
  are clean and complete;
- `BLOCKED` when availability, label leakage, same-bar-fill, locked-test, or
  missing-field conditions fail;
- the next required independent downstream review gate.

## Forbidden Decisions And Actions

The Auditor must not:

- promote a factor, candidate, strategy, or evidence bundle;
- weaken, bypass, or reimplement the no-lookahead audit or label-leakage guard;
- run diagnostics, retry runtime work, or resolve runtime inputs itself;
- draft or critique `AlphaSpec` contracts;
- review its own implementation or its own diagnostics output;
- read raw provider data, feature values, label values, or runtime values;
- make external provider calls;
- bypass the runtime input resolver or the sanctioned tool surface;
- write feature, label, dataset, promotion, or registry state directly;
- make risk, capital, paper, live, broker, order, account, deployment, or
  production decisions;
- make alpha, tradability, profitability, strategy, portfolio, deployment, or
  production-readiness claims.

## Required Handoff

The Auditor handoff uses structured references only:

- `request_id`
- `role`
- `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`
- runtime run summary ref
- no-lookahead audit summary ref
- label-leakage finding summary refs
- `status`
- `blocking_findings`
- `rejection_reasons`
- `next_required_gate`
- artifact refs
- `limitations`

The handoff must surface every blocker that prevents an integrity decision. A
missing `available_ts`, `label_available_ts`, same-bar-fill policy ref, or
locked-test partition ref is never treated as a silent pass.

## Reviewer Independence

The Auditor is independent from the drafter, implementer, and diagnostics
runner. Its lookahead decision is an integrity gate only and still requires the
next independent downstream review before any lifecycle advance. The Auditor
cannot self-approve its implementation or its own diagnostics output.

## Failure And Rejection Modes

The Auditor fails closed when:

- feature availability metadata violates point-in-time discipline;
- label availability metadata or label leakage findings block the run;
- same-bar-fill or locked-test discipline is violated;
- required audit refs are missing or inconclusive;
- the permission matrix or tool surface does not grant the audit call.

Failure output is `BLOCKED` or `INCONCLUSIVE`, never a silent `PASS`. No output
from this role authorizes alpha search, factor promotion, candidate promotion,
paper trading, live trading, broker operations, order routing, deployment, or
production use.
