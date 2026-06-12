# P085900_CALIBRATION_STAGING_INTEGRITY Handoff

## Scope

Implemented the real-data surrogate calibration staging integrity fix for
`tools/discovery_rigor_floor/run_real_surrogate_calibration.py`.

The coordinator now stages every declared factor lock in the StudySpec's one
non-support feature family for every matching declared primary-horizon label
partition. It no longer chooses a feature via arbitrary ordering. Ambiguous
declared factor family state fails closed with `declared_factor_family_ambiguous`;
missing/duplicate per-partition locks fail closed.

## Runtime Factor Derivation Reused

Runtime path found and reused:

`alpha_system.governance.surrogate_run.run_surrogate_study`
-> `_surrogate_scope`
-> `_study_config_for_surrogate`
-> `study_config_for_surrogate_scope`
-> `StudyConfig.from_mapping`

`study_config_for_surrogate_scope` is a pure extraction from the prior private
runtime helper. The original `_study_config_for_surrogate` still calls it, so
runtime behavior is unchanged. The calibration coordinator builds each staged
surrogate StudySpec, calls `study_config_for_surrogate_scope`, and verifies the
runtime `StudyConfig.factor_id` matches the staged lock's declared `feature_id`.

## Integrity Guards

- Feature staging filters rows by locked `feature_version_id`.
- Label staging filters rows by locked `label_version_id`.
- Resolved registry records must match lock `version_id`, `dataset_version_id`,
  and `partition`.
- Feature records must match the lock's declared `feature_id`.
- Value-store content hashes are verified before loading rows through
  `alpha_system.governance.feature_lock_validation.verify_registered_value_store_content_hash`.
  That helper uses the shared value-store primitives:
  `read_parquet_manifest` for Parquet/Dual stores and
  `compute_value_content_hash` for JSONL stores.
- Hash mismatch raises a fail-closed error naming the path plus expected and
  actual hashes.
- Reports include counts only: declared factor count, declared label pack count,
  staged sub-config count, total/staged feature and label rows, and off-grid
  label `event_ts` counts.
- Rescore mode does not resolve or stage values; it reuses the derived sub-config
  count only to preserve seed-grid parity.

## Six Rerun StudySpecs

Primary horizon used by the coordinator for these committed rerun StudySpecs:
`5m`. Each resolves to 24 locked `5m` label packs.

| StudySpec | Declared feature family | Declared factors | Sub-configs |
|---|---|---:|---:|
| `sspec_652fcc23a6f725b405612b8e` | `vwap_session_auction` | 6 | 144 |
| `sspec_676a012a4a4cdf3d169cd981` | `vwap_session_auction` | 6 | 144 |
| `sspec_1d87dfbe3d24810720f75014` | `regime_volatility_compression` | 5 | 120 |
| `sspec_c2114a3c6c90595350151af0` | `liquidity_sweep_pa_structure` | 9 | 216 |
| `sspec_950ad6bb7063928d9ff8ea4f` | `liquidity_sweep_pa_structure` | 9 | 216 |
| `sspec_6088f0ed5b02b161bfb54943` | `bbo_tradability_top_book` | 11 | 264 |

Declared factor IDs in StudySpec lock order:

- `sspec_652fcc23a6f725b405612b8e`: `base_ohlcv_vwap`,
  `base_ohlcv_anchored_vwap`, `base_ohlcv_distance_to_vwap`,
  `base_ohlcv_opening_range`, `base_ohlcv_overnight_range`,
  `base_ohlcv_session_minute`.
- `sspec_676a012a4a4cdf3d169cd981`: `base_ohlcv_vwap`,
  `base_ohlcv_anchored_vwap`, `base_ohlcv_distance_to_vwap`,
  `base_ohlcv_opening_range`, `base_ohlcv_overnight_range`,
  `base_ohlcv_session_minute`.
- `sspec_1d87dfbe3d24810720f75014`: `base_ohlcv_trendiness`,
  `base_ohlcv_atr`, `liquidity_structure_range_contraction`,
  `base_ohlcv_rolling_range`, `base_ohlcv_returns`.
- `sspec_c2114a3c6c90595350151af0`: `liquidity_structure_prior_high_distance`,
  `liquidity_structure_prior_low_distance`, `liquidity_structure_sweep_high_flag`,
  `liquidity_structure_sweep_low_flag`,
  `liquidity_structure_failed_high_breakout_flag`,
  `liquidity_structure_failed_low_breakout_flag`,
  `liquidity_structure_close_location_value`,
  `liquidity_structure_wick_rejection_score`,
  `liquidity_structure_range_contraction`.
- `sspec_950ad6bb7063928d9ff8ea4f`: `liquidity_structure_prior_high_distance`,
  `liquidity_structure_prior_low_distance`, `liquidity_structure_sweep_high_flag`,
  `liquidity_structure_sweep_low_flag`,
  `liquidity_structure_failed_high_breakout_flag`,
  `liquidity_structure_failed_low_breakout_flag`,
  `liquidity_structure_close_location_value`,
  `liquidity_structure_wick_rejection_score`,
  `liquidity_structure_range_contraction`.
- `sspec_6088f0ed5b02b161bfb54943`: `bbo_tradability_mid`,
  `bbo_tradability_spread_zscore`, `bbo_tradability_spread`,
  `bbo_tradability_spread_ticks`, `bbo_tradability_top_book_depth`,
  `bbo_tradability_top_book_imbalance`,
  `bbo_tradability_missing_bbo_flag`, `bbo_tradability_bad_quote_flag`,
  `bbo_tradability_wide_spread_flag`, `bbo_tradability_low_depth_flag`,
  `bbo_tradability_microprice`.

## Tests Added

- Synthetic multi-version Parquet feature/label stores stage only the locked
  `feature_version_id` and `label_version_id` rows.
- Parquet content-hash mismatch fails closed before staging.
- Ambiguous non-support feature family fails closed.
- Rescore mode remains consistent for a valid namespace.
- The six committed rerun StudySpecs resolve to the declared factor sets above
  with the sanctioned local-registry skip idiom.

## Validation

All commands were run with `PYTHONPATH=$PWD/src` where applicable so this
worktree's `src` was imported.

- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py -q`
  - `8 passed in 0.42s`
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance tests/unit/discovery_rigor_floor -q`
  - `681 passed in 3.50s`
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/research -q`
  - `6 passed in 0.13s`
- `PYTHONPATH=$PWD/src python tools/hooks/canary_runner.py`
  - All Frontier canaries passed.
- `PYTHONPATH=$PWD/src python tools/verify.py --smoke`
  - Exit code 0.
- `PYTHONPATH=$PWD/src PATH="$HOME/.venvs/alpha_system_ci/bin:$PATH" just ci-parity`
  - `3306 passed, 77 skipped in 83.93s`
- `git diff --check`
  - Exit code 0.
- `git ls-files runs`
  - No output.

Ruff was not installed in either `~/.venvs/alpha_system_research` or
`~/.venvs/alpha_system_ci`; changed files were manually checked for over-100
column lines.

## Residual Notes

No raw data, cache, DB, run-local artifact, pushed branch, PR, or review artifact
was created by this executor. Fresh adversarial review remains the next WF1 gate.
