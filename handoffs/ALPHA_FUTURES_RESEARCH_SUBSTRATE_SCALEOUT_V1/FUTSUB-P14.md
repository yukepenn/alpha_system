# FUTSUB-P14 Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P14` - FeaturePack Registry Integration, Coverage Audit, and Resolver Smoke  
Executor: Codex  
Date: 2026-06-09

## Scope Completed

Materialized and integrated the eight governed FeaturePack families on the V1
fast producer substrate:

- `base_ohlcv`
- `session_calendar_maintenance`
- `vwap_session_auction`
- `regime_volatility_compression`
- `liquidity_sweep_pa_structure`
- `volume_activity`
- `bbo_tradability_top_book`
- `cross_market_alignment`

Bounded-real 2024 was run before full-window expansion. Full-window scope is
the accepted/warned 2019-2026 window; blocked 2018 DatasetVersions remain
excluded. Per-symbol families cover ES/NQ/RTY accepted units; cross-market
registers one ES/NQ/RTY aligned panel unit per accepted year.

Current value-free coverage summaries report:

| Family | Accepted units | Current summary completed | Current summary skipped | Failed |
| --- | ---: | ---: | ---: | ---: |
| `base_ohlcv` | 24 | 21 | 3 | 0 |
| `session_calendar_maintenance` | 24 | 0 | 24 | 0 |
| `vwap_session_auction` | 24 | 21 | 3 | 0 |
| `regime_volatility_compression` | 24 | 21 | 3 | 0 |
| `liquidity_sweep_pa_structure` | 24 | 0 | 24 | 0 |
| `volume_activity` | 24 | 21 | 3 | 0 |
| `bbo_tradability_top_book` | 24 | 0 | 24 | 0 |
| `cross_market_alignment` | 8 | 0 | 8 | 0 |

The zero-completed/skipped summaries are reruns after the initial materialized
wave; those units skipped from checkpoint plus registry truth.

## Registry And Resolver Evidence

Registry consistency audit: `research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`

- Overall status: `PASS`
- Producer provenance: `alpha_system.features.fast.pack_materializer.v1`
- Value schema: `alpha_system.features.fast.values.v1`
- Store format: Parquet-backed rows with matching sidecar hashes
- Registry rows: 1,408 total across the eight families
- No reference/V1 mixing detected within the audited series

Resolver smoke: `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`

- Overall status: `PASS`
- Representative exact `fver_...` locks resolved for all eight families
- Resolved handles matched DatasetVersion, FeatureRequest id, and partition
- Parquet sidecar hash checks passed for representative rows
- Absent exact lock failed closed with `feature_pack_not_found`

## Repairs Made

Minimal materialization/resolver-blocking repairs were needed:

- `src/alpha_system/features/scaleout/driver.py`
  - Rebuilt live-registry declarations by exact `feature_version_id` for V1 serial registration, so multi-declaration and overlapping-selector packs register the intended member without request-id drift.
  - Added V1 worker manifest resume support that rebuilds registry-side materialization evidence from Parquet sidecars without re-reading canonical values.
  - Review repair F1: persists the generic `session_metadata_role: SESSION_METADATA_POINT_IN_TIME` registry marker for `session_calendar_maintenance`, `liquidity_sweep_pa_structure`, and `cross_market_alignment`, and routes V1 worker-job metadata through the shared `_v1_registry_metadata` helper.
  - Preserved the existing fake-result unit-test contract for materializer registration.
- `src/alpha_system/features/fast/vwap_session_auction.py`
  - Supported `session_minute` for the FUTSUB VWAP/session auction binding while preserving the legacy exported default feature-id tuple.
- `src/alpha_system/features/fast/regime_vol_compression.py`
  - Supported `base_ohlcv_returns` and `base_ohlcv_rolling_range` for FUTSUB regime bindings while preserving the legacy exported default feature-id tuple.
- `src/alpha_system/features/fast/bbo_tradability.py`
  - Honored the declared spread-zscore rolling window instead of a fixed module default.
