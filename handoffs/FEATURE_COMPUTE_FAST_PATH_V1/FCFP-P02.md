# FCFP-P02 Handoff

Summary: Implemented the V1 `base_ohlcv` Polars pack and fail-closed pack
resolver, added a 32-row synthetic parity fixture, gated all six governed Base
OHLCV features against the reference family, and recorded a value-free parity
report. Codex did not stage, commit, push, review, create a PR, or mark a phase
verdict.

## Files For Ralph To Stage

Codex did not run `git add`, `git commit`, `git push`, `git status`, or
`git diff` because the executor prompt explicitly prohibited them. Ralph should
stage only these commit-eligible paths:

- `src/alpha_system/features/fast/__init__.py`
- `src/alpha_system/features/fast/base_ohlcv.py`
- `src/alpha_system/features/fast/packs.py`
- `tests/unit/feature_compute_fast_path/test_base_ohlcv_pack.py`
- `tests/fixtures/feature_compute_fast_path/base_ohlcv.py`
- `tests/fixtures/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `docs/feature_compute_fast_path/PACK_MATERIALIZER.md`
- `research/feature_compute_fast_path_v1/README.md`
- `research/feature_compute_fast_path_v1/parity/base_ohlcv/FCFP-P02_PARITY.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P02.md`

No `runs/**` path, review artifact, value artifact, SQLite file, Parquet file,
or heavy artifact is included in this list.

## Scope Completed

- Added `build_base_ohlcv_pack()` under `src/alpha_system/features/fast/`.
- Added `build_fast_feature_pack()` as the V1 pack resolver; it currently
  resolves only the exact six-feature governed `base_ohlcv` pack and fails
  closed otherwise.
- Implemented Polars expressions for `returns`, `log_returns`,
  `rolling_volatility`, `rolling_range`, `range_position`, and
  `volume_zscore` with fixed `horizon=1`, `window=20`, `ddof=0`, and
  `reset_on_session=False`.
- Kept feature identity on the P01 path:
  `FastFeatureDeclaration.feature_version_id == FeatureVersion.derive(spec)`.
- Added a synthetic 32-row OHLCV fixture with one `no_trade` row to exercise
  first-window gaps, input-gap propagation, and post-gap recovery.
- Added parity tests for values, `available_ts`, gap rows, quality flags, and
  `feature_version_id` equality.
- Exercised `materialize_pack()` on a pytest temp root and confirmed the fast
  value-store wrapper records `producer_engine_id` and `value_schema_version`.
- Added a value-free parity report under
  `research/feature_compute_fast_path_v1/parity/base_ohlcv/`.
- Updated fast-path docs and the root README snapshot without marking the phase
  verdict.

## Parity Results

Fixture: `tests/fixtures/feature_compute_fast_path/base_ohlcv.py`  
Rows: 32 synthetic OHLCV rows.  
Tolerance: exact for five features; `volume_zscore` uses absolute tolerance
`5e-8`, justified by rolling-standard-deviation summation order. The referenced
full-year proof documented max `volume_zscore` drift around `3.3e-8`.

| Feature | Rows | Valid value pairs | Gap rows | Max abs diff | Median abs diff | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `returns` | 32 | 29 | 3 | 0 | 0 | exact |
| `log_returns` | 32 | 29 | 3 | 0 | 0 | exact |
| `rolling_volatility` | 32 | 6 | 26 | 0 | 0 | exact |
| `rolling_range` | 32 | 7 | 25 | 0 | 0 | exact |
| `range_position` | 32 | 7 | 25 | 0 | 0 | exact |
| `volume_zscore` | 32 | 7 | 25 | 3.9968028886505635e-15 | 1.9984014443252818e-15 | within `5e-8` |

Additional parity confirmations:

- `available_ts` parity: exact for all six features.
- Gap-row parity: exact for first-window gaps, the no-trade input gap, and
  post-gap recovery.
- Quality-flag parity: exact for all six features.
- `feature_version_id` equality: exact for all six features; no V1-specific
  identities are minted.

## Validation Results

- `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP`:
  succeeded, no output.
- `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P02/STOP`:
  succeeded, no output.
- `git status --short`: skipped. The executor prompt explicitly prohibits
  `git status`.
- Initial `python -m pytest tests/unit/feature_compute_fast_path/test_base_ohlcv_pack.py -q`:
  failed before repair. The failures were a rolling-volatility partial-window
  quality-flag mismatch and an over-broad synthetic registration assertion that
  hit FeatureRequest id drift during sequential temp-registry writes. Repairs
  were in scope: the rolling-volatility flags now carry source `input_gap`
  exactly, and the provenance test inspects the materialized value-store wrapper
  instead of forcing unrelated registry-gate churn.
- `python -m pytest tests/unit/feature_compute_fast_path/test_base_ohlcv_pack.py -q`:
  succeeded, `2 passed in 0.25s`.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`:
  succeeded, `5 passed in 0.32s`.
- `python tools/verify.py --smoke`: succeeded, no output.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`:
  succeeded, `12 passed in 0.13s`.
- `git ls-files runs`: succeeded, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: succeeded, empty output.
- `git ls-files '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst'`:
  succeeded, empty output.
- `rg -n "databento|ib_insync|IBKR|provider token|api[_-]?key|secret|read_parquet|\\.dbn|\\.zst|\\.feather" src/alpha_system/features/fast tests/unit/feature_compute_fast_path tests/fixtures/feature_compute_fast_path -S`:
  returned exit code 1 with no output, the expected no-match result for this
  boundary scan.

Polars was available in this environment; no Polars-absent skip occurred.

## Artifact And Boundary Confirmation

- Codex left all changes unstaged for Ralph.
- Codex did not write a run-local handoff under `runs/**`.
- Codex did not create `review.md`, `verdict.json`, review artifacts, a PR, or a
  merge.
- `runs/**` remains local-only and is not listed for staging.
- No Parquet, SQLite, DB, Arrow, Feather, DBN, Zstd, raw/canonical data,
  provider response, feature value, label value, log, cache, or model artifact is
  listed for staging.
- Reference engine files were consumed read-only:
  `src/alpha_system/features/families/**`,
  `src/alpha_system/features/primitives/causal.py`, and
  `src/alpha_system/features/engine/materialization.py` were not edited.
- No live trading, paper trading, broker operation, order routing, deployment,
  external provider call, profitability claim, or tradability claim was made.

Ralph owns staging, cached-diff audit, commit, review routing, verdict parsing,
PR, CI, merge gate, merge, and phase done-check.
