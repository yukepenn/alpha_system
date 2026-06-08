# PHASE_PLAN — FEATURE_COMPUTE_FAST_PATH_V1

16 phases (FCFP-P00..P15), `dag_wave` scheduler, serial merge queue. Family-pack phases
build in parallel (distinct modules + synthetic fixtures) and merge serially; phases that touch
the real local registry or run benchmarks share `resource_class: materialization_registry` and
are serialized. The reference engine is the parity oracle for every pack.

| Phase | Name | Lane | Depends on | Resource |
| --- | --- | --- | --- | --- |
| FCFP-P00 | Campaign Bootstrap and Active Pointer | GREEN | — | — |
| FCFP-P01 | V1 Engine Core + Reference-Parity Harness | YELLOW | P00 | — |
| FCFP-P02 | base_ohlcv Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P03 | session/calendar/maintenance Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P04 | vwap/session-auction Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P05 | regime/vol/compression Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P06 | liquidity-sweep/PA-structure Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P07 | volume/activity Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P08 | bbo tradability/top-book Polars Pack + Parity | YELLOW | P01 | — |
| FCFP-P09 | cross_market aligned-panel Polars Pack + Parity | YELLOW | P02,P05 | — |
| FCFP-P10 | multi-horizon fixed-horizon Label Pack + Parity | YELLOW | P01 | — |
| FCFP-P11 | Targeted/Incremental Materialization CLI | YELLOW | P01 | — |
| FCFP-P12 | Engine/Value-Schema Versioning + Reconciliation | YELLOW | P02..P09 | materialization_registry |
| FCFP-P13 | Benchmark Gate | YELLOW | P02..P10 | materialization_registry |
| FCFP-P14 | V1 Producer Path Integration + Resolver Smoke | YELLOW | P11,P12,P13 | materialization_registry |
| FCFP-P15 | Closeout + FUTSUB Resume Handoff | YELLOW | P14 | — |

## DAG shape

- **Bootstrap**: P00.
- **Engine core**: P01 (the PackMaterializer + parity harness everything builds on).
- **Family packs (parallel build, serial merge)**: P02–P08 depend only on P01; P09 (cross_market)
  depends on P02 + P05 because it reuses base + regime primitives; P10 (labels) depends on P01.
- **CLI**: P11 (targeting/incremental) depends on P01.
- **Reconciliation**: P12 depends on all feature packs (P02–P09).
- **Benchmark**: P13 depends on all packs incl. labels (P02–P10).
- **Integration**: P14 depends on P11 + P12 + P13.
- **Closeout**: P15 depends on P14.

## Lane summary

- 1 GREEN (P00 bootstrap, auto-merge, review optional).
- 15 YELLOW (fresh Claude Opus review required; auto-merge after review when gates pass).
- 0 RED (no external/live/broker/destructive scope; campaign expected to avoid Red).

## Per-phase contract

Every phase carries: id, lane, dependencies, purpose, scope, non-goals, checks (validation),
allowed_paths (expected files), forbidden_paths (forbidden changes), artifact_policy, done
criteria, handoff requirement, review requirement, and auto-merge eligibility — see
`campaign.yaml`.
