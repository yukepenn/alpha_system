# FCFP-P07 Handoff

## Scope Completed

- Added the V1 volume / activity fast pack:
  `src/alpha_system/features/fast/volume_activity.py`.
- Wired the pack into `build_fast_feature_pack` and package exports.
- Implemented the governed mixed primitive bindings selected by the reference
  volume/activity scaleout path:
  rolling volume, volume z-score, session minute, rolling range, range position,
  trendiness, close-location value, and wick rejection.
- Added a tiny synthetic OHLCV fixture covering leading insufficient windows, a
  no-trade/input-gap row, session-boundary reset behavior, a later valid
  reset-on-session rolling window, and a zero-range structure row.
- Added a synthetic parity test asserting values, `available_ts`, gap rows,
  quality flags, and reference `feature_version_id` identity.
- Updated the README snapshot and fast-path docs for P07.

## Files For Ralph To Stage

No files were staged by Codex. The executor prompt explicitly forbade `git add`
and required all changes to remain unstaged.

Commit-eligible files changed or added for this phase:

- `src/alpha_system/features/fast/volume_activity.py`
- `src/alpha_system/features/fast/packs.py`
- `src/alpha_system/features/fast/__init__.py`
- `tests/fixtures/feature_compute_fast_path/volume_activity.py`
- `tests/unit/feature_compute_fast_path/test_volume_activity_pack.py`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `docs/feature_compute_fast_path/PACK_MATERIALIZER.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P07.md`

Explicit staged file list: none.

## Git Status

`git status --short` was not run. The executor prompt explicitly forbade
running `git status`, and that override superseded the generated spec handoff
template.

## Validation

- `python -m pytest tests/unit/feature_compute_fast_path/test_volume_activity_pack.py -q`
  - Result: PASS, 1 test passed.
  - Note: an initial isolated run exposed an unsupported fixture-only
    `session_position` column; the fixture was fixed before final validation.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`
  - Result: PASS, 13 tests passed.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - Result: PASS, 12 tests passed.
- `python tools/verify.py --smoke`
  - Result: PASS, exit code 0 with no output.
- `git ls-files runs`
  - Result: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - Result: PASS, empty output.

Polars was present in the research environment, so the volume/activity parity
test ran rather than skipping. No Polars-absent env-only red was encountered.

## Float Tolerance

The parity test uses `abs=1e-12` and `rel=1e-12` only for finite floating-point
reductions and ratios:

- `base_ohlcv_volume_zscore`
- `base_ohlcv_rolling_range`
- `base_ohlcv_range_position`
- `base_ohlcv_trendiness`
- `liquidity_structure_close_location_value`
- `liquidity_structure_wick_rejection_score`

Reason: these features use rolling standard deviation, high/low reductions, or
OHLC ratio arithmetic; the Polars expression path can evaluate equivalent terms
in a different binary operation order from the Python reference path. Rolling
volume, session minute, `available_ts`, gap rows, quality flags, and
`feature_version_id` are asserted exactly.

## Safety And Artifact Notes

- No reference-engine files were edited.
- No governed primitive definitions, resolver exact-id semantics, registry
  write path, scaleout driver, CLI, broker, live, paper, execution, strategy,
  portfolio, management, L2, backtest, or agent-factory paths were touched.
- No real-data backfill, value materialization, production registry write,
  provider call, live/paper/broker operation, PR, merge, commit, push, or
  staging action was performed by Codex.
- No review artifact, `review.md`, or `verdict.json` was created by Codex.
- No `runs/**` handoff was written or staged; this commit-eligible handoff is
  the only handoff created for FCFP-P07.
