# Frontier Workflow 2

## Purpose

Workflow 2 is the Ralph-driven strict campaign loop for `alpha_system`. It uses the campaign contract as the source of work, Codex as the scoped executor, Claude as reviewer/verifier, and local run artifacts for audit and resume.

This harness is control-plane scaffolding. It does not provide broker integration, paper trading, live trading, order routing, production deployment, or research-platform source behavior.

## State Machine

The Workflow 2 state order is:

```text
RUN_INIT -> CAMPAIGN_LOAD -> PHASE_SELECT -> SPEC_GENERATE -> SPEC_VALIDATE -> WORKTREE_CREATE -> CODEX_EXECUTE -> CHECKS_RUN -> HANDOFF_VALIDATE -> CLAUDE_REVIEW -> VERDICT_PARSE -> PR_CREATE -> CI_WAIT -> MERGE_GATE -> MERGE -> DONE_CHECK -> NEXT_PHASE -> CAMPAIGN_DONE_CHECK -> RUN_SUMMARY
```

Ralph must not skip required states. A phase may stop, block, or route to bounded repair when checks, review, artifact policy, STOP, GitHub gates, or semantic done-checks fail.

## Roles

Ralph owns the driver loop, state transitions, run ledgers, STOP checks, validation orchestration, handoff validation, Claude review routing, verdict parsing, bounded repair routing, PR creation, CI wait, merge-gate enforcement, merge execution when allowed, done-checks, next-phase selection, and run summaries.

Codex executes the generated phase spec. Codex may create or update only paths authorized by the phase, run only checks authorized by the phase, repair only in-scope findings routed by Ralph, and write truthful handoffs. Codex must not call Claude, run reviewer, create verdict files, create PRs, merge, or mark phases PASS unless the active spec explicitly delegates that work.

Claude Opus 4.8 xhigh is the reviewer for Yellow and Red phases. It verifies state-machine completeness, lane policy, artifact discipline, scope control, STOP/resume behavior, handoff truthfulness, and semantic readiness.

Claude Sonnet 4.6 supports verifier, source-map, audit, and mechanical inspection work.

ChatGPT provides strategic reasoning, campaign framing, and post-run review.

## Lanes

Green is low-risk automatic work. It still requires checks, artifact policy, handoff validation, no STOP, and semantic done-check before merge eligibility.

Yellow is material engineering or research work. It requires fresh Claude Opus review, a parsed `PASS` or `PASS_WITH_WARNINGS` verdict, passing local checks, artifact policy, handoff validation, no STOP, CI when configured, and semantic done-check before merge eligibility.

Red covers external, destructive, live, production, costly, or broker-adjacent work. Red requires scoped authorization before execution or merge eligibility:

```text
PROJECT_OP_AUTHORIZED
PROJECT_OP_SCOPE
PROJECT_OP_EXPIRES
```

Ralph must verify the authorization flag, scope match, and expiry before any Red-lane operation. `ALPHA_SYSTEM_V1` is expected to avoid Red scope.

## Run Artifacts

`runs/**` is local-only runtime state. It exists for audit and resume, but it must never be staged or committed.

Run-level convention:

```text
runs/<run_id>/RUN_GOAL.md
runs/<run_id>/PHASE_PLAN.md
runs/<run_id>/state.json
runs/<run_id>/events.jsonl
runs/<run_id>/costs.jsonl
runs/<run_id>/progress.txt
runs/<run_id>/STOP
runs/<run_id>/RUN_SUMMARY.md
```

Phase-level convention:

```text
runs/<run_id>/phases/<phase_id>/spec.md
runs/<run_id>/phases/<phase_id>/executor_prompt.md
runs/<run_id>/phases/<phase_id>/executor_notes.md
runs/<run_id>/phases/<phase_id>/checks.json
runs/<run_id>/phases/<phase_id>/handoff.md
runs/<run_id>/phases/<phase_id>/review.md
runs/<run_id>/phases/<phase_id>/verdict.json
runs/<run_id>/phases/<phase_id>/repair_attempts/
```

Commit-eligible handoffs belong under `handoffs/<phase_id>.md`. Commit-eligible review artifacts belong under `reviews/**`. Run-local handoff, checks, review, verdict, and repair-attempt files remain local-only.

## STOP And Resume

`runs/<run_id>/STOP` requests a controlled stop. Ralph checks it before phase selection, provider calls, Codex execution, checks, review, PR creation, CI wait, merge gate, merge, done-check, next-phase selection, and campaign closeout.

Resume starts from recorded state and durable local artifacts. Resume must not regenerate completed specs, hide failed attempts, or mark a phase complete without the required handoff, checks, review when required, verdict, and done-check.

## Repair Bounds

Checks or review failures route to bounded repair attempts under:

```text
runs/<run_id>/phases/<phase_id>/repair_attempts/
```

Repair attempts are local-only and must be counted. If the allowed attempts are exhausted, Ralph must stop with a truthful blocked handoff rather than creating false completion.
