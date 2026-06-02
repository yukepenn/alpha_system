# ASV1-P00 Handoff

## Summary

ASV1-P00 established the repo and harness bootstrap policy foundation for `alpha_system` without adding implementation code. The work documents the canonical repo path `~/projects/alpha_system`, WSL2 Linux filesystem requirement, forbidden active worktree locations, explicit-staging-only git discipline, local-only artifact policy, `runs/**` separation, campaign layout, and placeholder roots for local data/artifact directories.

No source package, tests, schemas, data ingestion, factor logic, labels, diagnostics, registry logic, backtesting, broker, paper trading, live trading, order routing, hook enforcement, CI workflow, PR, merge, deployment, destructive cleanup, or phase PASS marking was introduced.

## Directory Tree Summary

Commit-eligible policy and campaign roots now exist or remain present:

* `campaigns/ALPHA_SYSTEM_V1/`
* `specs/`
* `handoffs/`
* `reviews/`
* `evals/`
* `docs/`
* `decisions/`
* `configs/`
* `data/raw/`
* `data/canonical/`
* `data/factors/`
* `data/labels/`
* `data/cache/`
* `metadata/`
* `artifacts/`

`runs/` exists only as local Workflow 2 runtime state. It is ignored by `.gitignore` and is not commit-eligible.

## Files Changed And Staged

Curated commit-eligible paths staged explicitly for commit:

* `.gitignore`
* `PROJECT_STATUS.md`
* `README.md`
* `artifacts/README.md`
* `campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md`
* `campaigns/ALPHA_SYSTEM_V1/GOAL.md`
* `campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
* `campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
* `campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
* `configs/.gitkeep`
* `data/cache/README.md`
* `data/canonical/README.md`
* `data/factors/README.md`
* `data/labels/README.md`
* `data/raw/README.md`
* `handoffs/ASV1-P00.md`
* `metadata/README.md`

No `runs/` path is included in the curated list.

Required files that already existed and were verified but not changed:

* `ACTIVE_CAMPAIGN.md`
* `campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`

## Validation Results

Executor-ran structural validation used only the explicit safe commands from the generated ASV1-P00 spec. Ralph remains the owner of formal validation, review, done-check, verdict, PR, CI, and merge gate.

All commands exited `0`:

* `git status --short`
* `git status -sb`
* `pwd`
* `test -f README.md`
* `test -f PROJECT_STATUS.md`
* `test -f .gitignore`
* `test -f ACTIVE_CAMPAIGN.md`
* `test -f campaigns/ALPHA_SYSTEM_V1/GOAL.md`
* `test -f campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md`
* `test -f campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md`
* `test -f campaigns/ALPHA_SYSTEM_V1/campaign.yaml`
* `test -f campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md`
* `test -f campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md`
* `test -f handoffs/ASV1-P00.md`
* `test -d specs`
* `test -d handoffs`
* `test -d reviews`
* `test -d evals`
* `test -d docs`
* `test -d decisions`
* `test -d configs`
* `test -d data/raw`
* `test -d data/canonical`
* `test -d data/factors`
* `test -d data/labels`
* `test -d data/cache`
* `test -d metadata`
* `test -d artifacts`
* `grep -q "ALPHA_SYSTEM_V1" ACTIVE_CAMPAIGN.md`
* `grep -R "git add ." README.md PROJECT_STATUS.md docs || true`
* `grep -R "git add -A" README.md PROJECT_STATUS.md docs || true`
* `git check-ignore -v data/raw/example.parquet || true`
* `git check-ignore -v data/canonical/example.parquet || true`
* `git check-ignore -v data/factors/example.parquet || true`
* `git check-ignore -v data/labels/example.parquet || true`
* `git check-ignore -v data/cache/example.parquet || true`
* `git check-ignore -v metadata/alpha_system.sqlite || true`
* `git check-ignore -v artifacts/example_large_output.csv || true`
* `git check-ignore -v runs/example_run/state.json || true`
* `find data -type f ! -name README.md ! -name ".gitkeep" -print`
* `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`
* `find artifacts -type f -size +1M -print 2>/dev/null || true`
* `find . -path ./tests/fixtures -prune -o -type f -name "*.parquet" -print`
* `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print`
* `git ls-files runs`

Informational outputs:

* `pwd` returned `/home/yuke_zhang/projects/alpha_system`, satisfying the WSL2 Linux filesystem path policy.
* `git status --short` showed only the scoped modified files and untracked permitted placeholder roots plus `handoffs/ASV1-P00.md`.
* `grep` confirmed the explicit `git add .` and `git add -A` prohibitions in `README.md` and `PROJECT_STATUS.md`.
* `git check-ignore -v` confirmed ignore coverage for representative data, metadata DB, artifact, and run-local paths.
* Artifact audit `find` commands returned no raw/generated data payloads, local DB files, large artifacts, or Parquet files.
* `git ls-files runs` returned empty.

## Artifact Policy Confirmation

Allowed Paths and local-only run artifacts are separated:

* Commit-eligible handoff is `handoffs/ASV1-P00.md`.
* Run-local handoff was written at `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P00/handoff.md` and is local-only.
* `.gitignore` ignores `runs/**`.
* No `runs/` path is staged or commit-eligible for ASV1-P00.
* `git ls-files runs` returned empty.

No raw data, generated canonical data, materialized factor values, materialized label values, local SQLite/DB files, logs, caches, heavy artifacts, model artifacts, credential material, or local environment files were staged or committed.

## Scope Confirmation

Explicit staging only is required. `git add .`, `git add -A`, and force push were not used.

Broker integration, paper trading, live trading, order routing, and production execution are out of scope and were not introduced.

No alpha, profitability, robustness, or tradability claims were introduced.

No hidden failed runs, test weakening, or test gaming was introduced.

Hook, CI, and enforcement-script implementation is deferred to ASV1-P01. Existing harness files and tests were not modified.

## Known Limitations

Ralph still must perform formal validation, handoff validation, Claude Opus 4.8 xhigh review, verdict parsing, semantic done-check, artifact gate, PR/CI/merge gate, and any repair loop. Codex did not create `review.md`, `verdict.json`, a PR, a merge, or a PASS marker.

The repository already contained harness code, tests, docs, reviews, and previous run-local artifacts before this execution. ASV1-P00 did not broaden scope by modifying those implementation surfaces.

## Review Focus

* Confirm ASV1-P00 remains policy/scaffold-only.
* Confirm WSL2 path policy names `~/projects/alpha_system` and forbids `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temporary directories.
* Confirm `.gitignore` protects local-only paths, especially `runs/**`, data payload directories, metadata DB files, artifacts, logs, caches, models, credentials, and env files.
* Confirm placeholder exceptions do not permit real payloads.
* Confirm `campaign.yaml` and `PHASE_PLAN.md` no longer list `runs/**` as commit-eligible for ASV1-P00.
* Confirm no source, tests, `pyproject.toml`, broker, paper, live, order-routing, data payload, DB, heavy artifact, review, verdict, PR, merge, or unsupported alpha/tradability claim was introduced.
