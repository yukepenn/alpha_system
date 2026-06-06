# Statistical Reviewer Role Contract

## Purpose

The Statistical Reviewer issues an independent `PASS`, `REJECT`, `WATCH`, or
`INCONCLUSIVE` review on bound runtime evidence summary refs produced by the
Diagnostics Runner and gated by the No-Lookahead Auditor. It consumes the
existing `alpha_system.governance.reviewer_verdict` primitive as the durable
review vocabulary and returns a value-free `AgentToolResult` evidence opinion.

This is a contract-only role. It does not instantiate an autonomous agent, run
diagnostics, recompute statistics from values, edit runtime or governance code,
read provider data, promote a factor, validate a strategy, or make alpha,
tradability, profitability, broker, paper, live, deployment, or production
claims.

## Readable Inputs

The Reviewer may read references and summaries only:

- `RuntimeRunSummary` and `RuntimeToolResult` evidence summary refs;
- `diagnostics_summary` and `cost_summary`;
- upstream No-Lookahead audit summary ref and its `PASS` or `BLOCKED` status;
- bound `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`;
- FeaturePack refs, LabelPack refs, and `runtime_run_id`;
- `AgentToolResult` summary refs.

These inputs are identifiers, refs, and short summaries. They are not raw
provider data, feature values, label values, runtime values, provider payloads,
local database content, logs, caches, or heavy artifacts.

## Callable Tools

The callable tool set is exactly the permission-matrix grant for
`statistical_reviewer`:

- `review.statistical_evidence`
- `review.issue_verdict`

The role module derives this set from `permission_for("statistical_reviewer")`
and fails closed at import time if the contract drifts from the permission
matrix.

## Producible Outputs

The Reviewer emits only an `AgentToolResult`-shaped value-free record:

- `status`: `OK` for `PASS`, `REJECTED` for `REJECT`, `WARN` for `WATCH`, or
  `INCONCLUSIVE` for `INCONCLUSIVE`;
- `role`: `statistical_reviewer`;
- `request_id`;
- `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`;
- FeaturePack and LabelPack refs;
- `runtime_run_id`;
- `diagnostics_summary` and `cost_summary` summary refs;
- `rejection_reasons`;
- `blocking_findings`;
- `next_required_gate`;
- artifact refs;
- limitations and no-claims notes.

Conceptually the result may also be recorded as a `ReviewerVerdict`-shaped
value-free review record. The verdict is an opinion on evidence quality. It is
not factor promotion, candidate promotion, Reference validation, alpha
evidence, tradability evidence, profitability evidence, strategy validation,
broker readiness, paper readiness, live readiness, deployment readiness, or
production readiness.

## Allowed Decisions

The Reviewer may decide:

- `PASS`, `REJECT`, `WATCH`, or `INCONCLUSIVE` on bound runtime evidence whose
  upstream No-Lookahead audit has passed;
- `BLOCKED` or `INCONCLUSIVE` when required summary refs, bound specs, or audit
  gates are missing;
- the next required downstream gate, typically Librarian recording or human
  judgment.

## Forbidden Decisions And Actions

The Reviewer must not:

- promote a factor, candidate, strategy, or evidence bundle;
- implement or alter FeatureRequest, LabelSpec, AlphaSpec, or StudySpec
  contracts;
- run, retry, or reimplement diagnostics;
- review its own implementation or its own diagnostics;
- act as the Feature Engineer, Label Engineer, or Diagnostics Runner for the
  evidence it reviews;
- recompute statistics from raw values or bypass the runtime tool surface;
- read raw provider data, feature values, label values, or runtime values;
- make external provider calls;
- write feature, label, dataset, promotion, or registry state directly;
- make risk, capital, paper, live, broker, order, account, deployment, or
  production decisions;
- claim alpha, profitability, tradability, strategy validity, or production
  readiness;
- treat an `EvidenceDraft` as a candidate;
- treat a `ReferenceCandidateHandoff` as Reference validation.

## Required Handoff

The Reviewer handoff uses structured references only:

- `request_id`
- `role`
- `alpha_spec_id`, `study_spec_id`, and `dataset_version_id`
- FeaturePack refs and LabelPack refs
- `runtime_run_id`
- evidence summary ref
- No-Lookahead audit summary ref
- `status`
- `rejection_reasons`
- `blocking_findings`
- `next_required_gate`
- artifact refs
- `limitations`

The handoff must surface every blocker that prevents a verdict. Missing
evidence summary refs, a non-`PASS` No-Lookahead audit, or a missing bound
`AlphaSpec` or `StudySpec` is never treated as a silent `PASS`.

## Reviewer Independence

The Reviewer is independent from the Feature Engineer, Label Engineer, and
Diagnostics Runner. The reviewer role or agent must not equal the implementer
role or agent for the evidence under review, and the Reviewer cannot self-review
its own implementation or diagnostics output.

The verdict requires the upstream No-Lookahead audit to have passed. A `WATCH`
or any forward lifecycle advance requires this independent verdict and never
constitutes promotion.

## Failure And Rejection Modes

The Reviewer fails closed when:

- runtime evidence summary refs are missing or insufficient;
- the upstream No-Lookahead audit is not `PASS`;
- the bound `AlphaSpec` or `StudySpec` is missing;
- reviewer independence cannot be established;
- the permission matrix or tool surface does not grant the review call.

Failure output is `BLOCKED` or `INCONCLUSIVE`, never a silent `PASS`. No output
from this role authorizes alpha search, factor promotion, candidate promotion,
paper trading, live trading, broker operations, order routing, deployment, or
production use. Dry-run or seed-pack evidence is not alpha.
