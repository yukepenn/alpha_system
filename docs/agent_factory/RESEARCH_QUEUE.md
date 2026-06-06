# Agent Factory Research Queue

## Purpose

`alpha_system.agent_factory.queue.models` defines the contracts-only research
queue and work-item schema for `ALPHA_AGENT_FACTORY_MVP`. It scopes a finite set
of operator-declared `ResearchTask` objects. It does not instantiate an agent,
read data, call the runtime, run diagnostics, start a scheduler, perform alpha
search, promote a factor, validate a strategy, or create broker, paper, live,
order, account, deployment, backtest, portfolio, profitability, tradability, or
production behavior.

The queue is a boundary object: it says what one bounded task may reference,
which partitions are allowed or blocked, what finite budget applies, what
independent reviews are required, and what the next contract action is.

## Schema

| Contract | Meaning |
| --- | --- |
| `ResearchQueue` | Finite ordered collection of `ResearchTask` objects governed by a deterministic `QueuePriorityPolicy` and a queue-level `FamilyBudgetPolicy`. |
| `ResearchTask` | One bounded unit of work with task status, admissible input refs, alpha-family scope, partition scope, required reviews, retry policy, rejection/blocker metadata, next action, and finite budget. |
| `AgentAssignment` | Binds one known role id to one task id. It carries no permission grants; AGENT-P04 remains the permission authority. |
| `ResearchBudget` | Composes a mandatory `VariantBudget` and `ComputeBudget`. |
| `VariantBudget` | Hard finite `max_variants` cap, currently capped at 25 variants per task. |
| `ComputeBudget` | Hard finite `max_runtime_minutes` cap, currently capped at 720 minutes per task. |
| `ReviewRequirement` | Declares an independent review role and the reviewed roles it must be independent from. It records intent only and performs no review. |
| `BlockerRecord` | Structured, value-free blocker record for input, locked-test metadata, parquet-sink, session-label-guard, or scope blockers. |
| `QueuePriorityPolicy` | Deterministic operator-priority ordering with `task_id` tie breaking. |
| `FamilyBudgetPolicy` | Queue-level per-family caps for task count, variants, and runtime minutes. |

All contracts are frozen dataclasses. Constructing them performs no I/O, opens no
file, resolves no registry entry, imports no runtime primitive, and calls no
provider. Validation rejects bytes, dataframe/array-like objects, mutable
collections where tuples are required, raw/provider/heavy payload markers,
heavy artifact paths, and prohibited continuous-runner markers.

## Single-Task-Bounded Guarantee

The queue has no scheduler, next-cycle field, result-driven enqueue behavior, or
self-feeding task generator. It only stores the finite task tuple an operator or
Research Director has already placed. `ordered_tasks()` returns those declared
tasks in deterministic priority order; it does not create new work.

`RetryPolicy` is also bounded. `max_attempts` is mandatory, finite, and capped.
Zero means no retry; a positive retry count must list the statuses it applies to.
There is no null or "unlimited" retry state.

The task lifecycle rejects these prohibited MVP states:

```text
ALPHA_VALIDATED
FACTOR_PROMOTED
STRATEGY_READY
PORTFOLIO_READY
CANDIDATE_PROMOTED
LIVE_READY
PAPER_READY
PROFITABLE
TRADABLE
PRODUCTION_READY
AUTONOMOUS_RESEARCH_RUNNING
```

`AUTONOMOUS_RESEARCH_RUNNING` belongs to a future separately authorized runner,
not this MVP contract layer.

## Inputs And Partitions

A task carries admissible input references only:

- `allowed_dataset_version_id`
- `allowed_dataset_version_state`, limited to `VERSIONED` or `READY_FOR_RESEARCH`
- `allowed_feature_pack_refs`
- `allowed_label_pack_refs`

These are ids and refs, not values. The queue does not resolve a
`DatasetVersion`, read a registry, read raw provider files, or embed feature or
label data.

Partition refs are explicit:

- `development`: 2018-01-01 through 2022-12-31
- `validation`: 2023-01-01 through 2024-12-31
- `locked_test_candidate`: 2025-01-01 through `as_of_run`
- `latest_shadow_candidate`: optional rolling recent period

The same partition cannot be both allowed and blocked. If locked-test is
allowed, governance contamination metadata refs are mandatory. If that metadata
is absent, the task can instead carry `locked_test_candidate` in
`blocked_partitions` and record a
`LOCKED_TEST_GOVERNANCE_METADATA_REQUIRED` blocker.

## Future Blockers

The queue can represent, but does not resolve, campaign blockers:

- `FEATURE_LABEL_PARQUET_SINK_REQUIRED`: large-scale value-consuming studies are
  blocked until `FEATURE_LABEL_PARQUET_SINK_V1`.
- `SESSION_LABEL_GUARD_FIX_REQUIRED`: session-context features such as
  `rth_flag`, `eth_flag`, or `session_minute` are blocked until
  `SESSION_LABEL_GUARD_FIX_V1`.

These blockers are value-free records. They do not read data, run checks, or
grant authorization.

## Boundaries

This module is a contract layer only. It does not prove alpha, tradability,
profitability, strategy readiness, portfolio readiness, paper readiness, live
readiness, broker readiness, or production readiness. A queued task, completed
review, dry-run route, evidence draft, or reference handoff remains inside the
Agent Factory contract boundary until later separately authorized governance
and human gates act.
