# FCFP-P01 Handoff

Summary: Added the P01 fast-path engine core, a reusable synthetic
reference-parity harness, documented the contract, and kept registry/value
operations local-only and routed through the official value-store plus
`FeatureStore` path.

## Files For Ralph To Stage

Codex did not stage files because the executor prompt explicitly prohibited
`git add`, `git commit`, `git push`, `git status`, and `git diff`. Ralph should
stage only these commit-eligible paths:

- `src/alpha_system/features/fast/__init__.py`
- `src/alpha_system/features/fast/materializer.py`
- `tests/unit/feature_compute_fast_path/__init__.py`
- `tests/unit/feature_compute_fast_path/parity_harness.py`
- `tests/unit/feature_compute_fast_path/test_pack_materializer_core.py`
- `tests/fixtures/feature_compute_fast_path/README.md`
- `tests/fixtures/feature_compute_fast_path/canonical_ohlcv_rows.json`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `docs/feature_compute_fast_path/PACK_MATERIALIZER.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P01.md`

No `runs/**` path, review artifact, value artifact, SQLite file, Parquet file,
or heavy artifact is included in this list.

## Git Status

`git status --short` was not run. The executor prompt explicitly prohibited
`git status`; changes were left unstaged for Ralph.

## Scope Completed

- Added `PackMaterializer`, `FastFeaturePack`, `FastFeatureDeclaration`, and
  `SymbolYearFrameRequest` under `src/alpha_system/features/fast/`.
- The fast engine loads a symbol-year OHLCV frame through the existing
  data-layer canonical loader supplied by the caller and caches one frame per
  request.
- Fast declarations compute values and quality flags as Polars expressions and
  convert outputs to `FeatureValueRecord` aligned by `event_ts` / `available_ts`.
- Fast feature identity is derived only with `FeatureVersion.derive(feature_spec)`.
  No V1-specific identity scheme was added.
- Value persistence writes through shared value-store helpers with default
  `ValueStoreFormat.DUAL` (Parquet plus JSONL audit output under
  `ALPHA_DATA_ROOT`).
- Registration goes through `FeatureStore.register_materialized_feature()` only.
  A process-local lock wraps pack registration to enforce serial registry writes;
  no manual SQLite rows are written.
- Fast-produced records carry `producer_engine_id` in registry metadata and
  lineage provenance, and `value_schema_version` through the value-store handle
  and registry metadata.
- Added a reusable parity helper under
  `tests/unit/feature_compute_fast_path/parity_harness.py`.
- Added a tiny documented synthetic OHLCV fixture under
  `tests/fixtures/feature_compute_fast_path/`.
- Added a test-only demonstrator fast declaration for Base OHLCV `returns` that
  compares against the reference family implementation for values,
  `available_ts`, gap rows, quality flags, and feature-version identity.
- Updated fast-path docs and the root README snapshot without marking P01 PASS.

## Validation Results

- `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/STOP`:
  PASS.
- `test ! -f runs/2026-06-08T160146Z_FEATURE_COMPUTE_FAST_PATH_V1/phases/FCFP-P01/STOP`:
  PASS.
- `git status --short`: SKIPPED. Executor prompt forbids `git status`.
- `python -m py_compile src/alpha_system/features/fast/__init__.py src/alpha_system/features/fast/materializer.py`:
  PASS, no output.
- `rg -n "read_parquet|pyarrow|databento|ib_insync|\\.dbn|\\.zst|\\.feather" src/alpha_system/features/fast src/alpha_system/features/__init__.py`:
  PASS, no matches.
- `PYTHONPATH=src python - <<'PY' ... import PackMaterializer ... PY`:
  PASS, output `PackMaterializer`.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`:
  PASS, `3 passed`.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`:
  PASS, `12 passed`.
- `python tools/verify.py --smoke`: PASS, no output.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst'`:
  PASS, empty output.

No checks were skipped for missing Polars; Polars was available in this
environment.

## Artifact And Boundary Confirmation

- `runs/**` remains local-only and was not written for this handoff.
- No Parquet, SQLite, DB, Arrow, Feather, DBN, Zstd, raw/canonical data,
  provider response, feature value, label value, log, cache, or model artifact was
  added to commit-eligible paths.
- The reference engine and primitives were read only:
  `src/alpha_system/features/primitives/causal.py`,
  `src/alpha_system/features/families/**`, and
  `src/alpha_system/features/engine/materialization.py` were not modified.
- Resolver exact-id semantics, keystone identity, `FeatureStore`, and
  `FeatureRegistry` serial-write semantics were not modified.
- `src/alpha_system/features/scaleout/driver.py` and
  `src/alpha_system/cli/scaleout.py` were not touched.
- No live trading, paper trading, broker operation, order routing, deployment,
  PR creation, merge, reviewer call, `review.md`, or `verdict.json` was created
  by Codex. Ralph owns review routing, verdict parsing, staging, commit, PR, CI,
  merge gate, and done-check.
