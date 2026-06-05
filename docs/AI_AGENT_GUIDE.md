# AI Agent Guide

## Purpose

This guide is for AI Agents operating `alpha_system` under Frontier Harness
Generic v3.0 Workflow 2. It restates the role boundaries and safety rules an
agent must preserve while executing a phase.

Do not broaden an active phase. Do not hide failed runs. Do not create broker,
paper, live, order-routing, deployment, or production behavior. Do not claim
alpha, profitability, robustness, tradability, approval, or readiness from
fixtures, diagnostics, grids, ML scores, reports, or backtests.

## Role Boundaries

Ralph owns the strict driver loop:

- run initialization
- campaign loading
- phase selection and spec validation
- STOP checks
- validation orchestration
- handoff validation
- review routing
- verdict parsing
- bounded repair routing
- PR creation
- CI waiting
- merge gates
- merge
- semantic done-checks
- run summaries

Codex owns scoped execution:

- read the generated phase spec
- make only in-scope changes
- run only authorized local checks
- repair only routed in-scope findings
- write truthful commit-eligible handoffs
- keep run-local artifacts out of git

Claude review is a separate Ralph-routed step. Yellow and Red phases require
review. Green documentation phases may skip review when the spec says review is
not required.

ChatGPT owns strategy, campaign framing, and post-run reasoning.

## Workflow 2 State Machine

Workflow 2 follows this order:

```text
RUN_INIT -> CAMPAIGN_LOAD -> PHASE_SELECT -> SPEC_GENERATE -> SPEC_VALIDATE -> WORKTREE_CREATE -> CODEX_EXECUTE -> CHECKS_RUN -> HANDOFF_VALIDATE -> CLAUDE_REVIEW -> VERDICT_PARSE -> PR_CREATE -> CI_WAIT -> MERGE_GATE -> MERGE -> DONE_CHECK -> NEXT_PHASE -> CAMPAIGN_DONE_CHECK -> RUN_SUMMARY
```

An executor must not skip ahead to review, verdict, PR, CI, merge, or done
states. Those are Ralph-owned gate actions.

The 13 per-phase stages (`spec -> execute -> validate -> review -> done_check ->
commit -> push -> pr -> ci -> branch_protection -> merge_gate -> merge ->
complete`) are unchanged. The scheduler sits **above** `PHASE_SELECT`: it decides
which phase(s) enter the loop and in what order.

## Scheduling: Sequential And DAG Wave

`frontier.yaml` `workflow2.scheduler` (overridable per campaign) chooses how
phases are selected:

- `mode: sequential` (default): phases run in list order, one at a time —
  unchanged behaviour.
- `mode: dag_wave`: Ralph selects the dependency-ready set. With
  `parallel_execution: true` and `max_parallel_phases > 1` (or `--parallel`), a
  conflict-free, parallel-safe wave **builds concurrently** in isolated worktrees
  and **merges serially** through a merge queue. `python tools/frontier/ralph_driver.py
  plan-dag --campaign-id <id>` previews the plan without running anything.

Optional per-phase scheduler metadata in `campaign.yaml` (all default to the
conservative run-alone choice, so omitting them keeps sequential behaviour):

- `parallel_safe: true` — eligible to share a wave (requires `allowed_paths`).
- `allowed_paths: [...]` / `forbidden_paths: [...]` — declared write scope; two
  phases with overlapping `allowed_paths` never share a wave.
- `conflicts_with: [...]` — never co-run with the listed phases.
- `resource_class: [...]` — phases sharing an exclusive resource never co-run.
- `must_run_alone: true` — always its own wave.
- `merge_group: <name>` — keep group members adjacent in the merge queue.

In a parallel wave the **coordinator owns `ACTIVE_CAMPAIGN.md`**: executors and
phase branches must never write it, so concurrent branches cannot conflict on the
pointer. RED phases never parallelize unless RED scope is armed. Merge is always
serial, even when builds run concurrently.

## STOP And Resume

