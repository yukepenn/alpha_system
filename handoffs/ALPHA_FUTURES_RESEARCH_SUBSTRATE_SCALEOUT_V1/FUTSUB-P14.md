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
- Registry rows: 1,360 trusted current-config rows audited across the eight
  families; 48 offline-only session roll-countdown registry rows remain
  local-only but are not certified by the trusted substrate audit
- Required generic `session_metadata_role` markers are present for trusted
  session/liquidity/cross-market rows
- No reference/V1 mixing detected within the audited series

Resolver smoke: `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`

- Overall status: `PASS`
- Representative exact `fver_...` locks resolved for all eight trusted
  current-config families
- Session representative is `session_calendar_roll_session_id`; the offline-only
  `bars_to_roll`/`minutes_to_roll` rows are not used as resolver-smoke evidence
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

## REWORK Repair Attempt

Review finding repaired: `src/alpha_system/features/fast/regime_vol_compression.py`
`_returns_expression` now detects reset-on-session boundary rows with an
available prior row in a different session segment and emits the reference
oracle's `("primitive_gap", "session_reset")` flag shape, with source-row
quality flags preserved and sorted. Feature values are unchanged; the branch
only replaces the stale `("insufficient_window", "primitive_gap")` flag on
session-reset rows.

Reference-parity coverage added:

- `tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py`
  covers `base_ohlcv_returns` and `base_ohlcv_rolling_range` through the regime
  fast pack with `reset_on_session=True` on the multi-session fixture, using
  `assert_feature_records_match` for value and `quality_flags` parity.
- `tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py`
  covers `base_ohlcv_session_minute` through the VWAP/session-auction fast pack
  on the multi-session fixture, using `assert_feature_records_match`.

Affected already-materialized `base_ohlcv_returns` FeatureVersion ids
(`momentum_reversion_state`; 24 accepted full-window units) are:

| Year | Symbol | FeatureVersion id |
| ---: | --- | --- |
| 2019 | `ES` | `fver_01471d627567885984a20a18a7291e2cbeaf5e6f525cfd76cfe5d89b496b3533` |
| 2019 | `NQ` | `fver_85768925efb86b774fad339e6d74d1a213e556732ce282e1379e656cfdd90773` |
| 2019 | `RTY` | `fver_8320c8b78315b295cf5e21c1d18d0134b47a29cb56f50be320953a13f86e62ef` |
| 2020 | `ES` | `fver_e367d2e7ea0d88cad44784e4a714f16e887eef6f3cb272865d7334e0dff16126` |
| 2020 | `NQ` | `fver_24db3f7fb5fc9c6a5966c0217506d1ff64bcbd92dea1133a12888cb70ec635eb` |
| 2020 | `RTY` | `fver_1d2ca59d7301ee6bc8a1f62de3a5d433c370f00af11c4b2b309a0a6d6fd460ba` |
| 2021 | `ES` | `fver_0c08fc066291dfd473c4f4cf461aa9903b4b8233f0cde2f2a39df973e3206356` |
| 2021 | `NQ` | `fver_5c7ae33eb8e4703251da4ec48268395711f258acf615e4c901f0be00bd7371f7` |
| 2021 | `RTY` | `fver_391646a6f2435c2099a5b8642f29b4e3360987e82b710ce8e6280a6ff57dcb79` |
| 2022 | `ES` | `fver_cc09751e055ced5b81c9684d159ad117860c249331759f4abb94b86947fd0b61` |
| 2022 | `NQ` | `fver_c97b89b46c5cd97451306eb20fdd8ceba6ca2678bcf9db474175342a2e57b315` |
| 2022 | `RTY` | `fver_7a6d9095f02d63fe7311a9d0f457d0ec7a87ba708a67c94272616f96c32fcaa9` |
| 2023 | `ES` | `fver_26aad2f9533efc5b98dfea724c8b8160e3b59e367e1738fe92cc5e190d330935` |
| 2023 | `NQ` | `fver_7ae926c7b432c6b17b20a4fa579a314f215dbb3bcf2fbd8bfdefd91a6436ee15` |
| 2023 | `RTY` | `fver_97abd18f1a1b2fb75e33bab1a764a4785dbd360d2809468762424dc8d96023e9` |
| 2024 | `ES` | `fver_bb016b77709e32d912ec2c35b1b3a23fc024a5c18c3b29dc0dddd8ddb033be5b` |
| 2024 | `NQ` | `fver_45b9368c5bf75420427be641a6468c62c7b503eeddf6e5130121335bb118b948` |
| 2024 | `RTY` | `fver_32a511e5f0336e70c1349a0c586d20fa6395139ea3bfea63f1d7e14c066257f8` |
| 2025 | `ES` | `fver_42c802e79b33dce1430df449a0888c625388f0b460137450fc4793a118ccd874` |
| 2025 | `NQ` | `fver_090f786e75e83a2ca36937a8d8c93822d57208ba7abef39a930831dbc421d2d4` |
| 2025 | `RTY` | `fver_360b9887edcd2baedb683a79048127aae1bb3010fe5d2ddd796a0925cf15d8f5` |
| 2026 | `ES` | `fver_6d6da5d527dfa1e55c636988fea758a0e735fda5dc0ee6954bec033f7cf059f2` |
| 2026 | `NQ` | `fver_0e1316dffcb840bc0d8aeda5c9bd9b76116f349769a6e9d8e8f54bbfe62ce5e0` |
| 2026 | `RTY` | `fver_6300441ac8edda664cb2bdab4853ecd4948eeed7d2055f3325e27ec745ebb350` |

