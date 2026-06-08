# FCFP-P09 Handoff

Summary: Implemented the V1 `cross_market` aligned-panel Polars pack for the
governed ES/NQ/RTY Cross-Market family, wired it into the fail-closed fast-pack
resolver, added strict-intersection and asof reference-parity coverage, updated
value-free docs/evidence, and left all changes unstaged for Ralph.

## Files For Ralph To Stage

Codex did not run `git add`, `git commit`, `git push`, `git status`, or
`git diff` because the executor prompt explicitly prohibited them. Ralph should
stage only these commit-eligible paths:

- `src/alpha_system/features/fast/__init__.py`
- `src/alpha_system/features/fast/cross_market_panel.py`
- `src/alpha_system/features/fast/packs.py`
- `tests/unit/feature_compute_fast_path/parity_harness.py`
- `tests/unit/feature_compute_fast_path/test_cross_market_pack.py`
- `tests/fixtures/feature_compute_fast_path/README.md`
- `tests/fixtures/feature_compute_fast_path/cross_market.py`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `docs/feature_compute_fast_path/PACK_MATERIALIZER.md`
- `research/feature_compute_fast_path_v1/README.md`
- `research/feature_compute_fast_path_v1/parity/cross_market/FCFP-P09_PARITY.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P09.md`

No `runs/**` path, review artifact, verdict artifact, value artifact, SQLite
file, Parquet file, or heavy artifact is included in this list.

## Git Status

`git status --short` was not run. The executor prompt explicitly prohibited
`git status`; changes were left unstaged for Ralph.

## Scope Completed

- Added `src/alpha_system/features/fast/cross_market_panel.py`.
- Registered `supports_cross_market_pack()` / `build_cross_market_pack()` in
  `build_fast_feature_pack()` and exported the pack from
  `alpha_system.features.fast`.
- Implemented the exact governed 11-feature Cross-Market pack:
  synchronized returns, NQ/RTY return spreads versus ES, NQ/RTY rolling beta
  residuals versus ES, NQ/RTY rolling correlations versus ES,
  confirmation/divergence flags, and risk-on/risk-off rotation proxies.
- Built one ES/NQ/RTY aligned Polars panel in `prepare_frame`. The
  `strict_intersection` path inner-joins exact shared `event_ts` rows, derives
  output `available_ts` from the max contributing timestamp, and does not carry
  one instrument's stale return into another instrument's later event. The
  legacy `asof` policy is also matched to the reference union availability
  timeline.
- Preserved feature identity through `FeatureVersion.derive(feature_spec)` for
  every declaration; no V1-specific identity is minted.
- Preserved reference gap/flag behavior for leading history gaps, no-trade
  return gaps, session-reset return gaps, rolling `input_gap`,
  `zero_benchmark_variance`, `zero_target_variance`, and optional exact-time BBO
  flags.
- Extended the parity harness to compare mapping values so
  `synchronized_returns` can be checked with the same tolerance machinery.
- Added a synthetic ES/NQ/RTY fixture with delayed NQ availability, a missing RTY
  event, optional missing-BBO row, no-trade row, RTH-to-ETH reset, and rolling
  variance gap branches.
- Added a value-free parity note under
  `research/feature_compute_fast_path_v1/parity/cross_market/`.
- Updated fast-path docs and the root README snapshot without marking the phase
  verdict.

## Parity Results

Fixture: `tests/fixtures/feature_compute_fast_path/cross_market.py`  
Rows: tiny synthetic OHLCV rows for ES/NQ/RTY plus one optional BBO row.  
Alignment policies tested: `strict_intersection` primary parity gate and `asof`
regression.  
Tolerance: point features are exact; rolling beta-residual and rolling
correlation use absolute/relative tolerance `1e-12`, justified by equivalent
floating-point covariance, variance, residual, and correlation reductions in the
Polars and Python reference paths.

Additional parity confirmations:

- `available_ts` parity: exact, including delayed NQ max-availability under
  `strict_intersection`.
- Gap-row parity: exact for leading history gaps, `input_gap`, session reset,
  `zero_benchmark_variance`, `zero_target_variance`, and no-trade propagation.
- Quality-flag parity: exact sorted/lower-cased sets, including optional
  `bbo_gap` / `nq_bbo_gap` / `missing_bbo`.
- No cross-instrument forward-fill: the fixture omits one RTY event; both the
  reference and fast strict-intersection outputs emit no record for that event.
- `feature_version_id` equality: exact for all 11 features.

## Validation Results

- `if [ -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP ]; then printf 'STOP present\n'; else printf 'STOP absent\n'; fi; if [ -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P09/STOP ]; then printf 'phase STOP present\n'; else printf 'phase STOP absent\n'; fi`:
  PASS, output:
  ```text
  STOP absent
  phase STOP absent
  ```
