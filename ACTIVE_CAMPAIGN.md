# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1`
Workflow: `workflow2`
Run: `none`
Status: `not_started`

Current phase: `FLF-P00` - Feature/Label Campaign Bootstrap
Last completed phase: `none`
Last completed status: `none`
Passing phases: `0/32`

Ralph updates this pointer through reviewed phase commits so the tracked repo stays clean after Workflow 2 stops. In `dag_wave` parallel mode this pointer is **coordinator-owned** and is never written by a phase branch.

## Campaign Identity

- Campaign ID: `ALPHA_FEATURE_LABEL_FOUNDATION_V1`
- Campaign path: `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2`
- Mode: Ralph-driven strict autonomous loop
- Project profile: `trading_research` / `research` / `feature_label_foundation`

## Scheduler

- `workflow2.scheduler.mode`: `dag_wave`
- `parallel_execution`: `true`; `max_parallel_phases`: `3`
- `merge_queue`: `serial` (build in parallel, merge one PR at a time)
- `update_active_campaign`: `coordinator_only` (phase branches never write this file in parallel mode)
- Preview: `just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1`
- Mock first: `just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3`
- Live parallel: `just frontier-run-parallel ALPHA_FEATURE_LABEL_FOUNDATION_V1 3`

## Model Routing

- Strategy / campaign framing / post-run reasoning: ChatGPT (GPT-5.5 Thinking)
- Specs / semantic review / done-check: Claude Opus 4.8 xhigh
- Source map / verifier / mechanical audit: Claude Sonnet 4.6
- Execution / tests / repair / handoffs: Codex GPT-5.5 high
- Orchestration / state machine / DAG scheduler / serial merge queue: Ralph

## Boundaries

Consume **accepted DatasetVersions** only (`resolve_dataset_version`); never read raw provider files. Databento is the primary deep-history research source; IBKR is broker-source recent validation only. Every feature carries `available_ts`; every label carries `label_available_ts`. Governance objects (`FeatureRequest`, `LabelSpec`, `StudySpec`, `AlphaSpec`) are consumed, not duplicated.

Out of scope: broker/live/paper trading, order routing, account trading, external provider calls, data pulls, raw/canonical/feature/label value commits, heavy artifact commits, local DB commits, alpha search, strategy/backtest/portfolio work, and alpha/tradability/profitability claims without evidence.

## Campaign Files

`campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/`: `GOAL.md`, `PHASE_PLAN.md`, `campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md`. There is no campaign-local `ACTIVE_CAMPAIGN.md`; this root pointer is the only one.

## Acceptance Gates

`campaign_bootstrap` · `canonical_inputs` · `feature_contracts` · `feature_families` · `feature_materialization` · `label_contracts` · `label_materialization` · `diagnostics_and_tests` · `workflow_and_closeout`. Every one of the 32 phases (`FLF-P00` … `FLF-P31`) belongs to exactly one gate. Final verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`}.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before phase selection, execution, checks, review, PR, CI, merge gate, merge, done-check, and next-phase. Resume continues from recorded run state rather than regenerating completed work. In parallel mode a wave builds concurrently in isolated worktrees but merges serially; a STOP halts new phase selection and new merges.

Note: Campaign contract generated; not yet started. This file is the projected `not_started` pointer.
