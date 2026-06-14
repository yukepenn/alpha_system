# Project Status

> **HISTORICAL — not live status.** This file lags the running campaign. For the
> authoritative campaign/phase, run `just status-doctor` (or read
> `runs/<run_id>/state.json`). Entry point for agents: `CRITICAL.md`.

Project: `alpha_system`

## Current State

- Harness profile: `trading_research`
- Template version: `3.0.0`
- Generated: `2026-05-31T21:48:47+00:00`
- Workflow 1: available
- Workflow 2: provider-wired conductor available; **no live run** — paused after
  `DIFFERENTIATED_KILLSHOT_V1` closeout (post-DK factory adjudication)
- Auto-merge: enabled through the protected-branch PR path when `FRONTIER_ALLOW_AUTOMERGE=1`
- Active campaign pointer: `DIFFERENTIATED_KILLSHOT_V1` COMPLETE (`6/6`,
  `PASS_WITH_WARNINGS`, current phase `none`, **0 survivors** — see post-DK note below)
- Current phase pointer: `ACTIVE_CAMPAIGN.md`
- Latest local run summary: `runs/<run_id>/RUN_SUMMARY.md`
- Canonical repo path: `~/projects/alpha_system`
- Required filesystem: WSL2 Linux filesystem

### Post-DK research state (0 survivors — second clean kill-shot)

`DIFFERENTIATED_KILLSHOT_V1` is COMPLETE 6/6 with **0 survivors**:

- **Track A** (calendar/flow conditioning factors as main-effect context):
  WELL-POWERED CLEAN NULL — 4 mechanisms `ZERO_PASS_MET`, all REJECT.
- **Track B** (EXPLORATORY `context != trigger` conditional probe):
  SUBSTRATE-GAP, UNTESTED — ran on a single-class (degenerate) 120m
  `target_before_stop` slice; not a null, a closable DATA_GAP.
- `roll_week`: honest DATA_GAP (`in_roll_window_flag` all-null).

Survivor gate = **0**: no promotion; no downstream factory module (broad Mining V2,
FactorLibrary as survivor memory, AlphaBook, Strategy Sandbox, PA grammar), no
universe expansion, and no paid data are authorized — all trigger-gated behind the
survivor gate. Next: post-DK factory production-line adjudication → a narrow Track B
substrate gap-closure (same pre-registered SetupSpec, existing `ES_2020_120m`
barrier-resolving slice, no new mechanisms/sweep/promotion) → a fresh narrow shot from
a ranked MechanismCard queue. ES/NQ/RTY existing data only.

### Completed campaigns (chronological; the deep history above/below is not the live ledger)

`ALPHA_SYSTEM_V1`, `ASV1_RELEASE_HYGIENE`, `ALPHA_RESEARCH_GOVERNANCE_MVP`,
`ALPHA_DATA_FOUNDATION_V1`, `ALPHA_FEATURE_LABEL_FOUNDATION_V1`,
`ALPHA_RESEARCH_RUNTIME_MVP`, `POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`,
`ALPHA_AGENT_FACTORY_MVP`, `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1`,
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` (INCONCLUSIVE substrate-coverage),
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` (FUTSUB — 0 survivors),
`DISCOVERY_RIGOR_FLOOR_V1` (rigor floor 8/8), `SHIP_REFIT_V1`,
`STRATEGY_SHAPED_RESEARCH_LANE_V0` (SSRL 5/5), and `DIFFERENTIATED_KILLSHOT_V1`
(DK 6/6, 0 survivors).

- All raw/canonical data, registries, and reports remain local-only under
  `ALPHA_DATA_ROOT`; nothing is committed. Loading any DatasetVersion implies no
  alpha, tradability, profitability, paper/live, broker, or production readiness.

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
