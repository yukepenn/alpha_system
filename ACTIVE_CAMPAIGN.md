# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Workflow: `workflow2`
Run: `not started`
Status: `ready` - contract bundle authored; not yet executed

Current phase: `none` - awaiting first Workflow 2 run
Last completed phase: `none`
Last completed status: `n/a`
Passing phases: `0/31`

Campaign `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is the **first small-but-real,
evidence-gated, cost-aware ES/NQ/RTY futures alpha research pilot** over the
completed Data + Feature/Label + Research Runtime + Agent Factory stack. It drives
those primitives through their sanctioned APIs to exercise one full controlled
research loop — hypothesis → AlphaSpec → StudySpec → Runtime diagnostics →
cost/session/regime/no-lookahead review → TrialLedger/RejectedIdeaLedger →
`REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH`. It produces **research
evidence only**. It does **not** do scaled/autonomous mining, FactorLibrary V1,
Strategy Reference Validation, AlphaBook, strategy/backtest/portfolio products,
paper/live/broker/order work, or any profitability/tradability claim.

This pointer selects `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` as the next Workflow 2
campaign. The predecessor `ALPHA_AGENT_FACTORY_MVP` is complete (26/26,
`COMPLETE_WITH_WARNINGS`,
`campaigns/ALPHA_AGENT_FACTORY_MVP/CLOSEOUT.md`). The two pre-pilot blockers it
named — `FEATURE_LABEL_PARQUET_SINK_V1` and `SESSION_LABEL_GUARD_FIX_V1` — both
landed in `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1` (PR #210), which is this
campaign's substrate.

Ralph updates this pointer through reviewed phase commits so the tracked repo
stays clean after Workflow 2 stops. In `dag_wave` parallel mode this pointer is
**coordinator-owned** and is never written by a phase branch.

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Campaign path: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2`
- Mode: Ralph-driven strict autonomous loop
- Project profile: `trading_research` / `research` / `core_alpha_pilot`
- Phase count: 31 phases (`FUTCORE-P00` … `FUTCORE-P30`)
- Lane policy: Green/Yellow only; **no Red scope**

## Scheduler

- `workflow2.scheduler.mode`: `dag_wave`
- `parallel_execution`: `true`; `max_parallel_phases`: `3`
- `merge_queue`: `serial` (build in parallel, merge one PR at a time)
- `update_active_campaign`: `coordinator_only` (phase branches never write this file)
- Preview: `just frontier-plan ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Mock first: `just frontier-run-parallel-mock ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 3`
- Live parallel: `just frontier-run-parallel ALPHA_FUTURES_CORE_ALPHA_PILOT_V1 3`

## Model Routing

- Strategy / campaign framing / post-run reasoning: ChatGPT (GPT-5.5 Thinking)
- Specs / semantic review / done-check: Claude Opus 4.8 xhigh
- Source map / verifier / mechanical audit: Claude Sonnet 4.6
- Execution / tests / repair / handoffs: Codex GPT-5.5 high
- Orchestration / state machine / DAG scheduler / serial merge queue: Ralph

These are **build-time** model roles. They are distinct from the in-product
agent roster (Research Director, Hypothesis Scout, AlphaSpec Critic, Data
Contract Auditor, Feature Engineer, Label Engineer, No-Lookahead Auditor,
Diagnostics Runner, Statistical Reviewer, Librarian), which the Agent Factory
contracts drive as constrained research workers — not autonomous traders.

## Scheduler Wave Map

```text
Sequential : FUTCORE-P00 -> P01 -> P02 -> P03 -> P04 -> P05 -> P06
Parallel   : [FUTCORE-P07 P08 P09] [P10 P11]
Sequential : FUTCORE-P12 -> P13 -> P14 -> P15
Parallel   : [FUTCORE-P16 P17 P18] [P19 P20]
Sequential : FUTCORE-P21 -> ... -> P30
```

## Boundaries

The pilot consumes — never edits — the runtime/governance/agent_factory/research/
experiments/backtest/data/core primitives. Diagnostics run only through the
Research Runtime tool surface; inputs resolve only through registry tools and
`resolve_dataset_version`; research-scale scans use registry-resolved Parquet
values; every feature has `available_ts`, every label `label_available_ts`. The
only phase permitted to add `src/alpha_system/features/**` or `labels/**` is
`FUTCORE-P15`, and only for minimal, justified primitives via FeatureRequest/
LabelSpec.

Out of scope: scaled/autonomous mining, continuous research runner, FactorLibrary
V1, Strategy Reference Validation, AlphaBook, strategy/backtest/portfolio
products, ML/DL/RL, L1/L2 event-stream, portfolio construction, paper/live/
broker/order, external provider calls, and any raw/canonical/feature/label/value
or local-DB commit. An EvidenceDraft is not a candidate; a candidate is not paper/
live/capital readiness; the human owns risk/capital/live judgment.

## Preflight Gates (encoded in `FUTCORE-P01`)

- `FEATURE_LABEL_PARQUET_SINK_V1` complete; research-scale values via Parquet.
- `SESSION_LABEL_GUARD_FIX_V1` complete; point-in-time session-context features OK.
- Research Runtime real-data smoke status recorded.
- Agent Factory preflight recorded.
- Accepted Databento ES/NQ/RTY DatasetVersion + Parquet FeaturePack/LabelPack
  resolve through registry tools; true forward-looking labels remain blocked.

## Campaign Files

`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/`: `GOAL.md`, `PHASE_PLAN.md`,
`campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md`. There is no
campaign-local `ACTIVE_CAMPAIGN.md`; this root pointer is the only one.

## Acceptance Gates

`bootstrap_and_inputs` · `alpha_spec_batches` · `spec_audit_and_packs` ·
`family_diagnostics` · `consolidation_and_audits` · `evidence_ledger_promotion` ·
`handoff_and_closeout`. Every one of the 31 phases (`FUTCORE-P00` …
`FUTCORE-P30`) belongs to exactly one gate. Final verdict ∈ {`COMPLETE`,
`COMPLETE_WITH_WARNINGS`, `BLOCKED`}.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state. In parallel
mode a wave builds concurrently in isolated worktrees but merges serially; a STOP
halts new phase selection and new merges.

Note: Campaign not started. This contract bundle was authored as a
contract-generation-only change (no alpha research, no diagnostics run, no data
read or committed). Run `just frontier-plan ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
and a parallel mock before the first live parallel run.
