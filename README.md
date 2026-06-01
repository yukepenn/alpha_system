# alpha_system

`alpha_system` is a research-only, local-first Alpha Research Platform foundation for offline hypothesis development, data checks, and reviewable research workflows.

The active campaign is [ALPHA_SYSTEM_V1](campaigns/ALPHA_SYSTEM_V1/GOAL.md). The current campaign pointer lives in [ACTIVE_CAMPAIGN.md](ACTIVE_CAMPAIGN.md).

## Repository Policy

- Canonical repo path: `~/projects/alpha_system`.
- Required filesystem: WSL2 Linux filesystem.
- Forbidden active worktree locations: `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, and temporary directories.
- Git staging is explicit-path-only. Do not use `git add .`, do not use `git add -A`, and do not force push.
- Raw data, canonical data, factor values, label values, heavy generated artifacts, caches, logs, temporary outputs, and local SQLite or database files must not be committed.
- Generated local-only contents under `data/`, `metadata/`, and `artifacts/` must stay out of git except placeholder `README.md` or `.gitkeep` files.

## Scope Boundaries

This repository is not a broker, paper trading, live trading, order routing, or production execution system. Those capabilities are out of scope for this campaign and must not be introduced by bootstrap policy work.

Research notes, examples, reports, and handoffs must not make alpha, profitability, robustness, or tradability claims without evidence and review context.

Failed runs must remain visible. Tests must not be weakened, skipped, or gamed to create false completion.

## Campaign Files

- [Campaign goal](campaigns/ALPHA_SYSTEM_V1/GOAL.md)
- [Acceptance criteria](campaigns/ALPHA_SYSTEM_V1/ACCEPTANCE.md)
- [Phase plan](campaigns/ALPHA_SYSTEM_V1/PHASE_PLAN.md)
- [Risk register](campaigns/ALPHA_SYSTEM_V1/RISK_REGISTER.md)
- [Runbook](campaigns/ALPHA_SYSTEM_V1/RUNBOOK.md)
- [Campaign config](campaigns/ALPHA_SYSTEM_V1/campaign.yaml)

Harness control files and hook enforcement are outside ASV1-P00 implementation scope. If present, they are treated as existing repository context and are not modified by this phase.
