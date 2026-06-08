# FUTSUB-P10 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P10`  
Lane: Yellow  
Executor: Codex

## Intended Commit File List

All changes were left unstaged per executor instructions. Ralph owns staging and
commit.

- `README.md`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `tests/unit/futures_substrate_scaleout/features/test_liquidity_pa_scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_liquidity_pa_scaleout_driver.py`
- `research/futures_substrate_scaleout_v1/feature_packs/liquidity_sweep_pa_structure/coverage_summary.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P10.md`

Existing config confirmed present and consumed:

- `configs/features/scaleout/liquidity_sweep_pa_structure.json`

## Implementation Summary

- Added `liquidity_sweep_pa_structure` support on the existing FUTSUB-P06
  `UnitExecutor` seam.
- Bound the P10 config labels to existing governed structure primitives only:
  prior high/low distance, sweep high/low flags, failed high/low breakout
  flags, close-location value, wick-rejection score, and range contraction.
- Reused the sanctioned scaleout/materialization path: canonical loader through
  the scaleout CLI, `materialize_features`, Parquet value-store format, and
  `FeatureStore.register_materialized_feature`.
- Added focused synthetic tests for P10 dry-run identity, `available_ts`
  discipline, sweep/failed-breakout behavior, and scaleout driver dispatch.
- Updated README snapshot and wrote value-free P10 coverage evidence.

No structure-family formula was changed. No new liquidity/PA features or
subjective/discretionary PA encodings were added.

## Materialization Result

The full-window dry-run preview succeeded:

- Rollout: `full-window`
- Accepted units: `24`
- Bounded-real year: `2024`
- Bounded-real units: `3`
- Planned units: `24`
- Failed preview units: `0`
- FeatureVersion preview count: `216` ids (`24` units x `9` governed structure
  primitives)
- 2018 blocked `ohlcv_1m` DatasetVersion excluded by the acceptance summary.
- 2019 and 2026 retained `ACCEPTED_WITH_WARNINGS` metadata.
- Per-symbol/year coverage and bounded-real FeatureVersion previews are recorded
  value-free in
  `research/futures_substrate_scaleout_v1/feature_packs/liquidity_sweep_pa_structure/coverage_summary.md`.

The bounded-then-full execute command was attempted but did not write values:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/liquidity_sweep_pa_structure.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json
```

Outcome:

```text
scaleout command error: [Errno 30] Read-only file system: '/home/yuke_zhang/alpha_data/alpha_system/materialization'
```

Because this executor sandbox cannot write `$ALPHA_DATA_ROOT/materialization`,
the real bounded-real and full-window Parquet writes, checkpoint markers,
registry rows, content hashes, and materialized `available_ts` min/max are not
available from this run. The P10 executor verifies required registry fields
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

## Validation

- Not run: `git status --short`
  - Reason: explicit executor safety instruction forbade `git status`.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/liquidity_sweep_pa_structure.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/liquidity_sweep_pa_structure/coverage_summary.md --json`
  - Passed; produced `24` planned units, `0` failed units.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/liquidity_sweep_pa_structure.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json`
  - Failed before writes with read-only `$ALPHA_DATA_ROOT/materialization` as
    shown above.
- `PYTHONPATH=src python -m compileall -q src/alpha_system/features/scaleout tests/unit/futures_substrate_scaleout/features/test_liquidity_pa_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_liquidity_pa_scaleout_driver.py`
  - Passed.
- `python tools/verify.py --smoke`
  - Passed.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/features/test_liquidity_pa_scaleout.py -q`
  - Passed: `2 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/scaleout -q`
  - Passed: `7 passed`.
- `python tools/hooks/canary_runner.py`
  - Passed: all Frontier canaries passed.
- `test -f configs/features/scaleout/liquidity_sweep_pa_structure.json && test -f research/futures_substrate_scaleout_v1/feature_packs/liquidity_sweep_pa_structure/coverage_summary.md`
  - Passed.
- `git ls-files runs && git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`
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
