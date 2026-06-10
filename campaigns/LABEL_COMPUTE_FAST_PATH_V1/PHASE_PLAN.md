# PHASE_PLAN — LABEL_COMPUTE_FAST_PATH_V1

10 phases (LCFP-P00..P09), `dag_wave` scheduler, serial merge queue. The three label-pack
phases (P03/P04/P05) build in parallel after the shared panel/terminal/guard contract (P02)
lands — they edit distinct modules with synthetic fixtures — and merge serially. Phases that
touch the real local label registry or run benchmarks (P06 integration, P08 benchmark) share
`resource_class: materialization_registry` and are serialized. The per-row reference label
engine is the parity oracle for every pack and is never deleted or weakened.

| Phase | Name | Lane | Depends on | Resource |
| --- | --- | --- | --- | --- |
| LCFP-P00 | Campaign Bootstrap + FUTSUB Pause Handoff | GREEN | — | — |
| LCFP-P01 | Label Engine Inventory + Baseline Benchmark | YELLOW | P00 | — |
| LCFP-P02 | Shared Label Panel / Terminal / Guard Contract | YELLOW | P01 | — |
| LCFP-P03 | Fast Fixed + Extended Horizon Labels | YELLOW | P02 | — |
| LCFP-P04 | Fast Session / Maintenance / Cost Labels | YELLOW | P02 | — |
| LCFP-P05 | Fast Path Labels (MFE/MAE/TBS/Triple-Barrier) | YELLOW | P02 | — |
| LCFP-P06 | Worker / Checkpoint / Registry / Resolver Integration | YELLOW | P03,P04,P05 | materialization_registry |
| LCFP-P07 | Parity / No-Lookahead / Guard Test Suite | YELLOW | P03,P04,P05 | — |
| LCFP-P08 | Benchmark + Production Readiness Gate | YELLOW | P06,P07 | materialization_registry |
| LCFP-P09 | FUTSUB Reintegration Handoff + Closeout | YELLOW | P08 | — |

## DAG shape

- **Bootstrap**: P00 (records the FUTSUB stop state; preserves all valid values/registries).
- **Inventory/baseline**: P01 (reference-path inventory + bounded baseline benchmark).
- **Shared contract**: P02 (the panel/terminal/guard/`label_available_ts` contract every
  pack builds on — the LCFP analogue of FCFP-P01's engine core).
- **Label packs (parallel build, serial merge)**: P03 (fixed + extended horizons; also
  repairs the stale FCFP-P10 fixed-horizon pack/fixture against the extended governed enum —
  `tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py` is currently RED
  with polars installed and must be green from P03 onward),
  P04 (session-close / maintenance-flat / cost-adjusted), P05 (path labels) depend only
  on P02 and edit distinct modules.
- **Integration**: P06 (targeting / checkpoint / workers / serial registry / resolver smoke)
  depends on P03+P04+P05 and shares `materialization_registry`.
- **Parity suite**: P07 depends on P03+P04+P05 (synthetic + guard-case parity; CI-runnable).
- **Benchmark/readiness**: P08 depends on P06+P07 and shares `materialization_registry`.
- **Closeout**: P09 depends on P08 (executable FUTSUB reintegration handoff; no alpha mining).

## Lane summary

- 1 GREEN (P00 bootstrap, auto-merge, review optional).
- 9 YELLOW (fresh Claude Opus review required; auto-merge after review when gates pass).
- 0 RED (no external/live/broker/destructive scope; campaign expected to avoid Red).

## Per-phase contract

Every phase carries: id, lane, dependencies, purpose, scope, non-goals, checks (validation),
allowed_paths (expected files), forbidden_paths (forbidden changes), artifact_policy, done
criteria, handoff requirement, review requirement, and auto-merge eligibility — see
`campaign.yaml`.
