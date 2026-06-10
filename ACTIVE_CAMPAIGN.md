# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Workflow: `workflow2`
Run: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` - the
original stopped live run, resumed (not restarted) after
`LABEL_COMPUTE_FAST_PATH_V1` closed.
Status: `executing-after-resume` - FUTSUB resumes under the LCFP-P08 accepted
**per-family label engine policy** (see below). The coordinator applied the
reintegration amendments from
`handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_REINTEGRATION_ON_FAST_LABELS.md`
to the campaign contract; Ralph owns staging, commit, review routing, PR/CI/
merge gates, and run summaries.

Current phase: `FUTSUB-P19` - Cost-Adjusted LabelPack Scaleout, resuming on the
**reference engine** from its ~60% durable checkpoint (181 completed units
preserved; checkpoint + registry truth skip completed valid units) per the
accepted per-family policy.
Next phase: `FUTSUB-P20` - Path LabelPack Scaleout on the **V1 fast label
path** (`--engine v1 --workers 8`, LCFP-P08 measured 10.2x).
Completed phases: `19/34` passing (P00-P18 merged; PASS=1,
PASS_WITH_WARNINGS=18).

## Post-LCFP Label Engine Policy (accepted)

`LABEL_COMPUTE_FAST_PATH_V1` closed `COMPLETE` (10/10, run
`2026-06-10T102615Z`, closeout at
`research/label_compute_fast_path_v1/closeout/CLOSEOUT.md`). Its P08 benchmark
selected the engine **per family**, not fast everywhere:

| FUTSUB phase | Family | Engine | Workers | Speedup |
| --- | --- | --- | ---: | ---: |
| P16 | `fixed_base` | V1 fast (future appends/recomputes only) | 8 | 1.03x |
| P17 | `fixed_extended` | reference | n/a | 0.55x |
| P18 | `close_out` | reference | n/a | 0.40x |
| P19 | `cost_adjusted` | reference | n/a | 0.72x |
| P20 | `path` | V1 fast | 8 | 10.23x |

Thread controls for fast runs: `POLARS_MAX_THREADS=2`, `OMP_NUM_THREADS=2`,
`RAYON_NUM_THREADS=2`, `NUMBA_NUM_THREADS=2`. The per-row reference label
engine remains the correctness oracle forever; existing valid
reference-produced labels are preserved (preserve-don't-delete), and
parity-gated engines emit identical governed `label_version_id` identities.

**Coordinator deviation from the reintegration handoff (2026-06-10):**
P16/P17/P18 are NOT reset - they remain merged PASS with valid, full-window,
parity-equivalent reference-produced values. Under the accepted policy
P17/P18 stay on reference anyway, and P16's v1 selection (1.03x) applies to
future appends/recomputes only. Only P19 (resume reference from checkpoint)
and P20 (fresh on V1 fast) are reset/resumed. Rationale recorded in the
handoff's "Coordinator deviation note (2026-06-10)" subsection
(Compass v3 minimum-substrate + preserve-valid-work).

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Campaign path: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Repo: `alpha_system` / `~/projects/alpha_system`
- Workflow: `workflow2` (Ralph strict autonomous loop; `dag_wave`;
  materialization phases serialized by the shared `materialization_registry`
  resource_class; serial merge queue)
- Project profile: `trading_research` / `research` / `research_substrate_scaleout`
- Phase count: 34 phases (`FUTSUB-P00` ... `FUTSUB-P33`)
- Lane policy: Green/Yellow only; **no Red scope expected**

## Contract Bundle

- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/PHASE_PLAN.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACCEPTANCE.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RISK_REGISTER.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUNBOOK.md`

## Boundaries

In scope: full accepted-window substrate materialization (features done on V1;
labels P16-P20 per the accepted per-family engine policy), roll-splice +
maintenance-crossing guards, registry integration + resolver smoke, coverage/
quality matrices, N_eff / walk-forward wiring, and the Core Pilot INCONCLUSIVE
StudySpec re-run on real materialized inputs. Out of scope: new alpha ideation,
platform rewrite, FactorLibrary/AlphaBook/Strategy Reference, paper/live/
broker, deleting or weakening the reference label engine, mixing producers in
one value series, committing values/SQLite/runs, and any alpha/profitability/
tradability claim.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state - the
coordinator performs the run-state surgery (state.json backup + P19/P20 reset,
registry backup, STOP removal) per the reintegration handoff before
`just frontier-resume-run 2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.
For live phase status, trust `runs/<run_id>/state.json` /
`python tools/frontier/status_doctor.py`, never this file. Phase branches never
write this pointer; the coordinator owns it.