REWORK repair completed: this repair attempt re-materialized through the patched
V1 driver. The targeted `momentum_reversion_state` recompute completed 24/24
units, then a full `regime_volatility_compression` force-recompute completed
24/24 units because the family writes a shared per-unit Parquet sidecar and all
five current-config regime rows needed current sidecar hashes. Final regenerated
registry/resolver evidence no longer requires coordinator rematerialization for
these rows.

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
- `tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py`
- `tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py`
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
own review, verdict, PR, CI, merge, and phase PASS decisions. Explicit
repair-path staging/commit actions are recorded in the bounded repair sections
below.

## Validation

- `git status --short`: run during repair; working tree contains the P14
  commit-eligible files plus this F1 repair, with no staged files.
- `python tools/verify.py --smoke`: PASS.
- `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 4 passed.
- `python -m pytest tests/no_lookahead/test_session_label_guard.py tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 19 passed.
- Review-repair focused rerun of `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py tests/no_lookahead/test_session_label_guard.py -q`: PASS, 19 passed.
- Repair-local representative-lock check with `PYTHONPATH=src`:
  base/session/VWAP/regime representative rows resolved under the repaired
  guard. Superseded by the final REWORK evidence-regeneration attempt below,
  which reran and re-registered liquidity/cross-market rows through the patched
  V1 driver so the generic `session_metadata_role` markers are present.
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

Review REWORK repair validation:

- `python -m pytest tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py -q`: PASS, 6 passed.
- `python tools/verify.py --smoke`: PASS.
- `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 4 passed.
- `python tools/verify.py --lint`: exit 0 with environment skip, `ruff is not installed`.
- `python tools/verify.py --typecheck`: PASS, compileall completed.
- `python tools/hooks/canary_runner.py`: PASS, all Frontier canaries passed.
- `python tools/verify.py --test`: FAIL, 2972 passed / 4 failed.
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`: tuple/list assertion mismatch.
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`: tuple/list assertion mismatch.
  - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`: fixture JSONL rows empty.
  - `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`: local `ALPHA_DATA_ROOT` env changes expected storage root.
- `test -f research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`: PASS.
- `test -f docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`: PASS.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`: PASS, empty output.
- Explicit repair commit file list:
  - `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`
  - `src/alpha_system/features/fast/regime_vol_compression.py`
  - `tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py`
  - `tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py`
- `git status --short` before explicit staging:
  - `M handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`
  - `M src/alpha_system/features/fast/regime_vol_compression.py`
  - `M tests/unit/feature_compute_fast_path/test_regime_vol_compression_pack.py`
  - `M tests/unit/feature_compute_fast_path/test_vwap_session_auction_pack.py`

## Bounded Repair Attempt - Force Recompute Capability

Review finding repaired: the scaleout driver now has a sanctioned
force-recompute capability for targeted units whose `feature_version_id` identity
is unchanged but whose recomputed value `content_hash` differs from the existing
registry row.

Implemented behavior:

- `alpha scaleout feature-pack --force-recompute` and
  `ALPHA_SCALEOUT_FORCE_RECOMPUTE` route to `run_scaleout(...,
  force_recompute=True)`.
- Forced runs bypass completed-unit checkpoint resume, registry-completed resume,
  and V1 worker-manifest resume so the targeted unit is recomputed.
- V1 serial registration compares the recomputed value-store `content_hash` with
  the existing registry row's `value_content_hash`.
- Matching hashes reuse the existing registry row and remain idempotent.
- Mismatched hashes re-register the existing `FeatureSpec`, `FeatureVersion`,
  lineage, and approved request payload through
  `FeatureStore.register_materialized_feature`, preserving
  `feature_version_id` identity and updating the registry row in place.

Repair file list:

- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/cli/scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py`
- `tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py`
- `tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`

