# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_RESEARCH_RUNTIME_MVP`
Workflow: `workflow2`
Run: `not_started`
Status: `not_started`

Current phase: `RT-P00` - Research Runtime Campaign Bootstrap
Last completed phase: `none`
Last completed status: `none`
Passing phases: `0/27`

This pointer selects `ALPHA_RESEARCH_RUNTIME_MVP` — the **executable research
loop layer** between the Feature/Label substrate and the future Agent Factory —
as the next Workflow 2 campaign. The predecessor
`ALPHA_FEATURE_LABEL_FOUNDATION_V1` is complete (32/32, `COMPLETE_WITH_WARNINGS`,
closeout `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md`); its
registered, point-in-time-safe FeatureStore/LabelStore substrate is the input
this campaign's runtime consumes.

Ralph updates this pointer through reviewed phase commits so the tracked repo stays clean after Workflow 2 stops. In `dag_wave` parallel mode this pointer is **coordinator-owned** and is never written by a phase branch.

## Campaign Identity

- Campaign ID: `ALPHA_RESEARCH_RUNTIME_MVP`
- Campaign path: `campaigns/ALPHA_RESEARCH_RUNTIME_MVP`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2`
- Mode: Ralph-driven strict autonomous loop
- Project profile: `trading_research` / `research` / `research_runtime`
- Phase count: 27 phases (`RT-P00` … `RT-P26`)

## Scheduler

- `workflow2.scheduler.mode`: `dag_wave`
- `parallel_execution`: `true`; `max_parallel_phases`: `3`
- `merge_queue`: `serial` (build in parallel, merge one PR at a time)
- `update_active_campaign`: `coordinator_only` (phase branches never write this file in parallel mode)
- Preview: `just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP`
- Mock first: `just frontier-run-parallel-mock ALPHA_RESEARCH_RUNTIME_MVP 3`
- Live parallel: `just frontier-run-parallel ALPHA_RESEARCH_RUNTIME_MVP 3`

## Model Routing

- Strategy / campaign framing / post-run reasoning: ChatGPT (GPT-5.5 Thinking)
- Specs / semantic review / done-check: Claude Opus 4.8 xhigh
- Source map / verifier / mechanical audit: Claude Sonnet 4.6
- Execution / tests / repair / handoffs: Codex GPT-5.5 high
- Orchestration / state machine / DAG scheduler / serial merge queue: Ralph

## Boundaries

This campaign builds the **local deterministic runtime** that turns an approved
`AlphaSpec` + `StudySpec` into reproducible diagnostics, cost stress, bounded
probes, EvidenceDraft inputs, rejection reasons, and a ReferenceCandidateHandoff
— by **orchestrating existing primitives** (`research.ic/buckets/regimes`,
`backtest.costs/slippage`, `experiments.limits/overfit_controls`,
`governance.study_input_pack/evidence_bundle`), never re-implementing them.

Consume **accepted DatasetVersions** only (`resolve_dataset_version`) plus the
registered FeatureStore/LabelStore; never read raw provider files. Databento is
the primary deep-history research source; IBKR is broker-source recent
validation only. Feature inputs carry `available_ts`; label inputs carry
`label_available_ts`.

Out of scope: broad alpha search, factor promotion, strategy wrappers as
research products, strategy/backtest/portfolio optimization, paper/live/broker
trading, order routing, external provider calls, data pulls,
raw/canonical/feature/label/runtime value commits, heavy artifact or local-DB
commits, and any alpha/tradability/profitability/production claim. A diagnostic
PASS is not alpha validation; a signal probe is not a strategy candidate; a
bounded grid is not promotion; an EvidenceDraft is not a candidate; a
ReferenceCandidateHandoff is not Reference validation; the fast path is not
Reference truth.

## Campaign Files

`campaigns/ALPHA_RESEARCH_RUNTIME_MVP/`: `GOAL.md`, `PHASE_PLAN.md`,
`campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md`. There is no
campaign-local `ACTIVE_CAMPAIGN.md`; this root pointer is the only one.

## Acceptance Gates

`campaign_bootstrap` · `runtime_contracts` · `diagnostics_runtime` ·
`runtime_integration` · `tests_tools_docs` · `workflow_and_closeout`. Every one
of the 27 phases (`RT-P00` … `RT-P26`) belongs to exactly one gate. Final
verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`}.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state rather than
regenerating completed work. In parallel mode a wave builds concurrently in
isolated worktrees but merges serially; a STOP halts new phase selection and new
merges.

Note: Campaign not started. This contract bundle was authored as a
contract-generation-only patch (no runtime code, no diagnostics run, no data
read or committed). Run `just frontier-plan ALPHA_RESEARCH_RUNTIME_MVP` and a
parallel mock before the first live parallel run.
