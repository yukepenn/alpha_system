# FCFP-P11 Handoff - Targeted / Incremental Materialization CLI

## Files For Explicit Staging By Ralph

- `src/alpha_system/cli/scaleout.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_targeting.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py`
- `docs/feature_compute_fast_path/TARGETED_SCALEOUT.md`
- `docs/feature_compute_fast_path/README.md`
- `docs/feature_compute_fast_path/OVERVIEW.md`
- `README.md`
- `handoffs/FEATURE_COMPUTE_FAST_PATH_V1/FCFP-P11.md`

No files were staged or committed by the executor. `git status`, `git diff`,
`git add`, `git commit`, and `git push` were not run per executor safety rules.

## Implementation Summary

- Added `ScaleoutTarget` with family, feature id, feature group, label id,
  label group, symbols, years, and DatasetVersion id selectors.
- Added `ScaleoutDryRunEstimate` and included it in `ScaleoutRunSummary` JSON
  and Markdown output. Estimates are counts and metadata only: selected unit
  count, planned step count, symbols, years, DatasetVersion ids, estimated rows
  per unit/total rows, and estimated seconds per unit/total seconds.
- Extended `build_scaleout_units()` and `run_scaleout()` to accept a target.
  Targeting filters the accepted unit grid before execution. Unknown feature,
  feature-group, symbol, or year selectors fail closed; DatasetVersion selectors
  resolve by intersecting the accepted grid.
- Narrowed feature selections build units whose `feature_names` contain only the
  selected feature/group members. Narrowed feature units get distinct checkpoint
  unit ids from full-family units; default untargeted unit ids remain unchanged.
- Extended `alpha scaleout feature-pack` with `--dry-run`, `--family`,
  `--feature-id`, `--feature-group`, `--label-id`, `--label-group`,
  `--symbols`, `--years`, and `--dataset-version-ids`.
- Strengthened skip-completed: a checkpoint completed record skips only when the
  official `FeatureStore` read path resolves the recorded `feature_version_id`
  entries to existing value files. If checkpoint truth is absent but registry
  truth proves the previewed ids are already complete, the driver records a
  checkpoint marker and skips.

The current scaleout command surface remains `feature-pack`. Label selectors are
accepted as target metadata for the shared contract, but no label scaleout
producer path was invented in this phase; label filters select no feature units
on current feature-pack configs.

## Behavioral Evidence

- `test_targeted_feature_selection_narrows_grid_to_feature_symbol_year_dataset`
  proves one selected feature/symbol/year/DatasetVersion builds one unit with
  only that feature and a different checkpoint unit id from the full-family unit.
- `test_feature_group_selection_uses_configured_group_without_other_features`
  proves configured feature groups narrow the unit feature set.
- `test_selecting_one_feature_does_not_expand_to_other_families` proves a
  one-feature target stays in `base_ohlcv` and a mismatched family target builds
  no units.
- `test_dry_run_estimate_is_value_free_and_writes_nothing` proves dry-run emits
  unit/row/time estimates with no Parquet path, zero materialized rows, and no
  `ALPHA_DATA_ROOT` writes.
- `test_execute_runs_selected_units_only` proves execute calls the executor only
  for selected units.
- `test_skip_completed_requires_checkpoint_and_registry_truth` proves restart
  skip requires checkpoint plus official registry read-path truth.

## Invariants

- The reference engine, feature/label family modules, resolver code, registry
  implementation, and `features/engine/materialization.py` were not edited.
- `feature_version_id` / `label_version_id` derivation, resolver exact-id
  semantics, and serial registry writes are unchanged.
- The driver was not routed to the V1 producer path; that remains FCFP-P14.
- No real registry, real values, provider data, Parquet, SQLite, DB, Arrow,
  Feather, DBN, ZST, logs, or run artifacts were intentionally created or added
  under commit-eligible paths.

## Validation

- `python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_targeting.py tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py -q`
  - exit 0; `9 passed`
- `python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_scaleout_driver.py tests/unit/futures_substrate_scaleout/scaleout/test_session_scaleout_driver.py -q`
  - exit 0; `4 passed`
- `python -m pytest tests/unit/feature_compute_fast_path/ -q`
  - exit 0; `19 passed`
- `python -m pytest tests/unit/futures_substrate_scaleout/ -q`
  - exit 0; `54 passed`
- `ALPHA_DATA_ROOT=/tmp/alpha_system_fcfp_p11_data python tools/verify.py --smoke`
  - exit 0
- `ALPHA_DATA_ROOT=/tmp/alpha_system_fcfp_p11_data python tools/verify.py --lint`
  - exit 0; ruff is not installed in the active environment, so the repository
    lint command skipped with: `ruff is not installed; run pip install -e
    ".[dev]" to enable lint. Skipping.`
- `ALPHA_DATA_ROOT=/tmp/alpha_system_fcfp_p11_data python tools/verify.py --typecheck`
  - exit 0; compileall completed
- `ALPHA_DATA_ROOT=/tmp/alpha_system_fcfp_p11_data python tools/hooks/canary_runner.py`
  - exit 0; all Frontier canaries passed
- `git ls-files runs`
  - exit 0; empty output
- `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.arrow' '**/*.feather' '**/*.db' '**/*.dbn' '**/*.zst'`
  - exit 0; empty output

`git status --short` and any cached-diff audit were not run because the
executor prompt explicitly prohibited `git status` and `git diff`. Ralph owns
staging and cached artifact audit after executor handoff.