## Bounded Repair Attempt - No-Lookahead Substrate Follow-up

Authoritative Yellow review required three follow-up repairs. This attempt
kept scope to those findings and did not mutate local registries, Parquet values,
run-local artifacts, review artifacts, verdicts, PRs, or merge state.

Repairs made:

- Finished the force-recompute unit coverage in
  `tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`.
  The test now proves a forced V1 recompute reuses exact existing registry
  `FeatureSpec`/request payloads, skips re-registration when the recomputed
  `content_hash` matches, and re-registers through
  `FeatureStore.register_materialized_feature` when the hash differs.
- Marked `session_calendar_roll_bars_to_roll` and
  `session_calendar_roll_minutes_to_roll` as offline-only/non-causal definitions
  in `src/alpha_system/features/families/session/family.py`, while preserving
  offline compute availability.
- Removed `bars_to_roll` and `minutes_to_roll` from the trusted FUTSUB
  `session_calendar_maintenance` scaleout config so they are no longer selected
  for causal substrate materialization/registration.
- Added session scaleout guards in `src/alpha_system/features/scaleout/driver.py`
  so offline/non-causal session specs fail closed if a future config or targeted
  call attempts to materialize them as trusted substrate features.
- Enforced `alignment_policy=strict_intersection` for
  `cross_market_alignment` substrate specs in the scaleout driver, and added a
  lower-level cross-market fast-pack guard keyed to FUTSUB substrate metadata so
  `asof` cannot silently enter substrate materialization.

Repair file list for this attempt:

- `configs/features/scaleout/session_calendar_maintenance.json`
- `src/alpha_system/features/families/session/family.py`
- `src/alpha_system/features/fast/cross_market_panel.py`
- `src/alpha_system/features/fast/session_calendar_roll.py`
- `src/alpha_system/features/scaleout/driver.py`
- `tests/unit/feature_compute_fast_path/test_cross_market_pack.py`
- `tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`
- `tests/unit/features/families/session/test_session_family.py`
- `tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`

Validation for this attempt:

- `python -m pytest tests/unit/features/families/session/test_session_family.py tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py tests/unit/futures_substrate_scaleout/features/test_session_scaleout.py -q`: PASS, 14 passed.
- `python -m pytest tests/unit/feature_compute_fast_path/test_cross_market_pack.py tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py -q`: PASS, 16 passed.
- `python tools/verify.py --smoke`: PASS.
- `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 4 passed.
- `python tools/verify.py --lint`: exit 0 with environment skip, `ruff is not installed; run pip install -e ".[dev]" to enable lint. Skipping.`
- `python tools/verify.py --typecheck`: PASS, compileall completed.
- `python tools/hooks/canary_runner.py`: PASS, all Frontier canaries passed.
- `python tools/verify.py --test`: FAIL, 4 failed / 2979 passed. The failures are outside this repair scope:
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`: tuple/list assertion mismatch.
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`: tuple/list assertion mismatch.
  - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`: fixture JSONL rows empty.
  - `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`: local `ALPHA_DATA_ROOT` env changes expected storage root.
- `test -f research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`: PASS.
- `test -f docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`: PASS.
- `git diff --check`: PASS.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`: PASS, empty output.
- `python tools/frontier/status_doctor.py`: WARN, no live run dir with `state.json` found for the active campaign; runtime contract is consistent.

`git status --short` before explicit staging contained only the repair files
listed above. No `runs/` path or heavy/value artifact was staged or committed.

Validation for this bounded repair:

- `python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py -q`: PASS, 10 passed.
- `python tools/verify.py --smoke`: PASS.
- `python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 4 passed.
- `python tools/verify.py --lint`: exit 0 with environment skip, `ruff is not installed`.
- `python tools/verify.py --typecheck`: PASS, compileall completed.
- `python tools/hooks/canary_runner.py`: PASS, all Frontier canaries passed.
- `python tools/verify.py --test`: FAIL, 2975 passed / 4 failed.
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`: tuple/list assertion mismatch.
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`: tuple/list assertion mismatch.
  - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`: fixture JSONL rows empty.
  - `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`: local `ALPHA_DATA_ROOT` selects the alpha-data cache root.
- `test -f research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`: PASS.
- `test -f docs/futures_substrate_scaleout/FEATURE_INTEGRATION.md`: PASS.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`: PASS, empty output.
- `git diff --cached --name-only`: PASS, empty output; no staged files.