A file at `runs/<RUN_ID>/STOP` is an active stop request. Ralph must check STOP
before provider calls, phase selection, Codex execution, validation, review, PR
creation, CI waiting, merge gates, merge, done-checks, and next-phase
selection. Codex must not ignore an active STOP file when acting inside a
Workflow 2 run.

Resume must continue from recorded run state. Do not regenerate completed work
unless the recorded state requires it.

## Phase Execution Checklist

For each phase:

1. Read `AGENTS.md`, `frontier.yaml`, `ACTIVE_CAMPAIGN.md`, the campaign
   contract, the generated spec, and referenced handoffs or reviews.
2. Confirm no active STOP file exists for the run.
3. Confirm the lane, allowed paths, forbidden paths, and artifact policy.
4. Inspect the working tree before edits.
5. Edit only in-scope files.
6. Run only checks authorized by the spec.
7. Preserve all failures in the handoff.
8. Stage only explicit allowed paths when staging is required.
9. Verify `git diff --cached --name-only` has no forbidden path.
10. Verify `git ls-files runs` is empty.
11. Write the commit-eligible handoff under `handoffs/<PHASE_ID>.md`.

## Handoff Rules

The handoff must be truthful and specific. Include:

- scope completed
- files changed
- explicit staged paths when staging occurred
- validation commands and results
- skipped or unavailable checks with exact reasons
- artifact-policy confirmation
- run-local versus commit-eligible separation
- no source behavior changes unless explicitly authorized
- no broker/live trading, paper trading, or order-routing scope
- no unsupported alpha, profitability, robustness, or tradability claims
- review status or review-skipped reason
- known limitations
- relevant risks

Run-local handoffs under `runs/<run_id>/...` are local-only. Commit-eligible
handoffs belong under `handoffs/<PHASE_ID>.md`.

## Repair Loop

Repair only valid in-scope findings routed by Ralph. Do not expand allowed
paths, weaken tests, hide failed runs, delete failure records, or mutate
unrelated files to get a clean result.

If the spec is contradictory, authorization is missing, validation repeatedly
fails for the same reason, or accuracy would require forbidden source/test/data
changes, write a blocked handoff and stop dependent progression.

## Artifact Discipline

Never stage or commit:

- `runs/**`
- raw data
- canonical generated data
- factor stores
- label stores
- caches
- local SQLite, DB, journal, or WAL files
- generated reports or bundles
- artifacts under `artifacts/**`
- Parquet, Arrow, or Feather files unless a later spec explicitly permits a
  tiny synthetic fixture
- logs
- model binaries
- credential material
- local environment files

Use explicit staging only. These are forbidden examples:

```text
git add .
git add -A
```

Force push is forbidden.

## Data-Heavy Phases

Before any data-heavy phase, read `docs/data_foundation/README.md`,
`docs/data_foundation/DATASET_VERSION.md`,
`docs/data_foundation/DATASET_CONSUMPTION.md`, and
`docs/data_foundation/PARTITION_PLAN.md`. IBKR data entry points live under
`src/alpha_system/data/ibkr/` (`connector.py`, `backfill_connect.py`,
`materialize.py`); use `docs/data_foundation/BACKFILL_RUNBOOK.md` only for an
authorized backfill. Dry-run, smoke, and synthetic modes are CI-safe; real
external pulls require `ALPHA_IBKR_*`/data-pull env gates and never run in CI.

## Avoid Hidden Failed Runs

Failed steps, rejected configs, missing artifacts, warnings, dirty-tree state,
unavailable tools, and validation failures are part of the record. Preserve
them in run-local state and handoffs. Do not rerun until only the successful
case remains unless the failed attempts are still visible.

## Escalating Blocked States

Escalate as blocked when:

- the spec conflicts with higher-level policy
- an active STOP condition remains unresolved
- required authorization is missing for Red or broker-adjacent scope
- completing accurately requires forbidden paths or behavior changes
- validation cannot be made truthful within the allowed scope
- repeated repair attempts hit the same blocking condition

A blocked handoff is better than false completion.
