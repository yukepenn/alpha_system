# Project Status

Project: `alpha_system`

## Current State

- Harness profile: `trading_research`
- Template version: `3.0.0`
- Generated: `2026-05-31T21:48:47+00:00`
- Workflow 1: available
- Workflow 2: provider-wired conductor available; currently paused after
  `ALPHA_DATA_FOUNDATION_V1` closeout
- Auto-merge: enabled through the protected-branch PR path when `FRONTIER_ALLOW_AUTOMERGE=1`
- Active campaign pointer: `ALPHA_DATA_FOUNDATION_V1` complete (`25/25`,
  current phase `none`)
- Current phase pointer: `ACTIVE_CAMPAIGN.md`
- Latest local run summary: `runs/<run_id>/RUN_SUMMARY.md`
- Canonical repo path: `~/projects/alpha_system`
- Required filesystem: WSL2 Linux filesystem

Post-closeout status:

- Completed baselines: `ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`,
  `ALPHA_RESEARCH_GOVERNANCE_MVP`, and `ALPHA_DATA_FOUNDATION_V1`.
- Latest completed campaign: `ALPHA_DATA_FOUNDATION_V1`
  (`COMPLETE_WITH_WARNINGS`, `DATA-P00` through `DATA-P24`, `25/25` passing).
- Post-closeout data work completed across two providers with distinct roles:
  - IBKR (read-only broker-validation source, ~2 years of available depth):
    Task 1A connector/smoke (PR #96) and Task 1B resumable backfill/materialize
    with the first real local-only DatasetVersion
    `dsv_ibkr_es_nq_rty_eth_20260603_v1` (PR #97).
  - Databento (primary deep-history research source): Phase B complete
    (PR #107) — full GLBX.MDP3 ES/NQ/RTY continuous OHLCV-1m + BBO-1m history
    (2018-01-01 → 2026-06-01) pulled, canonicalized (sparse provider truth plus
    a derived dense research grid), quality/coverage-gated, and registered as
    27 local-only DatasetVersions across development/validation/locked-test
    partitions, kept separate from the IBKR DatasetVersions. See
    `handoffs/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`.
- All raw/canonical data, registries, and reports remain local-only under
  `ALPHA_DATA_ROOT`; nothing is committed. Loading any DatasetVersion implies no
  alpha, tradability, profitability, paper/live, broker, or production readiness.
- Workflow 2 is paused; no phase is currently selected.
- True next intended campaign: `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.

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
# Only after an approved campaign contract exists.
just frontier-run-next ALPHA_FEATURE_LABEL_FOUNDATION_V1
just frontier-run-next-x ALPHA_FEATURE_LABEL_FOUNDATION_V1 <phase_count>
```

These commands create the phase PR, wait for required checks, run merge gate, and use the normal protected-branch merge path with auto-merge fallback when needed. They do not use `--admin`.

## Documentation Pointers

- Current completed campaign contract: `campaigns/ALPHA_DATA_FOUNDATION_V1/`
- Prior completed governance contract:
  `campaigns/ALPHA_RESEARCH_GOVERNANCE_MVP/`
- Current phase pointer: `ACTIVE_CAMPAIGN.md`
- Phase handoffs: `handoffs/`
- Reviews and verdicts: `reviews/`
- Architecture and domain docs: `docs/`
- Run-local audit trail: `runs/<run_id>/`

Use this file for concise project-level orientation before reading individual campaign artifacts.
