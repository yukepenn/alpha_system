# FCFP-P12 Handoff

Summary: implemented engine / value-schema versioning and value-free
reference-output reconciliation policy for `FEATURE_COMPUTE_FAST_PATH_V1`.
Changes are left unstaged for Ralph.

## Files For Ralph To Stage

Codex did not run `git add`, `git commit`, `git push`, `git status`, or
`git diff`. Ralph should stage only these commit-eligible paths:

- `src/alpha_system/features/registry.py`
- `src/alpha_system/features/store.py`
- `src/alpha_system/features/fast/__init__.py`
- `src/alpha_system/features/fast/materializer.py`
- `src/alpha_system/features/fast/reconciliation.py`
- `tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py`
- `tests/unit/feature_compute_fast_path/test_pack_materializer_core.py`
- `tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py`
- `docs/feature_compute_fast_path/ENGINE_PROVENANCE_RECONCILIATION.md`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `docs/feature_compute_fast_path/PACK_MATERIALIZER.md`
- `research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P12.md`

No `runs/**`, review artifact, verdict artifact, value artifact, SQLite file,
Parquet file, or heavy artifact is included.

## Implementation

- Added `producer_engine_id` as an additive feature registry record field and
  SQLite column, with backward-compatible schema backfill.
- Reference feature registrations default to
  `alpha_system.features.reference.materializer.v1`.
- Fast feature registrations pass
  `alpha_system.features.fast.pack_materializer.v1` through
  `FeatureStore.register_materialized_feature()`.
- `value_schema_version` remains sourced from the value-store handle.
- Producer provenance and value-schema version are emitted in registry record
  materialization metadata and remain excluded from `feature_version_id`.
- The label fast path remains on the existing label keystone path: fast label
  records carry producer/schema provenance through label registry metadata and
  lineage, with added assertions for metadata and `value_schema_version`.
- Added `alpha_system.features.fast.reconciliation`, which compares reference
  and V1 feature value records in memory or through
  `core.value_store.load_parquet_values()` and emits only value-free aggregate
  classifications.

## Identity Confirmation

The identity invariant is asserted by:

- `tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py::test_feature_store_records_reference_and_fast_provenance_without_changing_identity`

That test registers reference and V1 feature outputs through the official
keystone path and proves the same `feature_version_id` is preserved while
`producer_engine_id` differs. It also confirms the fast registry SQLite row
records `producer_engine_id` and `value_schema_version`.

The no-silent-mixing store guard is asserted by:

- `tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py::test_existing_reference_record_refuses_fast_overwrite_without_version_boundary`

## Reconciliation Policy And Classification

Policy:

- identical / within documented tolerance: keep the existing valid reference
  output, tag provenance, do not overwrite;
- beyond documented tolerance: block silent mixing; treat as a V1 bug, explicitly
  bump `value_schema_version`, or re-materialize through the official keystone
  path.

Value-free classification summary:

| Family / scope | Series | Compared fixture rows | Tolerance | Max abs diff | Median abs diff | Beyond rows | Decision |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| `base_ohlcv` full-window | 6 | 192 | exact except `volume_zscore` abs `5e-8` | `3.9968028886505635e-15` | `1.9984014443252818e-15` | 0 | keep reference, tag provenance |
| `vwap_session_auction` full-window | 5 | 60 | abs/rel `1e-12` for VWAP reductions | `2.842170943040401e-14` | `7.105427357601002e-15` | 0 | keep reference, tag provenance |
| `regime_vol_compression` full-window | 3 | 36 | abs/rel `1e-12` for reductions | `0` | `0` | 0 | keep reference, tag provenance |
| `liquidity_pa_structure` partial | 11 | 132 | abs/rel `1e-12` for ratios | `2.220446049250313e-16` | `0` | 0 | keep reference, tag provenance |
| `session_calendar_roll` 2024 | 10 | 80 | exact | `0` | `0` | 0 | keep reference, tag provenance |
| `volume_activity` 2024 | 8 | 376 | abs/rel `1e-12` for reductions/ratios | `2.220446049250313e-16` | `0` | 0 | keep reference, tag provenance |
| `bbo_tradability` 2024 | 15 | 150 | abs/rel `1e-12` for spread z-score | `0` | `0` | 0 | keep reference, tag provenance |
| `cross_market` 2024 | 11 | 110 | abs/rel `1e-12` for rolling beta/correlation | `0` | `0` | 0 | keep reference, tag provenance |

The durable summary is
`research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`.
It contains no per-row values.

## Validation

- `python tools/frontier/status_doctor.py`
  - Result: WARN only. No run dir with `state.json` exists in this worktree;
    runtime contract is consistent (`campaign.yaml` python 3.12 matches
    `pyproject.toml`).
- `git status --short`
  - Skipped. The executor prompt explicitly forbade running `git status`.
- `python -m py_compile src/alpha_system/features/registry.py src/alpha_system/features/store.py src/alpha_system/features/fast/materializer.py src/alpha_system/features/fast/reconciliation.py tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py`
  - PASS.
- `python -m pytest tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py -q`
  - PASS: `4 passed`.
- `python -m py_compile src/alpha_system/features/registry.py src/alpha_system/features/store.py src/alpha_system/features/fast/materializer.py src/alpha_system/features/fast/reconciliation.py src/alpha_system/features/fast/__init__.py tests/unit/feature_compute_fast_path/test_pack_materializer_core.py tests/unit/feature_compute_fast_path/test_fixed_horizon_label_pack.py tests/unit/feature_compute_fast_path/test_engine_provenance_reconciliation.py`
  - PASS.
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`
  - PASS: `24 passed`.
- `test -f research/feature_compute_fast_path_v1/reconciliation/reconciliation_summary.md`
  - PASS.
- `python tools/verify.py --smoke`
  - PASS, no output.
- `python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - PASS: `12 passed`.
- `python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed.
- `git ls-files runs && git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`
  - PASS, empty output.

## Artifact And Registry Safety

- No real full-window backfill or real re-materialization was run.
- No existing output was deleted or overwritten.
- No manual SQLite write was performed.
- Real local registries under `$ALPHA_DATA_ROOT` were not touched; no backup was
  attempted because this executor did not perform registry-touching work against
  the real data root.
- Tests used pytest temp directories for temporary value stores and registries.
- No run-local handoff was written because the supplied `runs/.../FCFP-P12`
  directory is absent in this worktree.
- No `review.md`, `verdict.json`, PR, merge, commit, push, staging action,
  broker/live/paper operation, external provider call, or production deployment
  was performed by Codex.

Ralph owns staging, cached-diff audit, commit, review routing, verdict parsing,
PR, CI, merge gate, merge, and phase done-check.
