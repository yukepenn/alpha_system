# Project Status

Project: `alpha_system`

## Current State

- Harness profile: `trading_research`
- Template version: `3.0.0`
- Generated: `2026-05-31T21:48:47+00:00`
- Workflow 1: available
- Workflow 2: provider-wired conductor available; currently paused after
  `ALPHA_AGENT_FACTORY_MVP` closeout
- Auto-merge: enabled through the protected-branch PR path when `FRONTIER_ALLOW_AUTOMERGE=1`
- Active campaign pointer: `ALPHA_AGENT_FACTORY_MVP` complete (`26/26`,
  `COMPLETE_WITH_WARNINGS`, current phase `none`)
- Current phase pointer: `ACTIVE_CAMPAIGN.md`
- Latest local run summary: `runs/<run_id>/RUN_SUMMARY.md`
- Canonical repo path: `~/projects/alpha_system`
- Required filesystem: WSL2 Linux filesystem

Post-closeout status:

- Completed baselines: `ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`,
  `ALPHA_RESEARCH_GOVERNANCE_MVP`, `ALPHA_DATA_FOUNDATION_V1`,
  `ALPHA_FEATURE_LABEL_FOUNDATION_V1`, `ALPHA_RESEARCH_RUNTIME_MVP`,
  `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`,
  `ALPHA_AGENT_FACTORY_MVP`, and `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1`.
- Latest completed campaign (Workflow 1): `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1`
  (**PASS**) — landed both pre-pilot data-access blockers:
  `FEATURE_LABEL_PARQUET_SINK_V1` (research-scale Parquet value sink/reader +
  registry pointer metadata; JSONL preserved as audit/small tier) and
  `SESSION_LABEL_GUARD_FIX_V1` (role-aware no-lookahead guard;
  `rth_flag`/`eth_flag`/`session_minute` unblocked as declared `SESSION_METADATA`).
  Real local Parquet + session-context smoke PASS; Agent Factory preflight
  PREFLIGHT_PASS on all four gates; `verify.py --all` green; artifact audit clean.
  Next (separately authorized): `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.
- Prior completed campaign: `ALPHA_AGENT_FACTORY_MVP`
  (`COMPLETE_WITH_WARNINGS`, `AGENT-P00` through `AGENT-P25`, `26/26` passing;
  the controlled AI Alpha Research Team contract layer — contracts only, no
  autonomous agent instantiated; live run `2026-06-06T193514Z`, PRs #182–#208).
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
    `handoffs/ALPHA_DATA_FOUNDATION_V1/ADF1_DATABENTO_ES_NQ_RTY_OHLCV_BBO_DEEP_HISTORY.md`.
- All raw/canonical data, registries, and reports remain local-only under
  `ALPHA_DATA_ROOT`; nothing is committed. Loading any DatasetVersion implies no
  alpha, tradability, profitability, paper/live, broker, or production readiness.
- Workflow 2 is paused; no phase is currently selected.
- True next intended campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` (a separate,
  separately authorized campaign that may consume the Agent Factory contract
  layer; its existence is not an alpha/tradability claim).

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
just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1                 # preview DAG waves (read-only)
just frontier-run ALPHA_FEATURE_LABEL_FOUNDATION_V1                  # start/continue
just frontier-next ALPHA_FEATURE_LABEL_FOUNDATION_V1 <phase_count>   # step N phases
just frontier-run-parallel ALPHA_FEATURE_LABEL_FOUNDATION_V1 <n>     # dag_wave parallel build, serial merge
```

These commands create the phase PR, wait for required checks, run the merge gate, and use the normal protected-branch merge path with auto-merge fallback when needed. They do not use `--admin`. `frontier-run-parallel` builds a conflict-free, parallel-safe wave concurrently and still merges one PR at a time.

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