- `git status --short`: SKIPPED. Executor prompt forbids `git status`.
- `python tools/verify.py --smoke`: PASS, no output.
- `python -m pytest tests/unit/feature_compute_fast_path/test_cross_market_pack.py -q`:
  PASS, output:
  ```text
  ...                                                                      [100%]
  3 passed in 0.51s
  ```
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`: PASS, output:
  ```text
  .................                                                        [100%]
  17 passed in 0.89s
  ```
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`:
  PASS, output:
  ```text
  ............                                                             [100%]
  12 passed in 0.17s
  ```
- `python tools/verify.py --lint`: PASS with environment skip, output:
  ```text
  ruff is not installed; run `pip install -e ".[dev]"` to enable lint. Skipping.
  ```
- `python tools/verify.py --typecheck`: PASS, output:
  ```text
  + /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m compileall -q src tests tools
  ```
- `python tools/verify.py --test`: RED outside P09 scope, output summary:
  ```text
  =========================== short test summary info ============================
  FAILED tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture
  FAILED tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture
  FAILED tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline
  FAILED tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only
  ======================= 4 failed, 2904 passed in 47.67s ========================
  + /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest
  ```
  The P09 fast-path tests passed inside this run:
  `tests/unit/feature_compute_fast_path/test_cross_market_pack.py ...`.
  The four failures are outside the allowed P09 paths: DuckDB/Polars fixture
  helpers returned tuples where tests expected lists, the Databento canonicalize
  fixture produced no JSONL rows, and the runtime cache policy selected
  `ALPHA_DATA_ROOT` in this environment instead of run artifacts.
- `python tools/hooks/canary_runner.py`: PASS, output:
  ```text
  PASS forbidden_git_add_dot
  PASS policy_doc_mentions_forbidden_command
  PASS forbidden_test_tamper
  PASS forbidden_secret
  PASS forbidden_large_binary
  PASS forbidden_destructive_op
  PASS forbidden_boundary_import
  PASS forbidden_raw_data_commit
  PASS forbidden_stray_raw_suffix
  PASS forbidden_stray_dbn_suffix
  PASS forbidden_cache_data_commit
  PASS forbidden_local_artifacts
  PASS forbidden_scope_drift
  PASS generated_scaffold_allowed
  PASS governance_future_shift
  PASS governance_permuted_labels
  PASS governance_optimistic_fill
  All Frontier canaries passed.
  ```
- `git ls-files runs`: SKIPPED. Executor prompt forbids git commands.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: SKIPPED. Executor prompt forbids
  git commands.
- Non-git artifact scan:
  `find src/alpha_system/features/fast tests/unit/feature_compute_fast_path tests/fixtures/feature_compute_fast_path docs/feature_compute_fast_path research/feature_compute_fast_path_v1 -type f \( -name '*.parquet' -o -name '*.sqlite' -o -name '*.db' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' \) -print`:
  PASS, no output.
- Run-local review/verdict scan:
  `find runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P09 -maxdepth 2 -type f \( -name 'review.md' -o -name 'verdict.json' \) -print`:
  exit code 1 because the phase directory was absent; output:
  ```text
  find: 'runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P09': No such file or directory
  ```
- Boundary scan:
  `rg -n "databento|ib_insync|IBKR|api[_-]?key|secret|read_parquet|\.dbn|\.zst|\.feather" src/alpha_system/features/fast tests/unit/feature_compute_fast_path tests/fixtures/feature_compute_fast_path -S`:
  PASS, exit code 1 with no output, the expected no-match result.
- `python -m py_compile src/alpha_system/features/fast/cross_market_panel.py tests/unit/feature_compute_fast_path/test_cross_market_pack.py tests/fixtures/feature_compute_fast_path/cross_market.py`:
  PASS, no output.

Polars was available in this environment; no Polars-absent skip occurred for the
P09 parity tests.

## Artifact And Boundary Confirmation

- Codex left all changes unstaged for Ralph.
- Codex did not write a run-local handoff under `runs/**`.
- Codex did not create `review.md`, `verdict.json`, review artifacts, a PR, or a
  merge.
- No Parquet, SQLite, DB, Arrow, Feather, DBN, Zstd, raw/canonical data,
  provider response, feature value, label value, log, cache, or model artifact
  is listed for staging.
- Reference engine files were consumed read-only:
  `src/alpha_system/features/families/cross_market/family.py` and
  `src/alpha_system/features/primitives/causal.py` were not edited.
- Resolver exact-id semantics, `FeatureStore`, and the registry write path were
  not weakened or bypassed.
- No live trading, paper trading, broker operation, order routing, external
  provider call, production deployment, destructive cleanup, profitability
  claim, or tradability claim was made.

Ralph owns staging, cached-diff audit, commit, review routing, verdict parsing,
PR, CI, merge gate, merge, and phase done-check.
