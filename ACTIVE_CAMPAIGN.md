# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Workflow: `workflow2`
Status: `resuming`. The Discovery Rigor Floor (RIGOR-P00..P07) is COMPLETE 8/8
and the FUTSUB kill-shot readiness checklist is 13/13 `MET` (fire condition
SATISFIED), so the boundary-STOPPED substrate-scaleout run resumes at the
FUTSUB-P28 Core Pilot kill-shot re-run.

## Resume context

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` run `2026-06-07T235209Z_...` was
deliberately boundary-STOPPED at 28/34 (P00–P27 merged) with FUTSUB-P28 BLOCKED
behind the Stage-B rigor gate. The gate is now satisfied:

- Readiness 13/13 `MET` (`research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md`),
  including row 6 (six per-family real-data surrogate calibrations, all
  `zero-pass-met`) and the POST-RELOCK_V2 reconciliation of rows 8/9/11.
- Track-B pre-registered pre-metric against the V2 anchor (`poolhyp_d3b3d986`,
  `poolhyp_0755f597`).
- P28 is reset BLOCKED→PENDING at resume; the run resumes from recorded state.

Caveats that travel into the kill-shot run context (resume handoff step 3):
R-037 `contract_id`, BBO-proxy regime limits, and the BBO proxy-flag /
`spread_ticks` degeneracy substrate caveat (74 bbo sub-configs excluded as
degenerate — recorded substrate findings, not signal).

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Run: `2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
  (resuming from 28/34; P28 kill-shot + P29–P33 closeout remain)
- Contract bundle: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`

## Boundaries

In scope: P28 re-run of the previously-INCONCLUSIVE Core Pilot studies (Track A
exact reruns + Track B pooled hypotheses, scored separately), P29–P33 closeout
and verdict evidence. Out of scope: any alpha/profitability/tradability claim;
historical evidence mutation; Mining-V2 / FactorLibrary mechanisms. No live
trading, paper, broker, or capital scope (research-only, evidence-gated).

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
every stage transition. Resume continues from recorded run state. For live phase
status, trust `python tools/frontier/status_doctor.py` /
`runs/<run_id>/state.json`, never this file. Phase branches never write this
pointer; the coordinator owns it.
