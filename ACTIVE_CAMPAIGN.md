# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Workflow: `workflow2`
Run: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` - the
original live run, resumed (not restarted) after the
`REFERENCE_LABEL_PARALLEL_COMPUTE_V1` insertion campaign closed COMPLETE
(5/5, PRs #346-#350).
Status: `executing-after-resume`. Current phase: `FUTSUB-P19` (cost-adjusted
labels, reference engine, resuming from ~134/216 durable full-window
checkpoint cells; explicit opt-in `--workers 8` per the documented coordinator
deviation in the campaign contract - measured 2.14x, determinism PASS,
NOT_RELEASED as default policy). Next: `FUTSUB-P20` (path labels, V1 fast
`--engine v1 --workers 8`, 10.2x), then P21-P26 minimum substrate.
Completed phases: `19/34`.

## Post-RLPC Label Engine + Worker Policy

Per-family engine policy (LCFP-P08, unchanged): path + fixed_base on V1 fast
(8 workers); fixed_extended / close_out / cost_adjusted on the reference
engine. Reference-engine unit-parallel workers exist platform-wide
(`--workers N`, parity-exact, single-writer-audited; RLPC-P01/P02) but the
3.0x release gate measured 2.14x (serial-registration/hydration ceiling), so
**workers=1 remains the reference default**; the P19 resume uses a documented
explicit opt-in only. Escalations recorded in `docs/STRUCTURAL_BACKLOG.md` §6.

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase count: 34 phases (`FUTSUB-P00` ... `FUTSUB-P33`); dag_wave parallel-3,
  serial merge queue, materialization phases serialized by
  `materialization_registry` resource_class
- Lane policy: Green/Yellow only; no Red scope expected
- Contract bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/{GOAL,PHASE_PLAN,campaign.yaml,ACCEPTANCE,RISK_REGISTER,RUNBOOK}.md`

## Boundaries

In scope: full accepted-window substrate materialization (labels per the
per-family engine policy), roll-splice + maintenance-crossing guards, registry
integration + resolver smoke, coverage/quality matrices, N_eff / walk-forward
wiring, and the Core Pilot INCONCLUSIVE StudySpec re-run on real materialized
inputs. Out of scope: new alpha ideation, platform rewrite,
FactorLibrary/AlphaBook/Strategy Reference, paper/live/broker, deleting or
weakening the reference label engine, mixing producers in one value series,
committing values/SQLite/runs, and any alpha/profitability/tradability claim.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
every stage transition. Resume continues from recorded run state. For live
phase status, trust `python tools/frontier/status_doctor.py` /
`runs/<run_id>/state.json`, never this file. Phase branches never write this
pointer; the coordinator owns it.
