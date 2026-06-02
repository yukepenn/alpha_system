# STOP And Resume

## STOP File

Workflow 2 uses a run-scoped STOP file:

```text
runs/<run_id>/STOP
```

The file is local-only runtime state. It must never be staged or committed.

## Required STOP Checks

Ralph must check for STOP before:

```text
RUN_INIT
PHASE_SELECT
SPEC_GENERATE
SPEC_VALIDATE
WORKTREE_CREATE
CODEX_EXECUTE
CHECKS_RUN
HANDOFF_VALIDATE
CLAUDE_REVIEW
VERDICT_PARSE
PR_CREATE
CI_WAIT
MERGE_GATE
MERGE
DONE_CHECK
NEXT_PHASE
CAMPAIGN_DONE_CHECK
RUN_SUMMARY
```

If STOP is active, Ralph must not call providers, run Codex, run review, create a PR, wait on CI, evaluate a merge gate, merge, mark done, or select the next phase.

## Codex Behavior

Codex must not ignore an active STOP file when executing inside a Workflow 2 run. If a STOP file appears during execution, Codex should finish only the minimal safe write needed to record a truthful handoff or blocked note, then stop without widening scope.

Codex must not create `review.md`, `verdict.json`, PRs, merges, live operations, paper operations, broker operations, order routing, production deployments, or destructive cleanup while responding to STOP/resume handling.

## Resume

Resume starts from recorded run state and existing local run artifacts. Ralph should inspect:

```text
runs/<run_id>/state.json
runs/<run_id>/events.jsonl
runs/<run_id>/progress.txt
runs/<run_id>/phases/<phase_id>/
```

Resume should continue from the last durable state. It must not hide failed checks, discard repair attempts, regenerate completed work without a reason, or mark a phase complete without required checks, handoff, review when required, verdict, artifact policy, and semantic done-check.

## Repair And Blocked States

When checks or review fail, Ralph routes to bounded repair attempts under:

```text
runs/<run_id>/phases/<phase_id>/repair_attempts/
```

Repair attempts are local-only. If the same blocker repeats or the repair budget is exhausted, Ralph must record a truthful blocked state and require human or external-state intervention before continuing.

## Local-Only Rule

All STOP and resume files under `runs/**` are local-only. Commit-eligible phase handoffs belong under:

```text
handoffs/<phase_id>.md
```

Review artifacts intended for git belong under:

```text
reviews/**
```