- `src/alpha_system/features/fast/bbo_tradability.py`
- `src/alpha_system/features/fast/cross_market_panel.py`
- `src/alpha_system/features/fast/liquidity_pa_structure.py`
- `src/alpha_system/features/fast/regime_vol_compression.py`
- `src/alpha_system/features/fast/session_calendar_roll.py`
- `src/alpha_system/features/fast/vwap_session_auction.py`
- `src/alpha_system/features/fast/volume_activity.py`
  - Normalized null quality-flag columns before list fill operations.
- `src/alpha_system/runtime/input_resolver.py`
  - Review repair F1: removed the hardcoded FUTSUB campaign/family exemption from the shared no-lookahead guard. The resolver now converts only explicit generic `session_metadata_role: SESSION_METADATA_POINT_IN_TIME` metadata into ordinary `SESSION_METADATA` field roles; arbitrary unrole-tagged live feature inputs remain fail-closed.

## Commit-Eligible Files For Ralph

- `README.md`
- `docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
- `research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`
- `research/futures_substrate_scaleout_v1/feature_packs/base_ohlcv/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/session_calendar_maintenance/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/vwap_session_auction/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/regime_volatility_compression/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/liquidity_sweep_pa_structure/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/volume_activity/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/bbo_tradability_top_book/coverage_summary.md`
- `research/futures_substrate_scaleout_v1/feature_packs/cross_market_alignment/coverage_summary.md`
- `tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/fast/bbo_tradability.py`
- `src/alpha_system/features/fast/cross_market_panel.py`
- `src/alpha_system/features/fast/liquidity_pa_structure.py`
- `src/alpha_system/features/fast/regime_vol_compression.py`
- `src/alpha_system/features/fast/session_calendar_roll.py`
- `src/alpha_system/features/fast/vwap_session_auction.py`
- `src/alpha_system/features/fast/volume_activity.py`
- `src/alpha_system/runtime/input_resolver.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`

No review artifact was created by this executor, per instruction. Ralph/reviewer
own review, verdict, staging, commit, PR, CI, merge, and phase PASS decisions.

## Validation

- `git status --short`: run during repair; working tree contains the P14
  commit-eligible files plus this F1 repair, with no staged files.
- `python tools/verify.py --smoke`: PASS.
- `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 4 passed.
- `python -m pytest tests/no_lookahead/test_session_label_guard.py tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 19 passed.
- Review-repair focused rerun of `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py tests/no_lookahead/test_session_label_guard.py -q`: PASS, 19 passed.
- Repair-local read-only representative-lock check with `PYTHONPATH=src`:
  base/session/VWAP/regime representative rows resolved under the repaired
  guard; existing local liquidity/cross-market registry rows still lack the new
  generic `session_metadata_role` marker and fail with `label_as_feature_input`.
  This repair did not mutate local SQLite; rerun/re-register those rows through
  the patched V1 driver before regenerating resolver-smoke evidence.
- Focused source-regression set for V1 registration, VWAP, regime, and FUTSUB scaleout tests: PASS, 8 passed.
- Checkpoint/resolver guard focused set: PASS, 22 passed.
- `python tools/verify.py --lint`: exit 0 with environment skip, `ruff is not installed`.
- `python tools/verify.py --typecheck`: PASS, compileall completed.
- `python tools/verify.py --test`: FAIL, 2970 passed / 4 failed.
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`: tuple/list assertion mismatch.
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`: tuple/list assertion mismatch.
  - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`: fixture JSONL rows empty.
  - `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`: local `ALPHA_DATA_ROOT` env changes expected storage root.
- `python tools/hooks/canary_runner.py`: PASS, all Frontier canaries passed.
- `test -f research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`: PASS.
- `test -f docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`: PASS.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`: PASS, empty output.

## Notes

Local-only values, SQLite registries, checkpoints, backups, and run artifacts
remain under `ALPHA_DATA_ROOT` or `runs/**`. Nothing was staged or committed by
this executor. No broker, live, paper, order-routing, deployment, provider-call,
alpha, profitability, tradability, or capital-allocation work was performed.
