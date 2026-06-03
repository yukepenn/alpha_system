# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The active campaign is `ALPHA_SYSTEM_V1`, defined in `campaigns/ALPHA_SYSTEM_V1/`. Current phase progress is tracked in `ACTIVE_CAMPAIGN.md`; run-local state and summaries live under `runs/<run_id>/` and are never committed.

This repository is not a broker, paper-trading, live-trading, order-routing, or production execution system. Do not make alpha, profitability, robustness, or tradability claims without evidence and review.

## Current Repo Snapshot

`ALPHA_SYSTEM_V1` has completed phases `ASV1-P00` through `ASV1-P24`; after ASV1-P24 merges, the next planned phase is `ASV1-P25` L2 Readiness Schema and Design. The repo now includes the local-first harness baseline, core contracts, metadata registry, canonical 1-minute data layer, calendar/data-quality checks, factor and label foundations, factor diagnostics/reports, signal and strategy contracts, reference 1-minute backtest truth, cost/slippage semantics, position management, portfolio target/sizing, fast-path parity scaffolding, the bounded `alpha grid run` strategy grid MVP, the survivor-gated bounded `alpha management grid` workflow, hardened experiment registry modules for run records, artifact manifests, reproducibility metadata, promotion decisions, audit findings, failure visibility, version references, the ML/factor-combination MVP, and multi-symbol universe readiness.

The ASV1-P24 universe layer adds `src/alpha_system/data/universe.py`, `src/alpha_system/core/instruments.py`, `src/alpha_system/core/instrument_master.py`, `src/alpha_system/experiments/universe_runner.py`, `src/alpha_system/portfolio/universe_constraints.py`, `src/alpha_system/research/cross_sectional.py`, `docs/UNIVERSES_AND_MULTI_ASSET.md`, `docs/INSTRUMENT_MASTER.md`, and curated examples under `configs/universes/examples/`. Safety boundaries are unchanged: local-first execution only, SQLite remains local-only and uncommitted, reference engine remains the single PnL truth, fast path is acceleration-only and parity-gated, failed runs stay visible, promotion requires review, no broker/live/paper/deployment scope, no alpha/tradability claims, and explicit staging only.

Durable phase docs live under `docs/`, and commit-eligible handoffs live under `handoffs/`. The README is expected to stay as a compact project snapshot after each merged phase; detailed phase evidence belongs in handoffs, reviews, and run-local summaries.

## Repository Location

Canonical repo path:

```text
~/projects/alpha_system
```

The active repo and any active worktree must live on the WSL2 Linux filesystem. Do not run active work from `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, or temporary directories.

## Workflow 2 Boundary

Frontier Workflow 2 uses Ralph as the strict autonomous driver. Codex executes generated phase specs and writes executor output and handoffs. Ralph owns formal validation, Claude review, verdict parsing, repair orchestration, semantic done-checks, PR creation, CI, and merge gates.

Required safety defaults:

- STOP files stop before provider, done-check, PR, CI, merge, or next-phase actions.
- Failed runs must remain visible in run artifacts and handoffs.
- Yellow phases require fresh Claude Opus review before merge eligibility.
- No phase may weaken or game tests.

Normal provider-wired campaign commands:

```bash
just frontier-run-next ALPHA_SYSTEM_V1
just frontier-run-next-x ALPHA_SYSTEM_V1 <phase_count>
```

Both commands create PRs, wait for required checks, run merge gate, and attempt the normal protected-branch merge path with auto-merge fallback when GitHub branch policy is still settling. They do not use `--admin`.

Use `ACTIVE_CAMPAIGN.md` as the durable tracked pointer after each phase. Use `runs/<run_id>/RUN_SUMMARY.md` for the local audit trail of a specific run.

## Git Discipline

Use explicit staging only. Stage curated paths one by one.

Forbidden:

```bash
git add .
git add -A
git push --force
```

Before any commit, inspect:

```bash
git status --short
git diff --cached --name-only
git ls-files runs .frontier/upgrade_reports
```

`git diff --cached --name-only` must contain no `runs/` path, and `git ls-files runs .frontier/upgrade_reports` must return empty.

## Artifact Policy

Never commit raw data, canonical generated data, materialized factor values, materialized label values, local SQLite or DB files, heavy artifacts, generated reports, logs, caches, local model artifacts, credential material, or local environment files.

Local-only paths include:

- `runs/**`
- data payloads under `data/raw/`, `data/canonical/`, `data/factors/`, `data/labels/`, and `data/cache/`
- local DB files under `metadata/`
- generated outputs under `artifacts/`

Permitted placeholders are limited to `.gitkeep` or `README.md` files where the campaign policy allows them. Commit-eligible phase handoffs belong under `handoffs/<PHASE_ID>.md`; run-local handoffs under `runs/<run_id>/...` are never staged or committed.

## Documentation Map

Project-level orientation:

- `ACTIVE_CAMPAIGN.md`
- `PROJECT_STATUS.md`
- `AGENTS.md`
- `CLAUDE.md`

Architecture and workflow docs:

- `docs/PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/LOCAL_FIRST_STACK.md`
- `docs/RESEARCH_WORKFLOW.md`
- `docs/DOMAIN_BOUNDARIES.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/BACKTEST_TIERS.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/REPRODUCIBILITY_PRINCIPLES.md`
- `docs/CLI_COMMANDS_TARGET.md`

Domain docs are added by phase under `docs/`, with matching handoffs under `handoffs/`. The campaign source of truth remains `campaigns/ALPHA_SYSTEM_V1/`.

## Directory Layout

Commit-eligible policy and campaign files live under:

- `campaigns/`
- `specs/`
- `handoffs/`
- `reviews/`
- `docs/`
- `decisions/`
- `evals/`
- `configs/`

Local data and generated artifact roots are present for structure only:

- `data/raw/`
- `data/canonical/`
- `data/factors/`
- `data/labels/`
- `data/cache/`
- `metadata/`
- `artifacts/`
- `runs/`

## Useful Commands

```bash
python tools/verify.py --smoke
python tools/verify.py --all
python tools/hooks/canary_runner.py
python tools/frontier/bootstrap.py doctor
just frontier-run-campaign <campaign>
just frontier-run-next <campaign>
just frontier-run-next-x <campaign> <phase_count>
just frontier-run-campaign-mock <campaign>
just frontier-run-next-mock <campaign>
just frontier-run-next-x-mock <campaign> <phase_count>
just frontier-run-campaign-ledger <campaign>
just frontier-run-overnight <campaign>
just frontier-resume <run_id>
just frontier-tail <run_id>
just frontier-summary <run_id>
just frontier-stop <run_id>
just frontier-heartbeat <run_id>
just frontier-acceptance
```
