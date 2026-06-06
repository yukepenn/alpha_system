# Agent Factory Permissions

## Purpose

`alpha_system.agent_factory.permissions` defines the contracts-only permission
model for the Agent Factory. It is default-deny and fail-closed: a role gets no
tool, data, write, review, or promotion capability unless the static matrix gives
that role an explicit entry.

This layer declares policy data only. It does not instantiate an autonomous
agent, call a tool, read data, call a provider, start a runner, promote a factor,
or add broker, paper, live, order, account, deployment, strategy, backtest,
portfolio, or production behavior.

## Permission Primitives

| Primitive | Meaning | Default |
| --- | --- | --- |
| `ToolPermission` | Declarative tool ids a role may call. Tool contracts are added later. | No tools. |
| `DataPermission` | Declarative accepted-DatasetVersion-only reference scope. Raw and provider scopes are rejected. | No data access. |
| `WritePermission` | Declarative write scopes allowed only through sanctioned tool APIs. Direct registry writes are rejected. | No writes. |
| `ReviewPermission` | Whether the role may issue a critique or review verdict, with independence required. | No review verdict. |
| `PromotionPermission` | Whether the role may promote. Promotion grants are invalid in this campaign. | No promotion. |
| `HumanApprovalRequired` | Actions reserved for human risk, capital, or live judgment. | No marked actions in a default-deny placeholder. |
| `RedLaneRequired` | Actions that would require scoped Red-lane authorization. | No marked actions in a default-deny placeholder. |
| `RolePermissions` | The complete permission entry for one `role_id`, containing exactly one of each primitive. | All grants denied. |

All fields are immutable and value-free. They carry short declarative strings
only, never raw data, provider payloads, DB rows, runtime values, feature values,
label values, local registries, logs, caches, or heavy artifact references.

`RolePermissions.default_deny(role_id)` exists for explicit deny entries. The
matrix lookup itself does not synthesize entries for unknown roles. Unknown or
empty role ids raise, so downstream wiring can fail closed.

## Matrix Table

| Role | Tools | Data scope | Write scope | Review | Promotion | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| `research_director` | Queue scoping, role assignment, budget declarations. | None. | Research task scope draft only. | Denied. | Denied. | Scopes one bounded task but cannot approve evidence, review, promote, or search broadly. |
| `hypothesis_scout` | Rejected-idea lookup, prior-work summary, AlphaSpec drafting. | None. | AlphaSpec draft only. | Denied. | Denied. | Generates drafts but cannot approve, implement, run diagnostics, or promote. |
| `alpha_spec_critic` | AlphaSpec critique, revision request, rejection. | None. | Critique record only. | `alphaspec_critique`. | Denied. | Independent critic may reject or request revision but cannot draft the reviewed spec or implement it. |
| `data_contract_auditor` | DatasetVersion resolution and feature/label pack admissibility checks. | Accepted DatasetVersion, FeaturePack, and LabelPack references only. | Input audit record only. | Denied. | Denied. | Verifies inputs through registry tools without raw access or registry writes. |
| `feature_engineer` | Seed feature reference, bounded FeatureRequest drafting, request validation. | Accepted DatasetVersion and FeaturePack references only. | FeatureRequest draft only. | Denied. | Denied. | May draft bounded feature requests but cannot self-review, materialize broadly, commit values, or promote. |
| `label_engineer` | Seed label reference, bounded LabelSpec drafting, spec validation. | Accepted DatasetVersion and LabelPack references only. | LabelSpec draft only. | Denied. | Denied. | May draft bounded label specs but cannot self-review, materialize broadly, use labels as features, or promote. |
| `no_lookahead_auditor` | Runtime no-lookahead audit and governance leakage checks. | None. | Lookahead audit record only. | Denied. | Denied. | Issues an audit record without promotion authority or guard-weakening authority. |
| `diagnostics_runner` | Runtime plan, input validation, diagnostics, label diagnostics, signal probe, cost stress, summary. | Accepted DatasetVersion reference only. | Runtime request record only. | Denied. | Denied. | Requests runtime diagnostics for a bound StudySpec without altering specs, bypassing runtime, or promoting. |
| `statistical_reviewer` | Statistical evidence review and verdict issuance. | None. | Statistical review record only. | `runtime_evidence_review`. | Denied. | Independent reviewer may issue PASS, REJECT, WATCH, or INCONCLUSIVE and cannot implement the reviewed work. |
| `librarian` | Decision ledger, rejection ledger, rejected-idea lookup, memory proposal. | None. | Decision and memory update proposals after verdict only. | Denied. | Denied. | Records decisions and proposed memory after a reviewer verdict without direct registry writes or promotion. |

## Separation Implications

The matrix keeps generation, implementation, diagnostics, review, memory, and
promotion concerns separate:

- The Hypothesis Scout can draft but cannot review its own draft.
- The AlphaSpec Critic can review AlphaSpec drafts but cannot implement them.
- Feature and Label Engineers can draft bounded contracts but cannot review
  their own work.
- The Diagnostics Runner can request runtime diagnostics but cannot alter specs
  or promote.
- The Statistical Reviewer can issue an independent verdict but cannot be the
  implementer.
- The Librarian can propose memory updates after a verdict but cannot write
  registries directly or promote.

Every role carries human-approval markers for risk judgment, capital allocation,
factor promotion, paper trading, live trading, broker operations, and order
routing. Every role carries Red-lane markers for external provider calls,
production deployment, paper trading, live trading, broker operations, and order
routing. These markers do not grant those actions; they make the reservation
explicit for downstream enforcement.

## Boundary

This permission layer does not enforce a live tool call. It supplies declarative
data and pure lookup functions for later phases. `AGENT-P16` wires registered
roles to this matrix and enforces separation of duties. `AGENT-P05` defines the
tool contracts that these declarative tool ids will gate.
