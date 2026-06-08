# FCFP-P05 Handoff

Summary: Added the V1 `regime_vol_compression` fast pack for governed ATR,
trendiness, and range-contraction features, wired it through the fail-closed
pack resolver, added synthetic reference-parity coverage, updated value-free
evidence/docs, and left all changes unstaged for Ralph.

## Files For Ralph To Stage

Codex did not run `git add`, `git commit`, `git push`, `git status`, or
`git diff` because the executor prompt explicitly prohibited them. Ralph should
stage only these commit-eligible paths:

- `src/alpha_system/features/fast/__init__.py`
- `src/alpha_system/features/fast/packs.py`
- `src/alpha_system/features/fast/regime_vol_compression.py`
- `tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py`
- `tests/fixtures/feature_compute_fast_path/regime_vol_compression.py`
- `tests/fixtures/feature_compute_fast_path/README.md`
- `research/feature_compute_fast_path_v1/README.md`
- `research/feature_compute_fast_path_v1/parity/regime_vol_compression/FCFP-P05_PARITY.md`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `docs/feature_compute_fast_path/PACK_MATERIALIZER.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P05.md`

No `runs/**` path, review artifact, verdict artifact, value artifact, SQLite
file, Parquet file, or heavy artifact is included in this list.

## Git Status

`git status --short` was not run. The executor prompt explicitly prohibited
`git status`; changes were left unstaged for Ralph.

## Scope Completed

- Added `src/alpha_system/features/fast/regime_vol_compression.py`.
- Registered the pack in `build_fast_feature_pack()` and exported its constants
  and builders from `alpha_system.features.fast`.
- Implemented Polars expressions for:
  - `base_ohlcv_atr`: true range with previous valid close plus rolling mean,
    including reset-on-session grouping and primitive gap flags.
  - `base_ohlcv_trendiness`: rolling efficiency ratio with
    `insufficient_window`, `input_gap`, and `zero_movement` branches.
  - `liquidity_structure_range_contraction`: current range versus exclusive
    prior-window mean range with structure-family no-trade and zero-range
    branches.
- Preserved reference feature identity through
  `FeatureVersion.derive(feature_spec)` for all declarations.
- Added a 12-row synthetic fixture with two session segments, reset warm-up, one
  no-trade row, flat-close `zero_movement` windows, and a valid post-reset
  range-contraction prior-window row.
- Added parity tests for values, `available_ts`, gap rows, quality flags,
  session-reset grouping, feature-version identity, and materialization
  provenance (`producer_engine_id` / `value_schema_version`).
- Added a value-free parity report under
  `research/feature_compute_fast_path_v1/parity/regime_vol_compression/`.
- Updated fast-path docs and the root README snapshot without marking the phase
  verdict.

## Parity Results

Fixture: `tests/fixtures/feature_compute_fast_path/regime_vol_compression.py`  
Rows: 12 synthetic OHLCV rows.  
Tolerance: ATR and trendiness use absolute/relative tolerance `1e-12` for
floating-point reductions. Range contraction is exact on this fixture.

| Feature | Rows | Valid value pairs | Gap rows | Max abs diff | Median abs diff | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `base_ohlcv_atr` | 12 | 6 | 6 | 0 | 0 | within `1e-12` |
| `base_ohlcv_trendiness` | 12 | 4 | 8 | 0 | 0 | within `1e-12` |
| `liquidity_structure_range_contraction` | 12 | 4 | 8 | 0 | 0 | exact |

Additional parity confirmations:

- `available_ts` parity: exact for all three features.
- Gap-row parity: exact for `insufficient_window`, `input_gap`, `no_trade`,
  `zero_movement`, primitive gap flags, and structure gap flags.
- Session-reset grouping: exact warm-up at the `RTH` to `ETH` boundary.
- `feature_version_id` equality: exact for all three features; no V1-specific
  identities are minted.

## Validation Results

- `test ! -e runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP`:
  PASS.
- `test ! -e runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P05/STOP`:
  PASS.
- `git status --short`: SKIPPED. Executor prompt forbids `git status`.
- Initial
  `python -m pytest tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py -q`:
  failed with a local helper `NameError` in `_structure_current_gap_flags`; fixed
  in scope.
- `python -m pytest tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py -q`:
  PASS, `2 passed in 0.27s`.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`:
  PASS, `10 passed in 0.44s`.
- `python tools/verify.py --smoke`: PASS, no output.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`:
  PASS, `12 passed in 0.13s`.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`: PASS, empty output.
- `git ls-files '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst'`:
  PASS, empty output.
- `python -m py_compile src/alpha_system/features/fast/regime_vol_compression.py src/alpha_system/features/fast/packs.py src/alpha_system/features/fast/__init__.py tests/fixtures/feature_compute_fast_path/regime_vol_compression.py tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py`:
  PASS, no output.

Polars was available in this environment; the parity tests did not skip.

## Artifact And Boundary Confirmation

- Codex left all changes unstaged for Ralph.
- Codex did not write a run-local handoff under `runs/**`.
- Codex did not create `review.md`, `verdict.json`, review artifacts, a PR, or a
  merge.
- No Parquet, SQLite, DB, Arrow, Feather, DBN, Zstd, raw/canonical data,
  provider response, feature value, label value, log, cache, or model artifact
  is listed for staging.
- Reference engine files were consumed read-only:
  `src/alpha_system/features/families/ohlcv/family.py`,
  `src/alpha_system/features/families/structure/family.py`, and
  `src/alpha_system/features/primitives/causal.py` were not edited.
- Resolver exact-id semantics, `FeatureStore`, and the registry write path were
  not weakened or bypassed.
- No live trading, paper trading, broker operation, order routing, external
  provider call, production deployment, destructive cleanup, profitability
  claim, or tradability claim was made.

Ralph owns staging, cached-diff audit, commit, review routing, verdict parsing,
PR, CI, merge gate, merge, and phase done-check.
