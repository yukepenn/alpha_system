# Active Campaign

Project: `alpha_system`

Campaign: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1`
Workflow: `workflow2`
Run: `workflow2 active` - bootstrap pointer and documentation phase prepared
Status: `bootstrap complete` - `FCFP-P00` refreshed the root pointer, confirmed
the campaign bundle shape, added the documentation index, and anchored the
value-free evidence directory. Ralph owns staging, commit, review routing,
merge-gate evaluation, and downstream phase selection.

Current phase: `FCFP-P01` - V1 Engine Core + Reference-Parity Harness
Next phase: `FCFP-P01` - V1 Engine Core + Reference-Parity Harness
Completed phases: `1/16` (`FCFP-P00`)

Campaign `FEATURE_COMPUTE_FAST_PATH_V1` builds a single-machine, local,
columnar, batch/vectorized, incremental, reference-parity-gated, registry-safe
producer compute path for feature/label materialization. The per-row Python
reference engine remains the correctness oracle.

```text
reference engine (oracle, retained)
  -> V1 PackMaterializer engine core + parity harness
  -> per-family Polars packs
  -> cross-market aligned panel
  -> multi-horizon fixed-horizon label pack
  -> targeted/incremental CLI
  -> engine/value-schema versioning + reconciliation
  -> benchmark gate
  -> V1 producer-path integration + resolver smoke
  -> closeout + FUTSUB resume-on-V1 handoff
```

## Campaign Identity

- Campaign ID: `FEATURE_COMPUTE_FAST_PATH_V1`
- Campaign path: `campaigns/FEATURE_COMPUTE_FAST_PATH_V1`
- Repo: `alpha_system` / `~/projects/alpha_system`
- Workflow: `workflow2` (Ralph strict autonomous loop; `dag_wave`; serial merge queue)
- Project profile: `trading_research` / `research` / `producer_compute_fast_path`
- Phase count: 16 phases (`FCFP-P00` ... `FCFP-P15`)
- Lane policy: Green/Yellow only; no Red scope
- Next phase: `FCFP-P01`

## Contract Bundle

- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/GOAL.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/PHASE_PLAN.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/campaign.yaml`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/ACCEPTANCE.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/RISK_REGISTER.md`
- `campaigns/FEATURE_COMPUTE_FAST_PATH_V1/RUNBOOK.md`

## Durable Bootstrap Artifacts

- Fast-path documentation index: `docs/feature_compute_fast_path/`
- Value-free evidence skeleton: `research/feature_compute_fast_path_v1/`
- Commit-eligible P00 handoff:
  `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P00.md`

## Boundaries

This campaign is substrate/infra engineering only. It does not authorize live
trading, paper trading, broker operations, order routing, production deployment,
external provider calls, alpha ideation, new AlphaSpecs, new features/labels
beyond existing governed families, parameter search, Ray/GPU/cluster, or a
feature-compiler/DSL platform.

The reference engine is never deleted or weakened. Resolver exact-id semantics,
official keystone registry writes, and serial registry writes remain unchanged.
Raw/canonical data, feature values, label values, local SQLite registries,
provider responses, heavy artifacts, logs, caches, and `runs/**` artifacts remain
local-only and are never committed. No profitability or tradability claim is made.

## Stop / Resume

A `runs/<run_id>/STOP` file is an active stop request. Ralph checks it before
phase selection, execution, checks, review, PR, CI, merge gate, merge, done-check,
and next-phase selection. Resume continues from recorded run state.
