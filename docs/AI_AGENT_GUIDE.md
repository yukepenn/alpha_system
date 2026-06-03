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
