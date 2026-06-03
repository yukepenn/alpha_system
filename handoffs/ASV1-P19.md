# ASV1-P19 Handoff - Fast Path and Reference Parity

## Summary

Implemented the ASV1-P19 fast path and deterministic parity harness. The fast
path is acceleration only. The Tier 1 reference 1-minute engine remains the
single canonical PnL truth, and no reference-engine source file was changed.

The accelerated subset covers no-trade, simple long, simple short, fixed bps
costs, fixed stop, target, same-bar adverse-first stop/target ambiguity,
reference `eod_flat`, deterministic trade summary, and deterministic equity
curve. Slippage-configured execution and management features route to reference
fallback or fail closed when fallback is disabled.

## Branch And Commit

Branch:

- `auto/alpha_system_v1/asv1-p19-fast-path-and-reference-parity`

Commit:

- Implementation commit is created after the staged-set audit. Codex reports the
  final commit hash in the execution response.

## Fast Path Scope

Source added:

- `src/alpha_system/backtest/fast_arrays.py`
- `src/alpha_system/backtest/fast_path.py`
- `src/alpha_system/backtest/fixtures.py`
- `src/alpha_system/backtest/parity.py`
- `src/alpha_system/backtest/parity_cases.py`

The fast path:

- reuses reference validators, signal scheduling, fills, result containers, and
  accounting helpers;
- uses optional NumPy/Numba array support when available;
- keeps a deterministic pure-Python array fallback because ASV1-P19 cannot edit
  dependency metadata and NumPy/Numba are not installed in this environment;
- never writes benchmark, array, DB, trade, equity, registry, or run artifacts;
- exposes `ParityCertification` and `assert_grid_fast_path_allowed` for later
  grid gating.

## Parity Matrix

| Feature / case | Route | Tolerance | Result |
| --- | --- | --- | --- |
| no-trade | accelerated | exact | PASS |
| simple long | accelerated | exact | PASS |
| simple short | accelerated | exact | PASS |
| costs | accelerated | exact | PASS |
| fixed stop | accelerated | exact | PASS |
| target | accelerated | exact | PASS |
| same-bar stop/target ambiguity | accelerated, adverse-first | exact | PASS |
| EOD exit (`eod_flat`) | accelerated | exact | PASS |
| deterministic trade summary | accelerated | exact | PASS |
| deterministic equity curve | accelerated | exact | PASS |
| slippage config metadata | reference fallback | exact | PASS |
| partial exits | reference fallback | exact | PASS |
| cooldown | reference fallback | exact | PASS |
| max holding bars | reference fallback | exact | PASS |
| unsupported feature fail-closed | raise when fallback disabled | n/a | PASS |
| grid gate for fallback features | blocked | n/a | PASS |

Exact means zero Decimal tolerance across summary, trade journal, equity curve,
and fills.

## Unsupported Feature Matrix

| Feature | Behavior |
| --- | --- |
| slippage model with non-zero slippage | reference fallback |
| liquidity policy semantics | reference fallback |
| laddered partial exits | reference fallback |
| cooldown | reference fallback |
| max holding bars | reference fallback |
| management fixed stop / target / EOD / time exits | reference fallback |
| ATR, volatility, breakeven, trailing, scale rules | reference fallback |
| max trades per day | reference fallback |
| management risk per trade / max position percent | reference fallback |
| portfolio desired exposure / target semantics | reference fallback |
| multi-instrument or multi-session run | reference fallback |
| unknown future feature label | fail closed |

Reference fallback parity does not certify accelerated grid use. Later grid code
must require accelerated parity for every requested feature.

## Files Changed And Staged

Source:

- `src/alpha_system/backtest/fast_path.py`
- `src/alpha_system/backtest/fast_arrays.py`
- `src/alpha_system/backtest/parity.py`
- `src/alpha_system/backtest/parity_cases.py`
- `src/alpha_system/backtest/fixtures.py`

Docs:

- `docs/FAST_PATH_PARITY.md`
- `docs/FAST_PATH_LIMITATIONS.md`

Tests:

- `tests/parity/helpers.py`
- `tests/parity/test_no_trade_parity.py`
- `tests/parity/test_simple_long_parity.py`
- `tests/parity/test_simple_short_parity.py`
- `tests/parity/test_costs_parity.py`
- `tests/parity/test_slippage_parity.py`
- `tests/parity/test_stop_target_parity.py`
- `tests/parity/test_same_bar_ambiguity_parity.py`
- `tests/parity/test_partial_exit_parity.py`
- `tests/parity/test_eod_exit_parity.py`
- `tests/parity/test_cooldown_parity.py`
- `tests/parity/test_max_holding_parity.py`
- `tests/parity/test_equity_curve_parity.py`
- `tests/parity/test_trade_summary_parity.py`
- `tests/parity/test_unsupported_fast_feature_fail_closed.py`
- `tests/performance/test_fast_path_smoke.py`
- `tests/unit/test_fast_path_artifact_policy.py`

Handoff:

- `handoffs/ASV1-P19.md`

Explicit staging is required for exactly the files above. No `runs/**` path is
commit-eligible for this phase.

## Validation Results

Passed:

