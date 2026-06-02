# alpha_system

`alpha_system` is a local-first, research-only trading harness for developing an Alpha Research Platform under Frontier Harness Generic `0.3.0-rc1`.

The active campaign is `ALPHA_SYSTEM_V1`, defined in `campaigns/ALPHA_SYSTEM_V1/`. This repository is not a broker, paper-trading, live-trading, order-routing, or production execution system. Do not make alpha, profitability, robustness, or tradability claims without evidence and review.

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

ASV1-P00 is policy and scaffold only. It does not add source code, domain schemas, data ingestion, registry logic, backtesting, hook enforcement, CI workflows, deployment, or trading operations. Additional hook, CI, and artifact-policy enforcement work is deferred to ASV1-P01.

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
git ls-files runs
```

`git diff --cached --name-only` must contain no `runs/` path, and `git ls-files runs` must return empty for ASV1-P00.

## Artifact Policy

Never commit raw data, canonical generated data, materialized factor values, materialized label values, local SQLite or DB files, heavy artifacts, generated reports, logs, caches, local model artifacts, credential material, or local environment files.

Local-only paths include:

- `runs/**`
- data payloads under `data/raw/`, `data/canonical/`, `data/factors/`, `data/labels/`, and `data/cache/`
- local DB files under `metadata/`
- generated outputs under `artifacts/`

Permitted placeholders are limited to `.gitkeep` or `README.md` files where the campaign policy allows them. The commit-eligible phase handoff for ASV1-P00 is `handoffs/ASV1-P00.md`; run-local handoffs under `runs/<run_id>/...` are never staged or committed.

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
python tools/frontier/bootstrap.py doctor
just frontier-run-campaign <campaign>
just frontier-run-next <campaign>
just frontier-run-campaign-mock <campaign>
just frontier-run-next-mock <campaign>
just frontier-run-campaign-ledger <campaign>
just frontier-run-overnight <campaign>
just frontier-resume <run_id>
just frontier-tail <run_id>
just frontier-summary <run_id>
just frontier-stop <run_id>
just frontier-heartbeat <run_id>
just frontier-acceptance
```
