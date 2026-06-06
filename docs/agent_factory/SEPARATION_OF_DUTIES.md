# Agent Factory Separation of Duties

## Purpose

`alpha_system.agent_factory.separation` assembles the MVP role contracts with
the permission matrix and evaluates value-free, fail-closed separation rules.
It is a contracts-and-enforcement layer only. It does not instantiate an
autonomous agent, start a continuous runner, run diagnostics, access data,
promote a factor, call a broker, or make an alpha, tradability, profitability,
paper, live, deployment, or production claim.

The separation layer consumes the existing role registry and permission matrix
as-is. It does not edit concrete role modules, `roles/__init__.py`,
`roles/registry.py`, runtime, governance, registry, research, feature, label,
data, CLI, broker, live, paper, order, strategy, backtest, portfolio, or
management primitives.

## Rule Results

Every rule returns a `SeparationRuleResult` with:

- `rule_id`
- `status`: `PASS` or `BLOCKED`
- `role_ids`
- `reason`

The result is value-free. It carries only stable ids, statuses, role refs, and
short reasons. It never carries raw data, provider payloads, DB rows, runtime
values, feature values, label values, local registry contents, caches, logs, or
heavy artifact paths.

All rules default to `BLOCKED` when input is missing, unknown, malformed, or
ambiguous. There is no implicit pass.

## Rules

| Rule id | Invariant | Fail-closed behavior |
| --- | --- | --- |
| `generator_approver_separation` | A generator cannot approve its own artifact. | Blocks when artifact, generator, approver, or known-role input is missing; blocks when `generator_role_id == approver_role_id`. |
| `implementer_reviewer_separation` | An implementer cannot review its own work class. | Blocks when work class, implementer, reviewer, or known-role input is missing; blocks when `implementer_role_id == reviewer_role_id`. |
| `promotion_permission_denied` | No MVP role may hold `PromotionPermission`; Diagnostics Runner specifically cannot promote. | Blocks when the matrix or expected role ids are missing, when an entry is incomplete, or when any inspected entry has `promotion.can_promote == True`. |
| `reviewer_assignment_independent` | A concrete reviewer assignment must not equal the implementer for the same work item. | Blocks when work item, implementer, reviewer, or known-role input is missing; blocks when reviewer equals implementer. |
| `librarian_verdict_required` | Librarian write paths require a bound reviewer verdict ref. | Blocks when the role, write scope, or known-role input is missing; blocks when the role is not `librarian`; blocks when `reviewer_verdict_ref` is absent. |

Two assembly guards support the required fail-closed wiring behavior:

- `permission_matrix_coverage` blocks unless the validated bundle contains
  exactly the ten MVP roles and every role has a complete permission entry.
- `human_reserved_flags_preserved` blocks unless every matrix entry preserves
  the `HumanApprovalRequired` and `RedLaneRequired` markers for reserved
  actions.

These guards do not grant human-reserved or Red-lane actions. They verify that
the existing matrix markers were not weakened by wiring.

## Wiring Assembly

`alpha_system.agent_factory.separation.wiring` is the single Agent Factory
module that imports all ten concrete MVP role modules:

- `research_director`
- `hypothesis_scout`
- `alpha_spec_critic`
- `data_contract_auditor`
- `feature_engineer`
- `label_engineer`
- `no_lookahead_auditor`
- `diagnostics_runner`
- `statistical_reviewer`
- `librarian`

Importing those modules lets each role self-register through the existing
discovery registry. `assemble_validated_bundle()` then builds an immutable
`SeparationBundle` with:

- `roles_by_id`
- `permissions_by_role_id`
- `rule_results`
- aggregate `status`

By default, `assemble_validated_bundle()` raises `SeparationWiringError` if any
rule is `BLOCKED`. Callers may pass `raise_on_blocked=False` to receive the
blocked bundle for diagnostics without treating it as approved.

The default wiring assignments are deliberately narrow:

- Hypothesis Scout generates AlphaSpec drafts; AlphaSpec Critic approves or
  rejects them.
- Feature Engineer, Label Engineer, and Diagnostics Runner outputs are routed
  to independent audit or review roles.
- Diagnostics Runner is checked against all promotion grants and specifically
  cannot promote.
- Librarian write scopes are validated as verdict-bound paths.

The wiring registers the ten MVP roles and requires a complete permission
matrix entry for each. Missing roles, missing matrix entries, promotion grants,
weakened human-approval markers, weakened Red-lane markers, self-review, and
missing Librarian verdict refs are all `BLOCKED`.

## Boundary

This layer is deterministic and local. It does not call tools, run the research
runtime, read provider files, materialize feature or label values, write
registries, create records, create reviews, create verdicts, create PRs, merge,
or operate broker, paper, live, order, account, or deployment surfaces.

Downstream phases may consume the structured `SeparationBundle` and
`SeparationRuleResult` objects, but they must still preserve the same
separation-of-duties, reviewer-independence, human-approval, Red-lane, artifact,
and no-claims boundaries.
