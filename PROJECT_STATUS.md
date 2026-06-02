# Project Status

Project: `alpha_system`

## Current State

- Harness profile: `trading_research`
- Template version: `3.0.0`
- Generated: `2026-05-31T21:48:47+00:00`
- Workflow 1: available
- Workflow 2: minimum viable local provider-wired conductor available for `ALPHA_SYSTEM_V1`
- Auto-merge: policy scaffold only until explicitly wired
- Active campaign: `ALPHA_SYSTEM_V1`
- Current generated phase: `ASV1-P00` - Repo and Harness Bootstrap Policy
- Canonical repo path: `~/projects/alpha_system`
- Required filesystem: WSL2 Linux filesystem

## ASV1-P00 Baseline

ASV1-P00 establishes the repository policy foundation only. It records the WSL2 path policy, explicit-staging-only git discipline, local-only artifact rules, campaign directory layout, and safe placeholder roots.

Forbidden active worktree locations are `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temporary directories.

The phase does not implement source code, data ingestion, factor computation, labels, diagnostics, registry logic, backtesting, hook enforcement, CI workflows, deployment, broker operations, paper trading, live trading, or order routing.

## Non-Negotiable Policy

- Stage explicit paths only; never `git add .` and never `git add -A`.
- Do not force push.
- Do not commit raw data, heavy artifacts, generated local outputs, local SQLite or DB files, caches, logs, model artifacts, local environment files, or credential material.
- Keep `runs/**` local-only. `git ls-files runs` must return empty.
- Do not hide failed runs.
- Do not weaken or game tests.
- Do not introduce alpha, profitability, robustness, or tradability claims without evidence and review.

## Notes

Use this file for concise project-level status that should be visible before reading individual campaign artifacts.

ASV1-P00B fixed the initial `frontier-ci` fresh-runner failure by installing
minimal pytest dependencies and handling the no-tests case safely.

Any hook, CI, or artifact-policy enforcement work not already present in the repository remains outside ASV1-P00 scope and is deferred to ASV1-P01.