`git status --short` before staging this repair:

- `M handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`
- `M src/alpha_system/cli/scaleout.py`
- `M src/alpha_system/features/scaleout/driver.py`
- `M tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py`
- `M tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`
- `M tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py`

## Bounded Repair Attempt - Evidence Regeneration After REWORK

Review findings repaired:

- B1: regenerated `feature_resolver_smoke.md` no longer certifies
  `session_calendar_roll_bars_to_roll`; the trusted session representative is
  `session_calendar_roll_session_id`.
- B2: re-materialized/re-registered the stale local V1 rows through the patched
  scaleout driver, then regenerated registry/resolver evidence against the
  current code and local registry state.

Local materialization performed through the patched V1 driver:

- `regime_volatility_compression`: targeted `momentum_reversion_state`
  force-recompute completed 24/24 units; superseded by full-family
  force-recompute completed 24/24 units to bring all shared sidecar hashes
  current.
- `liquidity_sweep_pa_structure`: full-family force-recompute completed 24/24
  units and re-registered rows with the generic session metadata marker.
- `cross_market_alignment`: full-family force-recompute completed 8/8 units and
  re-registered rows with the generic session metadata marker.

Minimal driver repair for this attempt:

- `src/alpha_system/features/scaleout/driver.py` now thaws an existing
  `FrozenJsonMapping` feature request payload with `to_dict()` before passing it
  back through `FeatureStore.register_materialized_feature` during forced
  existing-`FeatureVersion` updates. This preserves the official keystone
  registry path and fixes the registration replay failure encountered during
  recompute.
- `tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`
  covers that replay path with a frozen existing request payload.

Regenerated evidence:

- `research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`:
  PASS, 1,360 trusted current-config rows audited, 48 offline-only session
  roll-countdown rows excluded from trusted certification, no issues.
- Session/liquidity/cross-market marker coverage in the audit:
  `192/192`, `216/216`, and `88/88`, respectively.
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`:
  PASS, eight trusted representative locks resolved to Parquet-backed rows, and
  absent exact lock failed closed with `feature_pack_not_found`.

Repair file list for this attempt:

- `src/alpha_system/features/scaleout/driver.py`
- `tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`
- `research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`
- `research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`

Validation for this attempt:

- `PYTHONPATH=src python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py::test_v1_force_recompute_reuses_existing_specs_and_updates_only_stale_hash -q`: PASS, 1 passed.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/features/test_feature_resolver_smoke.py -q`: PASS, 4 passed.
- `git diff --check`: PASS.
- `python tools/verify.py --smoke`: PASS.
- `python tools/verify.py --lint`: exit 0 with environment skip, `ruff is not installed; run pip install -e ".[dev]" to enable lint. Skipping.`
- `python tools/verify.py --typecheck`: PASS, compileall completed.
- `python tools/hooks/canary_runner.py`: PASS, all Frontier canaries passed.
- `python tools/verify.py --test`: FAIL, 4 failed / 2979 passed. The failures are outside this repair scope:
  - `tests/integration/test_duckdb_query_fixture.py::test_duckdb_query_over_tiny_csv_fixture`: tuple/list assertion mismatch.
  - `tests/integration/test_polars_lazy_fixture.py::test_polars_lazy_transformation_over_tiny_fixture`: tuple/list assertion mismatch.
  - `tests/unit/data/test_databento_canonicalize.py::test_databento_canonicalize_quality_coverage_and_register_offline`: fixture JSONL rows empty.
  - `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`: local `ALPHA_DATA_ROOT` selects the alpha-data cache root.
- `git ls-files runs`: PASS, empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`: PASS, empty output.
- `git diff --cached --name-only`: PASS before staging, empty output.
- `python tools/frontier/status_doctor.py`: WARN, no live run dir with
  `state.json` found for the active campaign; runtime contract is consistent.

`git status --short` before explicit staging for this attempt:

- `M handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P14.md`
- `M research/futures_substrate_scaleout_v1/feature_packs/feature_resolver_smoke.md`
- `M research/futures_substrate_scaleout_v1/feature_packs/registry_consistency_audit.md`
- `M src/alpha_system/features/scaleout/driver.py`
- `M tests/unit/feature_compute_fast_path/test_scaleout_v1_engine_integration.py`

## Notes

Local-only values, SQLite registries, checkpoints, backups, and run artifacts
remain under `ALPHA_DATA_ROOT` or `runs/**`. No review artifact, verdict, PR,
merge, phase PASS, broker, live, paper, order-routing, deployment,
provider-call, alpha, profitability, tradability, or capital-allocation work was
performed.
