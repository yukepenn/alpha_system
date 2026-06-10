# LCFP-P06 Handoff

## Status

- `code_status`: implemented
- `execute_status`: isolated bounded-real smoke passed; main registry attempt failed closed on existing reference-lineage conflict.
- `registry_status`: serial writer path passed in an isolated local-only registry; main reference-engine rows were preserved; no manual SQLite writes.
- `artifact_status`: value-free committed report/docs only; label values, Parquet files, manifests, checkpoints, SQLite files, and backups remain local-only under `$ALPHA_DATA_ROOT`.

This handoff does not mark the phase PASS. Review, verdict, staging, commit, PR, CI, and merge are Ralph-owned.

## Branch / Commits

- Branch: Ralph-managed phase worktree. The executor did not query or mutate git branch state beyond allowed `git ls-files` artifact checks.
- Commits: none by executor.
- Staging: none by executor.

## Built

- Added V1 fast-label worker manifests and worker output contracts for value-free local resume evidence.
- Wired `scaleout label-pack` targeting for `--label-group`, `--horizon-group`, `--symbols`, `--years`, and `--dataset-version-ids`.
- Added label worker resolution precedence: `--workers` > `ALPHA_LABEL_CPU_WORKERS` > `ALPHA_CPU_WORKERS` > `1`.
- Routed `alpha label materialize --fast-path` through the scaleout driver targeting surface.
- Added compute-only worker fanout for fast label units and a single parent-process serial registry writer through `FastLabelMaterializer.register_pack` / `LabelRegistry.register_materialized_label`.
- Added checkpoint skip and `--force` behavior for label units, including engine-aware registry truth so fast outputs do not silently mix with reference-engine rows.
- Recorded fast producer metadata through the existing keystone lineage/registry path without changing label identity semantics.
- Added synthetic unit tests for targeting, dry-run write-freedom, checkpoint skip/force, serial writer order, worker env precedence, and the `alpha label materialize --fast-path` CLI.
- Added a value-free integration report for the bounded-real smoke.
- Updated README and label fast-path docs with the P06 capability and unchanged safety boundaries.

## Curated Files For Ralph To Stage

- `README.md`
- `docs/label_compute_fast_path/README.md`
- `docs/label_compute_fast_path/OVERVIEW.md`
- `research/label_compute_fast_path_v1/integration/integration_report.md`
- `src/alpha_system/labels/fast/worker.py`
- `src/alpha_system/labels/fast/__init__.py`
- `src/alpha_system/labels/registry.py`
- `src/alpha_system/features/scaleout/driver.py`
- `src/alpha_system/features/scaleout/__init__.py`
- `src/alpha_system/cli/scaleout.py`
- `src/alpha_system/cli/label.py`
- `tests/unit/label_compute_fast_path/test_worker_checkpoint_registry_integration.py`
- `tests/unit/futures_substrate_scaleout/scaleout/test_fixed_horizon_label_scaleout_driver.py`
- `handoffs/LABEL_COMPUTE_FAST_PATH_V1/LCFP-P06.md`

Run-local audit handoff, not commit-eligible:

- `runs/2026-06-10T102615Z_LABEL_COMPUTE_FAST_PATH_V1/phases/LCFP-P06/handoff.md`

## Registry Backup

- Main registry backup path:
  `/home/yuke_zhang/alpha_data/alpha_system/registry/labels.sqlite.bak_lcfp_20260610T132806Z`
- Timestamp encoded in backup filename: `20260610T132806Z`
- The main-registry fast execute attempt failed closed with `existing registry record has a mismatched lineage`, preserving existing reference-engine rows.

## Bounded-Real Slice Evidence

- Main bounded-real slice selection: `fixed_horizon`, label group `diagnostic`, horizon group `base`, symbol `ES`, year `2024`, dataset version `dsv_databento_ohlcv_05404069799decb0`.
- Selected units: `2` (`fwd_ret_1m`, `fwd_ret_3m`).
- Isolated local-only smoke root:
  `/home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z`
- Execute result in isolated smoke root: accepted `2`, completed `2`, failed `0`, skipped `0`.
- Registry row delta in isolated smoke registry: `+2`.
- Row counts recorded in registry/materialization metadata: `340876` and `340368`.
- Skip restart result: completed `0`, skipped `2`, reason `completed unit skipped from checkpoint + registry truth`.
- Force restart result: completed `2`, skipped `0`, `force_recompute=true`.
- Resolver smoke: strict identity resolved `2/2`; missing strict identity returned `None`; producer engine was `alpha_system.labels.fast.pack_materializer.v1`.

