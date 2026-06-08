# RISK_REGISTER — FEATURE_COMPUTE_FAST_PATH_V1

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | V1 values diverge from the reference beyond float tolerance (silent correctness bug) | Med | High | Mandatory synthetic-fixture parity gate per pack (value/available_ts/gap/flags); unexplained diff is a blocker; reference engine retained as oracle; `producer_engine_id` tags provenance. |
| R2 | Session-reset / gap / quality-flag semantics not faithfully vectorized | Med | High | Parity fixtures include session boundaries, leading gaps, and missing rows; cross_market (P09) and session-reset packs (P03–P07) carry explicit gap+reset fixtures. |
| R3 | feature_version_id / label_version_id drift (identity changes, breaks resolver/StudySpec locks) | Low | High | V1 produces values only; identity comes from the same FeatureSpec; parity asserts id equality; resolver-smoke at integration (P14). |
| R4 | Float-tolerance differences vs already-materialized reference outputs cause silent engine mixing | Med | Med | Engine/value-schema versioning (P12); reconciliation policy: within tolerance keep+tag, beyond tolerance re-materialize/version; never mix silently; existing 663 records preserved. |
| R5 | Parallel registry writes corrupt the shared SQLite | Low | High | Serial registry writes enforced; registry-touching phases share `materialization_registry` resource_class; no parallel SQLite. |
| R6 | Scope creep into a feature-compiler/DSL/distributed platform | Med | Med | Hard boundaries: single-machine/local/columnar only; no Ray/GPU/cluster; no DSL; per-family packs reuse existing governed families; forbidden_global_changes enforced. |
| R7 | Polars becomes a hard dependency (violates empty-core-deps contract) | Low | Med | Use the existing optional-dependency guard (`require_dependency("polars")`); reference engine remains the dependency-free fallback; CI parity tests skip-or-guard if polars absent (env-only red documented). |
| R8 | Committing heavy artifacts / values / SQLite | Low | High | Explicit staging only; artifact audit before merge; never_commit globs; `git ls-files runs` + parquet/sqlite globs must be empty; value-free summaries only. |
| R9 | Benchmark/parity run touches real data and is mistaken for production backfill | Low | Med | Bounded-real only; benchmark values local-only; full backfill is explicitly out of scope (resumes under FUTSUB on V1). |
| R10 | cross_market aligned-panel forward-fills across instruments (lookahead) | Med | High | No cross-instrument forward-fill (policy + parity fixture); per-instrument available_ts preserved; asof-join semantics tested. |
| R11 | Multi-horizon label batching applies guards inconsistently across horizons | Med | High | Roll-splice + maintenance-crossing guards applied once over the shared panel; parity fixture asserts guard behavior + label_available_ts per horizon. |
| R12 | Boundary violation: provider tokens leak into features/labels code | Low | Med | `tests/no_lookahead/feature_label/test_synthetic_fail_closed.py` in every pack's checks; fast code reads canonical via sanctioned readers only; no provider literals. |

Red-lane risks (external/live/broker/destructive) are out of scope; the campaign is expected to
avoid Red. If any task appears to require Red scope, STOP and request scoped authorization.
