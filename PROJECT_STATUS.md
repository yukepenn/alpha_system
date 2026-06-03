# Project Status

Project: `alpha_system`

## Current State

- Harness profile: `trading_research`
- Template version: `3.0.0`
- Generated: `2026-05-31T21:48:47+00:00`
- Workflow 1: available
- Workflow 2: provider-wired conductor available for `ALPHA_SYSTEM_V1`
- Auto-merge: enabled through the protected-branch PR path when `FRONTIER_ALLOW_AUTOMERGE=1`
- Active campaign: `ALPHA_SYSTEM_V1`
- Current phase pointer: `ACTIVE_CAMPAIGN.md`
- Latest local run summary: `runs/<run_id>/RUN_SUMMARY.md`
- Canonical repo path: `~/projects/alpha_system`
- Required filesystem: WSL2 Linux filesystem

Post-closeout status:

- Latest release baseline: ALPHA_SYSTEM_V1 executor-complete with warnings on deterministic
  fixtures.
- Current post-closeout work: ASV1_RELEASE_HYGIENE.
- Next intended campaign: ALPHA_RESEARCH_GOVERNANCE_MVP.

`ACTIVE_CAMPAIGN.md` is the tracked phase-progress pointer that Ralph updates through reviewed phase commits. This file is a stable project orientation note, not the authoritative live ledger.

## Non-Negotiable Policy

- Stage explicit paths only; never `git add .` and never `git add -A`.
- Do not force push.
- Do not commit raw data, heavy artifacts, generated local outputs, local SQLite or DB files, caches, logs, model artifacts, local environment files, or credential material.
- Keep `runs/**` local-only. `git ls-files runs` must return empty.
- Keep `.frontier/upgrade_reports/**` local-only. `git ls-files .frontier/upgrade_reports` must return empty.
- Do not hide failed runs.
- Do not weaken or game tests.
- Do not introduce alpha, profitability, robustness, or tradability claims without evidence and review.

## Normal Workflow 2 Commands

```bash
just frontier-run-next ALPHA_SYSTEM_V1
just frontier-run-next-x ALPHA_SYSTEM_V1 <phase_count>
```

These commands create the phase PR, wait for required checks, run merge gate, and use the normal protected-branch merge path with auto-merge fallback when needed. They do not use `--admin`.

## Documentation Pointers

- Campaign contract: `campaigns/ALPHA_SYSTEM_V1/`
- Current phase pointer: `ACTIVE_CAMPAIGN.md`
- Phase handoffs: `handoffs/`
- Reviews and verdicts: `reviews/`
- Architecture and domain docs: `docs/`
- Run-local audit trail: `runs/<run_id>/`

Use this file for concise project-level orientation before reading individual campaign artifacts.
