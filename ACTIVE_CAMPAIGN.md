# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
Workflow: `workflow2`
Status: `authored-pending-run` — small blocker-removal campaign (5 phases,
RLPC-P00…P04) inserted while `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
is deliberately STOPPED at `FUTSUB-P19` (2026-06-11T01:45Z, mid full-window
cost_adjusted pass, ~134/216 cells durably checkpointed, all values/registry
rows/worktree preserved).

## Why

FUTSUB-P19-class workloads run the reference label engine single-threaded
(~3h full-window). LCFP-P08 proved the V1 fast pack loses for
`cost_adjusted`/`fixed_extended`/`close_out` (best 0.72x/0.55x/0.40x) — the
per-unit engine, not the worker pool, was the slow part. This campaign reuses
the existing LCFP-P06 spawn worker pool with the UNCHANGED reference engine
inside it: N workers compute disjoint units; ALL keystone registry writes stay
serial in the parent. Implements `docs/STRUCTURAL_BACKLOG.md` §6 option 1
(trigger met). Gates: exact serial==parallel equivalence (BLOCKER, no
tolerances), interruption-resume, single-writer audit, bounded real benchmark
workers 1/2/4/8 with release at >=3.0x @ 8 workers or honest NOT_RELEASED.

## Campaign Identity

- Campaign ID: `REFERENCE_LABEL_PARALLEL_COMPUTE_V1`
- Phase count: 5 (`RLPC-P00` … `RLPC-P04`), serial chain, serial merge queue
- Lane policy: P00 GREEN; P01–P04 YELLOW (fresh Claude review); no Red scope
- Contract bundle: `campaigns/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/{GOAL,PHASE_PLAN,campaign.yaml,ACCEPTANCE,RISK_REGISTER,RUNBOOK}.md`

## Paused campaign (resumes after this one)

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`, run
`2026-06-07T235209Z_...`, 19/34 merged, STOP present. After RLPC-P04 merges,
the coordinator repoints this file back to FUTSUB and resumes P19 under the
amended ENGINE POLICY per
`handoffs/REFERENCE_LABEL_PARALLEL_COMPUTE_V1/FUTSUB_RESUME_ON_PARALLEL_REFERENCE.md`.
Then: P20 (path labels, V1 fast `--engine v1 --workers 8`, 10.2x) → P21–P26
minimum substrate → Discovery Rigor Floor → CORE_PILOT_RERUN_V1 kill-shot.

## Boundaries

In scope: scaleout-driver/CLI worker orchestration for `--engine reference`
label packs, determinism/resume/single-writer gates, bounded real benchmark,
FUTSUB contract amendment + resume handoff, backlog §6 closeout. Out of
scope: ANY edit to `labels/engine.py`, `labels/families/**`, `roll_guard.py`,
`version.py`; cost-kernel vectorization (backlog §6 option 2); v1 fast-path
changes; full-window runs; new alpha ideation; paper/live/broker; committing
values/SQLite/runs; alpha/profitability/tradability claims.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
every stage transition. For live phase status, trust
`python tools/frontier/status_doctor.py` / `runs/<run_id>/state.json`, never
this file. Phase branches never write this pointer; the coordinator owns it.
