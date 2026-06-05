# Git And Artifact Discipline

## Required Policy

This repository uses explicit staging only. Stage each curated file by path and review the staged set before committing.

Forbidden staging examples:

```text
git add .
git add -A
```

Force push is forbidden for this campaign. PR creation, CI waiting, merge gates, and merges are Ralph-owned gate actions.

## Commit-Eligible Vs Local-Only

Commit-eligible files are limited by the active phase spec and `frontier.yaml`. Typical commit-eligible categories are harness control files, docs, source files when authorized, tests when authorized, campaign specs, commit-eligible handoffs, reviews, decisions, curated configs, and tiny documented fixtures when explicitly allowed.

Local-only files must never be staged or committed:

```text
runs/**
data/raw/**
data/canonical/**
data/factors/**
data/labels/**
data/cache/**
metadata/*.sqlite
metadata/*.sqlite3
metadata/*.db
metadata/*.db-journal
metadata/*.wal
artifacts/**
**/*.parquet
**/*.arrow
**/*.feather
**/*.log
```

For ASV1-P01 specifically, the commit-eligible phase handoff is:

```text
handoffs/ALPHA_SYSTEM_V1/ASV1-P01.md
```

The run-local handoff remains local-only:

```text
runs/<run_id>/phases/ASV1-P01/handoff.md
```

## Run Artifacts

`runs/**` is local-only runtime state. It may contain run goals, state, event ledgers, costs, progress, STOP files, specs, executor prompts, executor notes, checks, handoffs, reviews, verdicts, done-checks, PR bodies, CI status, merge-gate results, and repair attempts. None of those files are commit-eligible.

`git ls-files runs` must return empty for this campaign baseline.

## Pre-Commit Review

Before commit or merge-gate evaluation, run:

```bash
git status --short
git diff --cached --name-only
git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print 2>/dev/null || true
find . -path ./tests/fixtures -prune -o -type f -name "*.parquet" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

The staged file list must contain no `runs/` path and no forbidden local-only artifact path.

## Hook Strategy

Git hook wrappers live under `.githooks/`. Hook implementations live under `tools/hooks/`.

Current local guards include:

```text
tools/hooks/artifact_guard.py
tools/hooks/bulk_add_guard.py
tools/hooks/secret_scan.py
tools/hooks/test_tamper_guard.py
tools/hooks/forbidden_pattern_guard.py
tools/hooks/boundary_guard.py
```

`tools/hooks/artifact_guard.py` blocks `runs/**`, local data directories, metadata DBs, artifacts, logs, caches, model binaries, and other heavy or generated files. `tools/hooks/bulk_add_guard.py` guards against suspiciously large staged additions. `tools/hooks/test_tamper_guard.py` protects against unauthorized test weakening.

The executable shell wrappers under `.githooks/` do not currently expose a separate `--check` mode. Ralph and reviewers should treat that as a documented enforcement gap until a later phase adds a formal dry-run hook entrypoint. The Python guard modules can still be invoked directly with explicit paths or by the pre-commit wrapper.

## Active Path Policy

The active repo and active worktrees must run under the WSL2 Linux filesystem at:

```text
~/projects/alpha_system
```

Forbidden active worktree locations include `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temporary directories.

## Scope Guard

Do not stage or commit broker, paper trading, live trading, order-routing, production execution, cloud/server/paid database dependencies, unsupported alpha claims, profitability claims, robustness claims, tradability claims, raw data, heavy artifacts, SQLite/DB files, generated Parquet/Arrow/Feather files, logs, or caches.
