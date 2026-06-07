# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_AGENT_FACTORY_MVP`
Workflow: `workflow2`
Run: `2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP`
Status: `complete` - `COMPLETE_WITH_WARNINGS`

Current phase: `none` - campaign complete
Last completed phase: `AGENT-P25` - Acceptance Audit and Closeout
Last completed status: `PASS_WITH_WARNINGS`
Passing phases: `26/26`

Campaign `ALPHA_AGENT_FACTORY_MVP` is the **controlled AI Alpha Research Team
layer** over the completed Governance + Feature/Label + Research Runtime stack.
It defines, as **contracts only**, the agent roles, permission matrix, tool
contracts, research queue, separation-of-duties enforcement, agent/decision/
handoff records, rejected-idea memory, prompt assets, a runtime tool integration
bridge, and a bounded non-alpha dry-run harness that future AI Alpha Researchers
will be driven by. It does **not** instantiate any autonomous agent, does **not**
start alpha search, does **not** run a continuous research runner, and does
**not** promote any factor or validate any strategy.

This pointer selects `ALPHA_AGENT_FACTORY_MVP` as the next Workflow 2 campaign.
The predecessor `ALPHA_RESEARCH_RUNTIME_MVP` is complete (27/27,
`COMPLETE_WITH_WARNINGS`, closeout
`campaigns/ALPHA_RESEARCH_RUNTIME_MVP/CLOSEOUT.md`); its local-first executable
research loop (`alpha_system.runtime`, with the agent-facing
`RuntimeToolResult` / `RuntimeRunSummary` structured outputs) plus the governed
seed FeaturePack/LabelPack and the real-data runtime smoke
(`real_dataset_version_smoke_ran: true`, from
`POST_RUNTIME_FEATURE_LABEL_STORAGE_AND_SEED_PACKS_V1`) are the substrate this
campaign's agent contracts drive.

Ralph updates this pointer through reviewed phase commits so the tracked repo
stays clean after Workflow 2 stops. In `dag_wave` parallel mode this pointer is
**coordinator-owned** and is never written by a phase branch.

## Campaign Identity

- Campaign ID: `ALPHA_AGENT_FACTORY_MVP`
- Campaign path: `campaigns/ALPHA_AGENT_FACTORY_MVP`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2`
- Mode: Ralph-driven strict autonomous loop
- Project profile: `trading_research` / `research` / `agent_factory`
- Phase count: 26 phases (`AGENT-P00` … `AGENT-P25`)

## Scheduler

- `workflow2.scheduler.mode`: `dag_wave`
- `parallel_execution`: `true`; `max_parallel_phases`: `3`
- `merge_queue`: `serial` (build in parallel, merge one PR at a time)
- `update_active_campaign`: `coordinator_only` (phase branches never write this file in parallel mode)
- Preview: `just frontier-plan ALPHA_AGENT_FACTORY_MVP`
- Mock first: `just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3`
- Live parallel: `just frontier-run-parallel ALPHA_AGENT_FACTORY_MVP 3`

## Model Routing

- Strategy / campaign framing / post-run reasoning: ChatGPT (GPT-5.5 Thinking)
- Specs / semantic review / done-check: Claude Opus 4.8 xhigh
- Source map / verifier / mechanical audit: Claude Sonnet 4.6
- Execution / tests / repair / handoffs: Codex GPT-5.5 high
- Orchestration / state machine / DAG scheduler / serial merge queue: Ralph

These are the **build-time** model roles (who writes, reviews, and merges the
campaign). They are distinct from the Agent Factory **in-product** agent roster
(Research Director, Hypothesis Scout, AlphaSpec Critic, Data Contract Auditor,
Feature Engineer, Label Engineer, No-Lookahead Auditor, Diagnostics Runner,
Statistical Reviewer, Librarian), which this campaign specifies as **contracts
only** and does not instantiate as autonomous agents.

## Boundaries

This campaign builds the **controlled AI research team contract layer** that lets
future agents operate inside durable tool contracts and Workflow 2 gates — to
reduce human interaction **without weakening any gate**. Every deliverable is a
contract (role, permission, tool, queue, memory, dry-run) that **drives** the
existing runtime/governance/registry primitives through their sanctioned APIs;
nothing duplicates or edits them.

Agents call the Research Runtime via the `RuntimeToolResult` / `RuntimeRunSummary`
tool surface and resolve inputs via `resolve_dataset_version`; they never read
raw provider files, never call external providers, never write value stores or
registries directly, never bypass `StudySpec`/`AlphaSpec`, never self-review, and
never self-promote. The human owns risk/capital/live judgment.

Out of scope: autonomous agent instantiation, continuous research runner, broad
alpha search, factor promotion, strategy wrappers/backtest/portfolio as agent
products, Core Alpha Pilot, large-scale value-consuming studies before
`FEATURE_LABEL_PARQUET_SINK_V1`, session-context features before
`SESSION_LABEL_GUARD_FIX_V1`, ML/DL beyond authorized scope, L2/event-stream,
paper/live/broker/order/account scope, external provider calls, and any
raw/canonical/feature/label/runtime/agent value or local-DB commit. Agent
dry-run success is not alpha; an agent-generated AlphaSpec is not implementation
approval; a runtime diagnostic PASS is not factor promotion; an EvidenceDraft is
not a candidate; a ReferenceCandidateHandoff is not Reference validation; no
alpha/tradability/profitability/production claim is permitted.

## Preflight Gates (encoded in `AGENT-P01`)

- A real seed FeaturePack / LabelPack exists locally (Databento ES/NQ/RTY 2024 seed window).
- Research Runtime real-data smoke PASSES (`real_dataset_version_smoke_ran: true`).
- `FEATURE_LABEL_PARQUET_SINK_V1` status is checked; large-scale value-consuming studies are **blocked** until it lands or a human explicitly approves.
- `SESSION_LABEL_GUARD_FIX_V1` status is checked; session-context features (`rth_flag`/`eth_flag`/`session_minute`) are **blocked** until the `session_label` guard false-positive in `runtime/input_resolver.py` is fixed.
- The dataset-registry report-rehydration gap is respected; agents use registry/runtime tools and the accepted-DatasetVersion policy, never a bypass.

## Campaign Files

`campaigns/ALPHA_AGENT_FACTORY_MVP/`: `GOAL.md`, `PHASE_PLAN.md`,
`campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md`. There is no
campaign-local `ACTIVE_CAMPAIGN.md`; this root pointer is the only one.

## Acceptance Gates

`bootstrap_and_entry` · `core_contracts` · `agent_roles` ·
`enforcement_and_records` · `assets_and_bridge` · `dry_run_and_closeout`. Every
one of the 26 phases (`AGENT-P00` … `AGENT-P25`) belongs to exactly one gate.
Final verdict ∈ {`COMPLETE`, `COMPLETE_WITH_WARNINGS`, `BLOCKED`}.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state rather than
regenerating completed work. In parallel mode a wave builds concurrently in
isolated worktrees but merges serially; a STOP halts new phase selection and new
merges.

Note: Campaign not started. This contract bundle was authored as a
contract-generation-only patch (no agent code, no autonomous agent, no
diagnostics run, no data read or committed). Run
`just frontier-plan ALPHA_AGENT_FACTORY_MVP` and a parallel mock before the first
live parallel run.
