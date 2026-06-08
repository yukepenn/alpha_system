# FUTSUB-P09 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P09`  
Lane: Yellow  
Executor: Codex

## Intended Commit File List

All changes were left unstaged per executor instructions. Ralph owns staging and commit.

- `README.md`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `src/alpha_system/features/families/structure/family.py`
- `tests/unit/futures_substrate_scaleout/features/test_regime_scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_regime_scaleout_driver.py`
- `research/futures_substrate_scaleout_v1/feature_packs/regime_volatility_compression/coverage_summary.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P09.md`

Existing config confirmed present and consumed:

- `configs/features/scaleout/regime_volatility_compression.json`

## Implementation Summary

- Added `regime_volatility_compression` scaleout support on the existing
  `UnitExecutor` seam.
- Bound config-facing P09 features to existing governed primitives:
  `trendiness -> base_ohlcv_trendiness`,
  `atr_volatility_regime -> base_ohlcv_atr`,
  `range_compression -> liquidity_structure_range_contraction`,
  `range_expansion -> base_ohlcv_rolling_range`, and
  `momentum_reversion_state -> base_ohlcv_returns`.
- Reused the sanctioned scaleout/materialization path:
  canonical loader through the scaleout CLI, `materialize_features`, Parquet
  value-store format, and `FeatureStore.register_materialized_feature`.
- Added symbol/partition `input_scope` metadata to the structure family so the
  mixed OHLCV/structure regime pack remains keystone identity scoped by symbol,
  year, partition, DatasetVersion, and feature-set version. No structure formula
  changed.
- Added focused synthetic tests for P09 dry-run identity and `available_ts`
  discipline, plus a scaleout driver-seam dispatch test.
- Updated the README snapshot for P09 and wrote value-free P09 coverage evidence.

## Materialization Result

The full-window dry-run preview succeeded:

- Rollout: `full-window`
- Accepted units: `24`
- Bounded-real year: `2024`
- Bounded-real units: `3`
- Planned units: `24`
- Failed preview units: `0`
- FeatureVersion preview count: `120` ids (`24` units x `5` bindings)
- 2018 blocked `ohlcv_1m` DatasetVersion excluded by the acceptance summary.
- 2019 and 2026 retained `ACCEPTED_WITH_WARNINGS` metadata.

The bounded-then-full execute command was attempted but did not write values:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/regime_volatility_compression.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json
```

Outcome:

```text
scaleout command error: [Errno 30] Read-only file system: '/home/yuke_zhang/alpha_data/alpha_system/materialization'
```

Because the executor sandbox cannot write `$ALPHA_DATA_ROOT/materialization`,
the real bounded-real and full-window Parquet writes, checkpoint markers,
registry rows, content hashes, and materialized `available_ts` min/max are not
available from this run. The P09 driver verifies required registry fields
(`value_store_format`, `parquet_path`, `value_content_hash`,
`value_schema_version`, `dataset_version_id`, `feature_version_id`) after
successful execute, but no real registry rows were written here.

## DatasetVersions Previewed

Each listed year covers `ES`, `NQ`, and `RTY`; all units consume `ohlcv_1m`.

| Year | DatasetVersion | Acceptance state |
| ---: | --- | --- |
| 2019 | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` |
| 2020 | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` |
| 2021 | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` |
| 2022 | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` |
| 2023 | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` |
| 2024 | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` |
| 2025 | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` |
| 2026 | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` |

Per-symbol/year coverage and bounded-real FeatureVersion previews are recorded
value-free in:

- `research/futures_substrate_scaleout_v1/feature_packs/regime_volatility_compression/coverage_summary.md`

## Validation

- Not run: `git status --short`
  - Reason: explicit executor safety instruction forbade `git status`.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/regime_volatility_compression.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/regime_volatility_compression/coverage_summary.md --json`
  - Passed; produced `24` planned units, `0` failed units.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/regime_volatility_compression.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json`
  - Failed before writes with read-only `$ALPHA_DATA_ROOT/materialization` as shown above.
- `PYTHONPATH=src python -m compileall -q src/alpha_system/features/scaleout src/alpha_system/features/families/structure tests/unit/futures_substrate_scaleout/features/test_regime_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_regime_scaleout_driver.py`
  - Passed.
- `python tools/verify.py --smoke`
  - Passed.
- `python -m pytest tests/unit/futures_substrate_scaleout/features/test_regime_scaleout.py -q`
  - Passed: `2 passed`.
- `python -m pytest tests/unit/futures_substrate_scaleout/scaleout -q`
  - Passed: `6 passed`.
- `python tools/hooks/canary_runner.py`
  - Passed: all Frontier canaries passed.
- `python -m ruff check src/alpha_system/features/scaleout/driver.py src/alpha_system/features/scaleout/__init__.py src/alpha_system/features/families/structure/family.py tests/unit/futures_substrate_scaleout/features/test_regime_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_regime_scaleout_driver.py`
  - Not run to completion: `ruff` is not installed in this venv (`No module named ruff`).
- `test -f configs/features/scaleout/regime_volatility_compression.json`
  - Passed.
- `test -f research/futures_substrate_scaleout_v1/feature_packs/regime_volatility_compression/coverage_summary.md`
  - Passed.
- `git ls-files runs`
  - Passed: empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`
  - Passed: empty output.

## Artifact And Safety Notes

- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.
- No files under `runs/**` were created for this handoff.
- No `review.md`, `verdict.json`, PR, merge, live, paper, broker, order, or
  deployment action was performed.
- No feature values, Parquet files, SQLite registries, provider responses, raw
  data, canonical data, roll-calendar data, or heavy artifacts were written into
  the repository.
- Phase is not marked PASS by this executor.
