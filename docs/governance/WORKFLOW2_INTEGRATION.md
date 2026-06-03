# Workflow 2 Governance Integration

`ALPHA_RESEARCH_GOVERNANCE_MVP` uses Frontier Workflow 2 for phase execution,
review, verdict parsing, merge gates, and campaign closeout. Governance artifacts
must follow the Workflow 2 artifact boundary so local run state stays local-only
and durable audit artifacts live in commit-eligible paths.

This document adds no new governance object, gate rule, CLI command, canary type,
or public runtime interface. It records the artifact mapping used by ARGOV-P19.

## Artifact Boundary

| Artifact | Run-local path | Commit-eligible path |
| --- | --- | --- |
| Codex executor handoff copy | `runs/<run_id>/phases/<phase_id>/handoff.md` | `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/<PHASE_ID>.md` |
| Reviewer notes | `runs/<run_id>/phases/<phase_id>/review.md` | `reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/**` only when reviewer-written and selected for git |
| Parsed verdict | `runs/<run_id>/phases/<phase_id>/verdict.json` | `reviews/ALPHA_RESEARCH_GOVERNANCE_MVP/**` only when reviewer-written and selected for git |
| Validation/check ledger | `runs/<run_id>/phases/<phase_id>/checks.json` and run validation files | Handoff summary under `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/<PHASE_ID>.md` |
| Repair attempts | `runs/<run_id>/phases/<phase_id>/repair_attempts/` | Repair handoff or durable review note only if explicitly in scope |
| Run summary and state | `runs/<run_id>/**` | None |

`runs/**` is local-only runtime state. It must not be staged or committed.
`git ls-files runs` is expected to return empty before merge-gate evaluation.

## Responsibilities

Codex executor scope:

- execute the generated phase spec;
- edit only commit-eligible in-scope files;
- run authorized local checks requested by the spec;
- write the commit-eligible handoff;
- use explicit staging by path.

Ralph driver scope:

- check STOP files at Workflow 2 checkpoints;
- orchestrate validation, handoff validation, review, verdict parsing, repair
  routing, PR creation, CI, merge gates, merge, done-checks, and run summary;
- keep run-local artifacts under `runs/**`;
- reject staged `runs/**` paths and forbidden artifacts.

Independent reviewer scope:

- write semantic review artifacts when routed by Ralph;
- perform Yellow-lane review and the final campaign-wide semantic done-check;
- produce the verdict that Ralph parses.

Codex must not create `review.md`, `verdict.json`, PRs, CI state, merge results,
or phase PASS records.

## Governance Closeout Exercise

ARGOV-P19 exercises the integration without adding new runtime code:

- ARGOV-P00 through ARGOV-P18 have run-local handoff, review, verdict, validation,
  done-check, PR, CI, and merge-gate artifacts under
  `runs/2026-06-03T135209Z_ALPHA_RESEARCH_GOVERNANCE_MVP/phases/<PHASE_ID>/`.
- The durable executor handoff trail for those phases lives under
  `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P00.md` through
  `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P18.md`.
- ARGOV-P19 writes its commit-eligible handoff to
  `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P19.md`.
- The ARGOV-P19 executor does not create or stage a run-local `handoff.md`,
  `review.md`, `verdict.json`, `checks.json`, or `repair_attempts/` artifact.
- The artifact audit confirms `git ls-files runs` is empty and the staged set has
  no `runs/` path.

This is an artifact-boundary exercise only. It does not perform reviewer work,
verdict parsing, PR creation, CI waiting, merge, broker work, live work, paper
work, order routing, real-data ingestion, or alpha search.

## Closeout Checks

ARGOV-P19 records these checks in the commit-eligible handoff:

```bash
git status --short
python tools/verify.py --smoke
python tools/verify.py --all
python -m pytest tests/unit/governance -q
python -m pytest tests/integration/governance -q
python tools/hooks/canary_runner.py
test -f campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/CLOSEOUT.md
test -f docs/governance/WORKFLOW2_INTEGRATION.md
find data -type f ! -name README.md ! -name .gitkeep -print
find metadata -type f ! -name README.md ! -name .gitkeep -print
git ls-files runs
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
git diff --cached --name-only
```

All command output that matters for the phase result belongs in the ARGOV-P19
handoff. Run-local check ledgers remain under `runs/**`.
