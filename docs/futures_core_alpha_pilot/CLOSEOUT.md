# Futures Core Alpha Pilot Closeout

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Final verdict: `COMPLETE_WITH_WARNINGS` (coordinator resolution; autonomous
`FUTCORE-P30` recorded `BLOCKED` on a local-only, CI-green verifier failure —
see `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT_COORDINATOR_RESOLUTION.md`)  
Closeout phase: `FUTCORE-P30`

The authoritative closeout audit is
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`. This page is the
durable operator-facing summary.

## Final State

The P30 audit artifacts were produced, but terminal closeout is blocked because
the required `python tools/verify.py --all` command failed. P28 recorded 4
`REJECT` outcomes and 6 `INCONCLUSIVE` outcomes. It recorded 0 `WATCH` and 0
`CANDIDATE_RESEARCH` outcomes, so the campaign produces no FactorLibrary
ingestion survivor and no Strategy Reference validation candidate.

## Why The Verdict Is Blocked

The verifier failed with 4 failing tests and 2840 passing tests. The failing
tests were:

- `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
- `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
- `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`
- `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`

The audit also records warning-bearing evidence limitations:

- cross-market missingness and cross-instrument availability gaps;
- unresolved locked feature bindings for several derived-state groups;
- unresolved materialized `15m` LabelPack evidence in diagnostics;
- BBO fallback and proxy-only cost/capacity language;
- thin-session and RTH-comparator gaps;
- variant-count evidence-format warnings for pre-grid blocked reports;
- executor-side limitations from the prompt: Codex did not run reviewer,
  staging, `git status`, `git diff`, PR, merge, or phase PASS steps.

These warnings are not favorable evidence and do not authorize broader scope.

## Closeout Pointers

- Acceptance audit:
  `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
- Research closeout summary:
  `research/futures_core_alpha_pilot_v1/closeout/README.md`
- Downstream handoffs:
  `docs/futures_core_alpha_pilot/DOWNSTREAM_HANDOFFS.md`
- Promotion boundary:
  `docs/futures_core_alpha_pilot/PROMOTION_DECISIONS.md`
- Evidence ledger:
  `docs/futures_core_alpha_pilot/LEDGERS.md`

## Safety Boundary

The pilot remains research-only and evidence-only. It does not provide paper,
live, broker, order, production, capital-allocation, profitability,
tradability, FactorLibrary promotion, Strategy Reference validation, or
AlphaBook output.