- `python -m pytest tests/parity tests/performance/test_fast_path_smoke.py tests/unit/test_fast_path_artifact_policy.py` - PASS, 20 passed.
- `python -m pytest tests/unit tests/integration tests/parity` - PASS, 406 passed after fixing one ASV1-P19 test assertion to compare serialized equity rows.
- `python -m pytest tests/performance || true` - PASS, 1 passed; command exited 0.
- `python -m compileall src` - PASS.
- `python -m compileall tests/parity tests/performance/test_fast_path_smoke.py tests/unit/test_fast_path_artifact_policy.py` - PASS.
- `git diff --check` - PASS.
- `git status --short` - PASS for audit; before staging it showed only ASV1-P19 allowed-path files.
- `find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` - PASS, no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - PASS, no output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` - PASS, no output.
- `find . -path ./tests/fixtures -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" -o -name "*.npy" -o -name "*.npz" \) -print` - PASS, no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` - PASS, no output.
- `git ls-files runs` - PASS, no output.
- `git diff --cached --name-only` - PASS before commit; returned only the ASV1-P19 allowed paths listed in this handoff.
- `git diff --cached --name-only | grep '^runs/'` - PASS before commit; exit 1 with no output, so no `runs/**` path was staged.
- `git diff --cached --name-only | grep -E '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'` - PASS before commit; exit 1 with no output.

Command exception:

- `python -m pytest tests/parity tests/performance tests/unit/backtest` - FAIL, exit 4 because `tests/unit/backtest` does not exist in this repository. Creating that directory is outside ASV1-P19 allowed paths. The covered ASV1-P19 paths passed in the focused parity/performance/artifact run above.

Non-blocking unavailable tools:

- `python -m ruff check src tests || true` - ruff unavailable: `/usr/bin/python: No module named ruff`; command exited 0 due `|| true`.
- `python -m mypy src || true` - mypy unavailable: `/usr/bin/python: No module named mypy`; command exited 0 due `|| true`.

Development failure fixed and recorded:

- Initial `python -m pytest tests/unit tests/integration tests/parity` failed with one ASV1-P19 assertion in `tests/parity/test_equity_curve_parity.py`. The parity checker already compared serialized equity rows successfully; the test used direct dataclass tuple equality. The test was corrected to compare `to_dict()` rows, and the final broad run passed.

## Artifact Policy Confirmation

- `runs/**` remains local-only. `git ls-files runs` returned empty.
- No run-local `handoff.md`, `review.md`, `verdict.json`, or `checks.json` was staged or committed by Codex.
- No benchmark logs, `.npy`/`.npz` arrays, Parquet/Arrow/Feather files, SQLite/DB/journal/WAL files, raw data, canonical data, factor stores, label stores, signal stores, grid outputs, full trade logs, full equity logs, model binaries, caches, or heavy artifacts were staged or committed.
- Fast path, parity, and performance tests do not produce repository-local benchmark artifacts.
- Tiny parity fixtures are in-memory source fixtures only and are documented as correctness fixtures, not market evidence.

## Truth Boundary Confirmation

- Reference truth semantics are unchanged.
- No reference engine source file was edited.
- Fast path defines no second PnL truth and remains acceleration only.
- Unsupported features fail closed or route to reference; they are never silently approximated.
- Same-bar stop/target ambiguity remains conservative and adverse-first.
- Grid use without accelerated parity certification is blocked by `assert_grid_fast_path_allowed`.

## Scope Boundary Confirmation

- No broker, paper trading, live trading, order routing, or production execution scope was introduced.
- No alpha, profitability, robustness, or tradability claims were introduced.
- No CLI command, grid engine, registry schema change, heavy artifact, raw data, or database artifact was introduced.
- No Claude call, reviewer run, `review.md`, `verdict.json`, PR, merge, or PASS marking was performed.

## Risk Dispositions

- R-004 - Same-bar stop/target ambiguity: mitigated by parity case asserting adverse-first stop outcome.
- R-009 - Execution truth ambiguity: mitigated; reference remains single PnL truth and fast path uses reference contracts.
- R-010 - Fast/reference divergence: mitigated by exact parity tests across summary, trades, equity, and fills.
- R-035 - Fast path used before parity: mitigated by representable certification and grid gate tests.
- R-036 - Fixture tests too trivial: mitigated by coverage for no-trade, long, short, costs, slippage fallback, stop, target, same-bar ambiguity, partial fallback, EOD, cooldown fallback, max holding fallback, trade summary, equity curve, and fail-closed behavior.
- R-013 / R-038 / R-039 - Heavy artifact, SQLite, Parquet/array commits: mitigated by artifact audits and explicit staging discipline.

## Known Limitations

- NumPy and Numba are optional and not installed in the current environment.
- The accelerated subset is single-instrument, single-session, and scoped to reference bar semantics listed above.
- Slippage-configured execution currently routes to reference fallback.
- Management features, including partial exits, cooldown, max holding bars, and management EOD exits, route to reference fallback.
- Passing fallback parity does not certify accelerated grid use.

## Review Focus

Review should focus on reference-truth preservation, parity adequacy, exact
same-bar adverse-first equivalence, fallback/fail-closed behavior, grid gate
strictness, optional NumPy/Numba dependency handling, artifact-policy
compliance, and ensuring the docs do not imply alpha, tradability, broker,
paper, live, or production execution scope.
