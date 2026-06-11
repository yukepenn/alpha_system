# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/DISCOVERY_RIGOR_FLOOR_V1`
Workflow: `workflow2`
Status: `launching`. The rigor-floor insertion campaign (RIGOR-P00..P07)
running at the FUTSUB P27/P28 boundary per compass v4.3 Stage B: statistical
multiplicity controls, sealed holdout, executable negative controls,
surrogate-FDR calibration, reason_code taxonomy, and kill-shot readiness
artifacts must exist BEFORE the FUTSUB-P28 Core Pilot re-run computes any
Track-A metric.

## Gated predecessor

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` run
`2026-06-07T235209Z_...` is deliberately boundary-STOPPED at 28/34
(P00–P27 merged through PR #371 + #367; P28 kill-shot BLOCKED pre-execution
by the Stage-B gate STOP — reset to PENDING at resume). Its run dir,
registries, values, and worktrees are DATA for this campaign — untouched.
FUTSUB resumes only after RIGOR-P07 merges and the
`handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` steps complete
(Track-B pre-registration BEFORE any Track-A metric; surrogate zero-pass
check; KILL_SHOT_READINESS verification).

## Campaign Identity

- Campaign ID: `DISCOVERY_RIGOR_FLOOR_V1`
- Phase count: 8 phases (`RIGOR-P00` ... `RIGOR-P07`); dag_wave parallel-2;
  RIGOR-P01/P02/P03 serialized (all touch promotion_gate.py)
- Lane policy: Green/Yellow only; no Red scope
- Contract bundle: `campaigns/DISCOVERY_RIGOR_FLOOR_V1/{GOAL,PHASE_PLAN,campaign.yaml,ACCEPTANCE,RISK_REGISTER,RUNBOOK}.md`

## Boundaries

In scope: reason_code taxonomy, VariantLedger + family budgets, sealed
holdout + access log, executable negative controls + planted-fake-alpha e2e
canary, surrogate-FDR calibration machinery, evidence-accrual requeue scan,
kill-shot readiness + Track-B preregistration template. Out of scope:
historical Core Pilot evidence mutation (forbidden_paths everywhere;
annotations are NEW files only), Mining-V2 mechanisms (duplicate-exposure
registry expansion, FactorLibrary), FUTSUB run-state changes, any
alpha/profitability/tradability claim.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
every stage transition. Resume continues from recorded run state. For live
phase status, trust `python tools/frontier/status_doctor.py` /
`runs/<run_id>/state.json`, never this file. Phase branches never write this
pointer; the coordinator owns it.
