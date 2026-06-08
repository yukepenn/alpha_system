# FCFP-P06 Handoff

## Scope Completed

- Added the V1 liquidity-sweep / PA-structure fast pack:
  `src/alpha_system/features/fast/liquidity_pa_structure.py`.
- Wired the pack into `build_fast_feature_pack` and package exports.
- Added a tiny synthetic OHLCV fixture covering:
  leading insufficient prior windows, contiguous session reset, outside-opening-session
  rows, a no-trade/input-gap row, high/low sweeps, failed breakouts, frozen opening range,
  zero range, and valid range contraction.
- Added parity and materialization-provenance tests for all governed
  `StructureFeatureName` outputs.
- Updated the README campaign snapshot for FCFP-P06.

## Files For Ralph To Stage

No files were staged by Codex. The executor prompt explicitly forbade `git add`
and required all changes to remain unstaged.

Commit-eligible files changed or added for this phase:

- `src/alpha_system/features/fast/liquidity_pa_structure.py`
- `src/alpha_system/features/fast/packs.py`
- `src/alpha_system/features/fast/__init__.py`
- `tests/fixtures/feature_compute_fast_path/liquidity_pa_structure.py`
- `tests/unit/feature_compute_fast_path/test_liquidity_pa_structure_pack.py`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P06.md`

## Git Status

`git status --short` was not run. The executor prompt explicitly forbade
running `git status`, and that override superseded the generated spec handoff
template.

## Validation

- `python -m py_compile src/alpha_system/features/fast/liquidity_pa_structure.py src/alpha_system/features/fast/packs.py src/alpha_system/features/fast/__init__.py`
  - Result: PASS.
- `python -m pytest tests/unit/feature_compute_fast_path/test_liquidity_pa_structure_pack.py -q`
  - Result: PASS, 2 tests passed.
  - Note: initial isolated runs exposed two prepare-frame issues; both were fixed before final validation.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`
  - Result: PASS, 12 tests passed.
- `python tools/verify.py --smoke`
  - Result: PASS.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - Result: PASS, 12 tests passed.
- `git ls-files runs`
  - Result: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - Result: PASS, empty output.

Polars was present in the research environment, so the new parity tests ran
rather than skipping.

## Float Tolerance

The parity test uses `abs=1e-12` and `rel=1e-12` only for:

- `close_location_value`
- `wick_rejection_score`
- `range_contraction`

Reason: these features divide finite OHLC ranges, and `range_contraction` also
uses a prior mean range. The tolerance allows tiny binary floating-point ordering
differences between the reference Python arithmetic and Polars expressions.
Prior-distance, opening-range-distance, sweep flags, failed-breakout flags,
`available_ts`, gap rows, quality flags, and `feature_version_id` are asserted
exactly.

## Safety And Artifact Notes

- No reference-engine files were edited.
- No scaleout, CLI, broker, live, paper, execution, strategy, or backtest paths
  were touched.
- No real-data backfill or production registry write was run.
- No review artifact, `review.md`, `verdict.json`, PR, merge, commit, push, or
  staging action was created by Codex.
- The supplied run-local phase directory was not present in this worktree, so no
  run-local handoff was written. This commit-eligible handoff is the only handoff
  created for FCFP-P06.
