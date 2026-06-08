# FCFP-P08 Executor Handoff

## Scope

Implemented the BBO tradability / top-book Polars pack in the V1 fast feature
engine and added a synthetic-fixture parity test against the reference BBO
family. The pack computes the governed BBO feature set only; it does not write a
registry, run real-data backfill, call broker/live/paper surfaces, create a PR,
or create review/verdict artifacts.

## Changed Files

- `src/alpha_system/features/fast/bbo_tradability.py`
- `src/alpha_system/features/fast/packs.py`
- `src/alpha_system/features/fast/__init__.py`
- `tests/fixtures/feature_compute_fast_path/bbo_tradability.py`
- `tests/fixtures/feature_compute_fast_path/README.md`
- `tests/unit/feature_compute_fast_path/test_bbo_tradability_pack.py`
- `docs/feature_compute_fast_path/README.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P08.md`

## Implementation Notes

- Added `build_bbo_tradability_pack` / `supports_bbo_tradability_pack` and
  resolver/export wiring through the existing `build_fast_feature_pack` path.
- The pack uses `require_dependency("polars")`, validates the exact governed
  BBO feature IDs and default BBO parameters, and emits `FastFeatureDeclaration`
  records whose `feature_version_id` is derived from the reference
  `FeatureSpec`.
- Quote-derived value features gap on missing/quarantined BBO rows or quote
  invariant violations. Missing/quarantined flags, wide-spread and low-depth
  flags, top-book depth/imbalance, microprice, and spread-derived values are
  computed as Polars expressions over the canonical BBO frame.
- `spread_zscore` uses a causal rolling window of 3, `ddof=0`, and a
  session-reset segment keyed by `session_label`, matching the reference
  primitive's reset behavior.
- The synthetic fixture covers leading rolling warm-up, one `missing_bbo` row,
  one `bbo_quarantined` row, a wide-spread / low-depth row, an ETH session reset,
  and a missing `spread_ticks` gap.

## Tolerance

`spread_zscore` parity uses `abs=1e-12` and `rel=1e-12`. This is limited to the
rolling z-score because variance terms can be summed in a different binary order
by the Polars expression path and the Python reference primitive. All other BBO
features use exact parity in the synthetic fixture.

## Identity And Artifact Confirmation

- The parity test asserts fast declaration `feature_version_id` values match the
  reference BBO definitions and then asserts every fast record uses the same
  reference identity.
- No `git add`, commit, push, PR, merge, reviewer, review artifact, or verdict
  action was performed by Codex.
- No values, SQLite files, Parquet/Arrow/Feather files, provider responses,
  heavy artifacts, or `runs/` files were staged by Codex.

## Validation

- STOP check: `runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP` was
  absent.
- `git status --short`: not run. The executor prompt explicitly forbade running
  `git status`.
- `python -m ruff format src/alpha_system/features/fast/bbo_tradability.py src/alpha_system/features/fast/packs.py src/alpha_system/features/fast/__init__.py tests/fixtures/feature_compute_fast_path/bbo_tradability.py tests/unit/feature_compute_fast_path/test_bbo_tradability_pack.py`: exit 1; `ruff` is not installed in this environment.
- `python -m compileall -q src/alpha_system/features/fast tests/fixtures/feature_compute_fast_path tests/unit/feature_compute_fast_path`: exit 0.
- `python -m pytest tests/unit/feature_compute_fast_path/test_bbo_tradability_pack.py -q`: exit 0; 1 passed.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`: exit 0; 14 passed.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`: exit 0; 12 passed.
- `python tools/verify.py --smoke`: exit 0.
- `python tools/verify.py --lint`: exit 0; skipped because `ruff` is not installed.
- `python tools/verify.py --typecheck`: exit 0.
- `python tools/verify.py --test`: exit 1; 2901 passed, 4 failed. Failures were:
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`
    returned a tuple where the test expects a list.
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`
    returned a tuple where the test expects a list.
  - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`
    found empty `ohlcv_rows`.
  - `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
    resolved the cache root to `ALPHA_DATA_ROOT` instead of run artifacts in this
    environment.
- `python tools/hooks/canary_runner.py`: exit 0; all Frontier canaries passed.
- `git ls-files runs`: exit 0; no output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: exit 0; no output.
