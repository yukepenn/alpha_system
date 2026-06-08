# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1`
Workflow: `workflow2`
Run: `workflow2 ready to launch` - contract bundle authored; mock run 16/16 PASS; live WF2 run starting
Status: `contract authored (validated, ready to run)` - the 6-file campaign bundle
is present, YAML parses, the DAG plan is valid, and a deterministic mock run
completed 16/16 PASS with no providers/network/merge. `FCFP-P00`
(coordinator-owned, `must_run_alone`) re-confirms this pointer at run start.

Current phase: `none` - run starting
Next phase: `FCFP-P00` - Campaign Bootstrap and Active Pointer
Completed phases: `0/16`

Campaign `FEATURE_COMPUTE_FAST_PATH_V1` builds a single-machine, local, columnar
(Polars), batch/vectorized, incremental, **reference-parity-gated**, registry-safe
**producer compute fast path** for feature/label materialization (ADR-0007), so
large-scale backfill stops depending on the per-row Python reference engine -
which remains the correctness **oracle**. A measured proof
(`research/futures_substrate_scaleout_v1/producer_fast_path/V1_PROOF.md`) computed
all 6 base_ohlcv features for ES 2024 in **0.19s vs ~108s** (~500x) with reference
parity. It is substrate/infra engineering only: NOT Ray/GPU/cluster, NOT a
feature-compiler platform, NOT alpha ideation, NOT FactorLibrary/AlphaBook/Strategy
Reference, NOT paper/live/broker; no profitability or tradability claim.

```text
reference engine (oracle, kept)
  -> V1 PackMaterializer engine core + parity harness
  -> per-family Polars packs (base/session/vwap/regime/structure-liquidity/volume/bbo)
  -> cross-market aligned ES/NQ/RTY panel
  -> multi-horizon fixed-horizon label pack
  -> targeted/incremental CLI
  -> engine/value-schema versioning + reconciliation
  -> benchmark gate
  -> V1 producer-path integration + resolver smoke
  -> closeout + FUTSUB resume-on-V1 handoff
```

## Paused predecessor

`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is **paused** at FUTSUB-P14 pending
V1. Its driver is fixed and merged (PRs #276-#280); all 8 families validated on
bounded-real 2024; the reference-engine full-window backfill produced 663 records
(0 orphaned, preserved, backed up) before the coordinator paused it to build V1.
After this campaign closes (FCFP-P15 writes the resume handoff), the coordinator
amends FUTSUB so P06-P13/P16-P20 materialize via V1 and P14/P22 validate V1
output, reconciles the existing reference outputs (ADR-0007), and resumes FUTSUB
P14 -> P33 on V1.

## Campaign Identity

- Campaign ID: `FEATURE_COMPUTE_FAST_PATH_V1`
- Campaign path: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1`
- Repo: `alpha_system` / `~/projects/alpha_system`
- Workflow: `workflow2` (Ralph strict autonomous loop; `dag_wave`; registry-touching
  phases serialized by a shared `materialization_registry` resource_class; serial merge)
- Project profile: `trading_research` / `research` / `producer_compute_fast_path`
- Phase count: 16 phases (`FCFP-P00` ... `FCFP-P15`)
- Lane policy: Green/Yellow only; **no Red scope**
- Decision record: `decisions/0007-producer-compute-fast-path.md`
- Proof: `research/futures_substrate_scaleout_v1/producer_fast_path/V1_PROOF.md`

## Contract Bundle

- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/GOAL.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/PHASE_PLAN.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/campaign.yaml`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/ACCEPTANCE.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/RISK_REGISTER.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/RUNBOOK.md`

## Boundaries

In scope: the V1 PackMaterializer engine + parity harness; per-family Polars packs
with reference-parity tests; cross-market aligned panel; multi-horizon label pack;
targeted/incremental CLI; engine/value-schema versioning + reconciliation;
benchmark gate; V1 driver integration + resolver smoke. Out of scope: resuming the
FUTSUB full backfill (coordinator action under FUTSUB on V1 after this closes);
Ray/GPU/cluster; feature-compiler/DSL platform; new alpha ideation / AlphaSpecs;
new features/labels beyond existing governed families; param search;
FactorLibrary/AlphaBook/Strategy Reference; paper/live/broker/order; external
provider calls; raw/canonical/feature/label/value or local-DB commits; any
profitability or tradability claim. The reference engine is never deleted or
weakened; resolver exact-id semantics and serial registry writes are never weakened.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request; Ralph checks it before phase
selection, execution, checks, review, PR, CI, merge gate, merge, done-check, and
next-phase. Resume continues from recorded run state. Registry-touching phases
(FCFP-P12/P13/P14) share `resource_class: materialization_registry` and never run
concurrently; merges are always serial. This pointer is updated by `FCFP-P00` and
`FCFP-P15` only (coordinator-owned, `must_run_alone`).
