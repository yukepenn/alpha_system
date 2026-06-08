# FUTSUB-P13 Executor Handoff

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Phase: `FUTSUB-P13`  
Lane: Yellow  
Executor: Codex

## Intended Commit File List

All changes were left unstaged per executor instructions. Ralph owns staging and
commit.

- `README.md`
- `src/alpha_system/features/families/cross_market/family.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `configs/features/scaleout/cross_market_alignment.json`
- `research/futures_substrate_scaleout_v1/feature_packs/cross_market_alignment/coverage_summary.md`
- `tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P13.md`

## Implementation Summary

- Added `cross_market_alignment` support on the existing FUTSUB-P06
  `UnitExecutor` seam and scaleout family dispatch.
- Reused the governed cross-market family engine and the sanctioned scaleout
  write path: canonical loader, Parquet value-store format, and
  `FeatureStore.register_materialized_feature`.
- Added strict event-timestamp intersection mode for cross-market rows. This
  mode emits output only where ES, NQ, and RTY share the same `event_ts`; output
  `available_ts` is the latest contributing per-instrument availability for that
  same event.
- Forbid cross-instrument forward-fill and missing-instrument imputation in the
  P13 materialization path. Missing events are excluded from the explicit
  intersection and surfaced through coverage.
- Bound P13 config labels to existing governed Cross-Market primitives only:
  synchronized returns, NQ/ES and RTY/ES beta residuals, NQ-minus-ES and
  RTY-minus-ES return spreads, risk-on/risk-off rotation proxies,
  confirmation/divergence flags, and existing NQ/ES and RTY/ES rolling
  correlations as governed pair-state proxies.
- Added target-symbol input scope to Cross-Market FeatureVersion input metadata
  so ES, NQ, and RTY target partitions produce distinct deterministic identities
  without depending on registry mutation state.
- Added focused synthetic tests for dry-run identity, strict intersection,
  delayed contributing availability, missing-instrument exclusion, and scaleout
  driver dispatch.
- Updated the README snapshot and wrote value-free P13 coverage evidence.

No new cross-market formulas were introduced. No other feature family, label
family, runtime diagnostic, value-store schema, execution, broker, live, signal,
strategy, portfolio, or backtest path was edited.

## Materialization Result

The full-window dry-run preview succeeded:

- Rollout: `full-window`
- Accepted units: `24`
- Acceptance states: `21` `ACCEPTED`, `3` `ACCEPTED_WITH_WARNINGS`
- Bounded-real year: `2024`
- Bounded-real units: `3`
- Planned units: `24`
- Failed preview units: `0`
- FeatureVersion preview count: `264` ids (`24` units x `11` existing governed
  primitive bindings)
- 2018 blocked `ohlcv_1m` DatasetVersion excluded by the acceptance summary.
- 2019 and 2026 warning metadata retained through accepted/warned
  DatasetVersion state.
- Per-symbol/year coverage and bounded-real FeatureVersion previews are recorded
  value-free in
  `research/futures_substrate_scaleout_v1/feature_packs/cross_market_alignment/coverage_summary.md`.

The bounded-real-then-full execute command could not be run in this executor
sandbox because `$ALPHA_DATA_ROOT/materialization` is read-only here. I verified
the write precondition before invoking the expensive execute path:

```bash
mkdir -p "$ALPHA_DATA_ROOT/materialization/futures_substrate_scaleout_v1/checkpoints/features/cross_market_alignment"
```

Outcome:

```text
mkdir: cannot create directory ‘/home/yuke_zhang/alpha_data/alpha_system/materialization’: Read-only file system
```

Because this sandbox cannot write `$ALPHA_DATA_ROOT/materialization`, real
bounded-real and full-window Parquet writes, checkpoint markers, registry rows,
content hashes, materialized row counts, materialized per-instrument
`available_ts` min/max, and registry-resolved coverage rates are not available
from this executor run. The P13 executor code verifies required registry fields
(`value_store_format`, `parquet_path`, `value_content_hash`,
`value_schema_version`, `dataset_version_id`, `feature_version_id`) after a
successful execute through `FeatureStore.register_materialized_feature`, but no
real registry rows were written here.

The exact execute command that remains for Ralph or an unsandboxed operator is:

```bash
PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/cross_market_alignment.json --rollout bounded-then-full --execute --alpha-data-root "$ALPHA_DATA_ROOT" --dataset-registry "$ALPHA_DATA_ROOT/registry/datasets.sqlite" --json
```

## DatasetVersions Previewed

Each listed year covers ES, NQ, and RTY target units. Each target unit consumes
the configured ES/NQ/RTY cross-market input set through the listed accepted
`ohlcv_1m` and dense-grid DatasetVersions.

| Year | `ohlcv_1m` DatasetVersion | Dense-grid DatasetVersion | Acceptance state |
| ---: | --- | --- | --- |
| 2019 | `dsv_databento_ohlcv_a483cc0cc282474b` | `dsv_databento_ohlcv_dense_2019_v1` | `ACCEPTED_WITH_WARNINGS` |
| 2020 | `dsv_databento_ohlcv_bac95e92f1bb1850` | `dsv_databento_ohlcv_dense_2020_v1` | `ACCEPTED` |
| 2021 | `dsv_databento_ohlcv_8aeb50fb409fc691` | `dsv_databento_ohlcv_dense_2021_v1` | `ACCEPTED` |
| 2022 | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `dsv_databento_ohlcv_dense_2022_v1` | `ACCEPTED` |
| 2023 | `dsv_databento_ohlcv_ec144f9a02a64774` | `dsv_databento_ohlcv_dense_2023_v1` | `ACCEPTED` |
| 2024 | `dsv_databento_ohlcv_05404069799decb0` | `dsv_databento_ohlcv_dense_2024_v1` | `ACCEPTED` |
| 2025 | `dsv_databento_ohlcv_35ffead770498acd` | `dsv_databento_ohlcv_dense_2025_v1` | `ACCEPTED` |
| 2026 | `dsv_databento_ohlcv_a0342ee6a412622b` | `dsv_databento_ohlcv_dense_2026_v1` | `ACCEPTED_WITH_WARNINGS` |

## Availability Confirmation

The implemented P13 path preserves per-instrument `available_ts` with no
cross-instrument forward-fill (R-015, R-016):

- Strict mode aligns ES/NQ/RTY only on exact shared `event_ts`.
- Output `available_ts` is `max(ES.available_ts, NQ.available_ts,
  RTY.available_ts)` for that event.
- A delayed contributor delays the output feature value.
- A missing instrument event is excluded rather than imputed.
- The synthetic tests cover delayed NQ availability and a missing RTY event.

This was verified against synthetic fixtures and dry-run identity. It could not
be re-verified against real materialized values in this sandbox because the local
data root is read-only.

## Validation

- Not run: `git status --short`
  - Reason: explicit executor safety instruction forbade `git status`.
- `PYTHONPATH=src python -m compileall -q src/alpha_system/features/families/cross_market/family.py src/alpha_system/features/scaleout tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py`
  - Passed.
- `PYTHONPATH=src python -m alpha_system.cli scaleout feature-pack --config configs/features/scaleout/cross_market_alignment.json --rollout full-window --summary-out research/futures_substrate_scaleout_v1/feature_packs/cross_market_alignment/coverage_summary.md --json`
  - Passed; produced `24` planned units, `0` failed units, dry-run `true`.
- `mkdir -p "$ALPHA_DATA_ROOT/materialization/futures_substrate_scaleout_v1/checkpoints/features/cross_market_alignment"`
  - Failed before materialization with read-only `$ALPHA_DATA_ROOT/materialization`:
    `mkdir: cannot create directory ‘/home/yuke_zhang/alpha_data/alpha_system/materialization’: Read-only file system`.
- `python tools/verify.py --smoke`
  - Passed.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/features/test_cross_market_scaleout.py -q`
  - Passed: `3 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_cross_market_scaleout_driver.py -q`
  - Passed: `2 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/scaleout -q`
  - Passed: `13 passed`.
- `python tools/hooks/canary_runner.py`
  - Passed: all Frontier canaries passed.
- `test -f configs/features/scaleout/cross_market_alignment.json`
  - Passed.
- `test -f research/futures_substrate_scaleout_v1/feature_packs/cross_market_alignment/coverage_summary.md`
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