The value-free report with command details is at `research/label_compute_fast_path_v1/integration/integration_report.md`.

## Validation

Requested commands:

- `git status --short`
  - Not run. The user explicitly forbade `git status`; this is not treated as a blocker.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - Passed.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/ -q`
  - Passed: `27 passed in 0.98s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/feature_compute_fast_path/ -q`
  - Passed: `51 passed in 3.02s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/no_lookahead/feature_label/test_synthetic_fail_closed.py -q`
  - Passed: `12 passed in 0.14s`.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m pytest tests/unit/test_fast_path_artifact_policy.py -q`
  - Passed: `2 passed in 0.26s`.
- `test -f research/label_compute_fast_path_v1/integration/integration_report.md`
  - Passed.
- `git ls-files runs`
  - Passed: empty output.
- `git ls-files '**/*.parquet' '**/*.sqlite'`
  - Passed: empty output.

Additional artifact check:

- `git ls-files '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.db'`
  - Passed: empty output.

Additional implementation checks:

- `python -m compileall -q src/alpha_system/labels/fast/worker.py src/alpha_system/labels/fast/__init__.py src/alpha_system/labels/registry.py src/alpha_system/features/scaleout/driver.py src/alpha_system/features/scaleout/__init__.py src/alpha_system/cli/scaleout.py src/alpha_system/cli/label.py tests/unit/label_compute_fast_path/test_worker_checkpoint_registry_integration.py tests/unit/futures_substrate_scaleout/scaleout/test_fixed_horizon_label_scaleout_driver.py`
  - Passed.
- `PYTHONPATH=src python -m pytest tests/unit/label_compute_fast_path/test_worker_checkpoint_registry_integration.py -q`
  - Passed: `5 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/futures_substrate_scaleout/scaleout/test_fixed_horizon_label_scaleout_driver.py -q`
  - Passed: `4 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_cli_targeting.py -q`
  - Passed: `2 passed`.
- `PYTHONPATH=src python -m pytest tests/unit/feature_compute_fast_path/test_scaleout_worker_parallelism.py -q`
  - Passed: `5 passed`.

Bounded-real / resolver commands:

- `PYTHONPATH=src python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/fixed_horizon.json --execute --rollout bounded-real --bounded-year 2024 --label-group diagnostic --horizon-group base --symbols ES --years 2024 --dataset-version-ids dsv_databento_ohlcv_05404069799decb0 --workers 2 --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 --json`
  - Failed before writes under the default Python because optional dependency `polars` was not installed.
- `PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/fixed_horizon.json --execute --rollout bounded-real --bounded-year 2024 --label-group diagnostic --horizon-group base --symbols ES --years 2024 --dataset-version-ids dsv_databento_ohlcv_05404069799decb0 --workers 2 --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 --json`
  - Failed closed: `existing registry record has a mismatched lineage`.
- `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z PYTHONPATH=src /home/yuke_zhang/.venvs/alpha_system_research/bin/python -m alpha_system.cli.main scaleout label-pack --config configs/labels/scaleout/fixed_horizon.json --execute --rollout bounded-real --bounded-year 2024 --label-group diagnostic --horizon-group base --symbols ES --years 2024 --dataset-version-ids dsv_databento_ohlcv_05404069799decb0 --workers 2 --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system/lcfp_p06_smoke_20260610T133001Z --dataset-registry /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite --canonical-root /home/yuke_zhang/alpha_data/alpha_system/databento/canonical/glbx_mdp3 --json`
  - Passed: accepted `2`, completed `2`, failed `0`.
- Same isolated execute command without `--force`
  - Passed: completed `0`, skipped `2`.
- Same isolated execute command with `--force`
  - Passed: completed `2`, skipped `0`.
- Resolver smoke Python snippet from `research/label_compute_fast_path_v1/integration/integration_report.md`
  - Passed: `{'resolved_count': 2, 'fail_closed_missing_id': True, 'producer_engine_id': 'alpha_system.labels.fast.pack_materializer.v1'}`.

## Skipped Checks / Exceptions

- `git status --short` was not run because the user explicitly forbade `git status`.
- No reviewer, review artifact, verdict artifact, PR, merge, staging, commit, or push was created by the executor per user instruction.

## Next Step

Ralph should perform curated staging, review routing, validation ledger updates, verdict handling, PR/CI/merge gate work, and any allowed repair routing.
