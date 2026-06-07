# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Workflow: `workflow2`
Run: `workflow2 not started` - contract bundle authored; live WF2 run not yet started
Status: `contract authored (ready to plan/run)` - the 6-file campaign bundle is
present, YAML parses, gates cover all 34 phases exactly once. No phase has run
yet. `FUTSUB-P00` (coordinator-owned, `must_run_alone`) will re-confirm this
pointer at run start.

Current phase: `none` - run not started
Next phase: `FUTSUB-P00` - Campaign Bootstrap and Active Pointer
Completed phases: `0/34`

Campaign `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is the bridge from the
smoke/pilot-scale substrate to a **full-window, BBO-aware, roll-guarded,
resolver-safe research substrate**. It accepts/locks the existing Databento
ES/NQ/RTY DatasetVersions, materializes the existing feature/label families over
the full 2018->2026 window, adds the roll-splice + maintenance-crossing guards
and N_eff / walk-forward wiring, produces coverage and quality matrices, proves
registry-resolved Parquet values are runtime-usable, and re-runs the Core Pilot's
INCONCLUSIVE StudySpecs against real materialized inputs. It is **substrate
engineering, not new alpha ideation** (the AlphaSpecs/StudySpecs already exist
and are reusable).

```text
accepted DatasetVersions
  -> full-window FeaturePack materialization
  -> full-window LabelPack materialization
  -> roll-splice / maintenance-crossing guards
  -> N_eff / walk-forward wiring inputs
  -> resolver smoke
  -> coverage matrices
  -> Core Pilot inconclusive StudySpec rerun
  -> handoff to Validation Governance / FactorLibrary / Multi-Horizon Mining
```

Inherited Core Pilot promotion boundary (the baseline this campaign refreshes):
`4` `REJECT`, `6` `INCONCLUSIVE`, `0` `WATCH`, `0` `CANDIDATE_RESEARCH`. The
pilot's gaps were a **substrate coverage finding, not an alpha failure**.

Ralph owns authoritative validation, staged-set audit, review routing, verdict
parsing, repair routing, PR, CI, merge, and final done-check actions. This
pointer is updated by `FUTSUB-P00` and `FUTSUB-P33` only (coordinator-owned,
`must_run_alone`).

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Campaign path: `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2`
- Mode: Ralph-driven strict autonomous loop (`dag_wave`; materialization
  serialized by a shared registry `resource_class`; serial merge queue)
- Project profile: `trading_research` / `research` / `research_substrate_scaleout`
- Phase count: 34 phases (`FUTSUB-P00` ... `FUTSUB-P33`)
- Lane policy: Green/Yellow only; **no Red scope**
- Predecessor: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
  (`COMPLETE_WITH_WARNINGS`, 31/31) -
  `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
- Source handoff:
  `research/futures_core_alpha_pilot_v1/closeout/SUBSTRATE_SCALEOUT_V1_HANDOFF.md`
- Measured reality: `docs/SUBSTRATE_REALITY_REPORT.md`

## Contract Bundle

- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/PHASE_PLAN.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACCEPTANCE.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RISK_REGISTER.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUNBOOK.md`

## Boundaries

This campaign is aggressive on materialization but bounded on scope. In scope:
DatasetVersion acceptance-lock; roll-splice + maintenance-crossing guards;
full-window FeaturePacks (8 families) and LabelPacks (diagnostic/primary/extended/
session-close/maintenance-flat/cost-adjusted/path); resolver smoke; coverage +
BBO-quality + cross-market-alignment matrices; N_eff + walk-forward wiring; Core
Pilot re-lock + rerun.

Out of scope (handed off or deferred): new alpha ideation / new AlphaSpec batch;
multiple-testing / DSR/PBO/PSR correction engine; FactorLibrary ingestion
pipeline; Strategy Reference validation; AlphaBook; Research Runner; full roll
execution engine / IBKR contract resolver / back-adjusted continuous
construction; L1/L2 event-stream; ML/DL/RL; portfolio construction;
paper/live/broker/order; external provider calls; raw/canonical/feature/label/
value or local-DB / roll-calendar commits; any profitability or tradability
claim. BBO is a tradability proxy, not execution truth; the roll calendar is
analytic/approximate, not provider-exact.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge,
done-check, and next-phase. Resume continues from recorded run state. Because
materialization phases share `resource_class: materialization_registry` and are
not `parallel_safe`, registry-writing phases never run concurrently; merges are
always serial. A STOP halts new phase selection and new merges.
