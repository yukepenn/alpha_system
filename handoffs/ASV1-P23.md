# ASV1-P23 Handoff - ML and Factor Combination MVP

## Scope Summary

Implemented the local-first ML/factor-combination MVP scaffold. The layer validates versioned factor-only feature sets, label references, chronological split contracts, deterministic baseline model specs, score output schemas, score-to-portfolio contract metadata, local JSON run manifests, score summaries, and temp SQLite `ml_runs` registry writes.

No broker, live, paper, order-routing, serving, deployment, cloud, GPU, Ray, MLflow server, LightGBM, XGBoost, model binary, prediction dataset, Parquet, Arrow, Feather, or heavy artifact scope was introduced.

## ML Contracts

- `FeatureSetSpec`: requires `feature_set_id`, `data_version`, non-empty `factor_versions`, and feature entries that resolve to declared `factor_id`/`factor_version` pairs.
- `LabelSpec`: records a versioned label reference plus decision and label-availability timestamp fields. Labels are targets only.
- `SplitConfig`: supports chronological train/validation and walk-forward splits with purge/embargo gaps.
- `ModelSpec`: registers executable deterministic MVP baselines (`linear_baseline`, `ridge_baseline`, `ic_weighted_score`) and design-only placeholders for deferred model families.
- `ScoreOutput`: schema `ml_score_output_v1` with run, split, instrument, decision time, score, data version, factor versions, and label version fields.
- `ScoreToPortfolioContract`: representation only; sizing is `deferred` and execution is `none`.
- `ml_runs`: records local/temp SQLite registry rows with reproducibility metadata.

## Leakage Controls

- Raw/ad hoc columns, canonical-bar source declarations, dataframe expressions, and non-factor feature sources are rejected.
- Label ids and label-style sources are rejected as features.
- `label_available_ts` must be no later than `decision_ts` for every scored fixture row.
- Train/validation windows are chronological and non-overlapping.
- Walk-forward windows record explicit train and validation positions.
- Purge and embargo gaps remove training indices around validation windows.

## Model and Scoring Behavior

The MVP baseline is deterministic and standard-library only. It computes covariance-weighted linear/ridge-style scores over declared factor ids. `ic_weighted_score` normalizes gross absolute weights when non-zero. Deferred model types validate as registered design placeholders but raise before training/scoring.

The MVP uses tiny fixture rows keyed by declared factor ids; direct factor-store loading is intentionally not implemented in this phase.

## Registry Integration

`src/alpha_system/experiments/ml_registry.py` writes one row to `ml_runs` through the existing registry migration/table and `RunRecord` helper. Tests use temp SQLite DBs under pytest `tmp_path`. Registry records include git, code hash, config hash, data version, factor versions, label versions, engine version, parameters, artifact paths, decision status, warnings, and status message.

## Files Changed

Source:

- `src/alpha_system/experiments/ml.py`
- `src/alpha_system/experiments/feature_sets.py`
- `src/alpha_system/experiments/splits.py`
- `src/alpha_system/experiments/model_specs.py`
- `src/alpha_system/experiments/scoring.py`
- `src/alpha_system/experiments/ml_outputs.py`
- `src/alpha_system/experiments/ml_registry.py`
- `src/alpha_system/cli/ml.py`
- `src/alpha_system/cli/main.py`

Docs/configs:

- `docs/ML_LAYER.md`
- `docs/ML_LEAKAGE_POLICY.md`
- `configs/ml/examples/feature_set.json`
- `configs/ml/examples/label_spec.json`
- `configs/ml/examples/model_spec.json`
- `configs/ml/examples/split.json`
- `configs/ml/examples/run_config.json`
- `README.md`

Tests:

- `tests/unit/test_feature_set_requires_factor_versions.py`
- `tests/unit/test_feature_set_schema.py`
- `tests/no_lookahead/test_ml_raw_column_rejection.py`
- `tests/no_lookahead/test_ml_label_leakage_rejection.py`
- `tests/no_lookahead/test_ml_label_availability.py`
- `tests/unit/test_train_validation_split.py`
- `tests/unit/test_walk_forward_split.py`
- `tests/unit/test_purge_embargo_gap.py`
- `tests/unit/test_model_spec_registration.py`
- `tests/unit/test_linear_model_spec.py`
- `tests/unit/test_future_model_type_placeholders.py`
- `tests/integration/test_ml_run_registry_tempdb.py`
- `tests/unit/test_ml_score_output_schema.py`
- `tests/unit/test_score_to_portfolio_contract.py`
- `tests/unit/test_ml_artifact_policy.py`
- `tests/unit/test_ml_no_tradability_claims.py`
- `tests/integration/test_ml_cli_help.py`
- `tests/unit/cli/test_ml_cli.py`
- `tests/unit/models/test_ml_baseline.py`

Handoff:

- `handoffs/ASV1-P23.md`

Staged files: none. `git diff --cached --name-only` returned empty. No commit or push was performed by this executor.

## Validation

Passed:

- `python -m pytest tests/unit tests/integration tests/no_lookahead` - 532 passed.
- `python -m pytest tests/unit/models tests/unit/cli/test_ml_cli.py || true` - 2 passed.
- `python -m pytest tests/unit/test_feature_set_requires_factor_versions.py tests/no_lookahead/test_ml_raw_column_rejection.py tests/no_lookahead/test_ml_label_leakage_rejection.py` - 6 passed.
- `python -m pytest tests/unit/test_train_validation_split.py tests/unit/test_walk_forward_split.py tests/unit/test_purge_embargo_gap.py` - 4 passed.
- `PYTHONPATH=src python -m alpha_system.cli ml run --help` - passed; help exposes ML run arguments.
- `python -m compileall src` - passed.
- `find artifacts/ml_experiments -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` - no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - no output.
- `find . -type f \( -name "*.pkl" -o -name "*.joblib" -o -name "*.pickle" -o -name "*.onnx" \) -print` - no output.
- `git ls-files runs` - no output.
- `git diff --cached --name-only` - no output.

Failed/unavailable:

- `python -m alpha_system.cli ml run --help` - failed with `ModuleNotFoundError: No module named 'alpha_system'` because this shell does not have the src-layout package installed and no `PYTHONPATH=src` is set. Changing packaging/root files was outside this phase's allowed paths.
- `alpha ml run --help` - failed with `/bin/bash: line 1: alpha: command not found`; the console script is not installed in this environment.
- `python -m ruff check src tests` - failed with `No module named ruff`; ruff is unavailable.
- `python -m mypy src` - failed with `No module named mypy`; mypy is unavailable.

## Artifact Policy

Explicit staging only was preserved. I did not run `git add .`, `git add -A`, force push, create a PR, merge, create review artifacts, create `verdict.json`, or mark the phase PASS.

No model/prediction/score artifacts, DB files, Parquet/Arrow/Feather files, logs, or `runs/**` paths were staged or committed. ML tests write only to pytest temp directories. The repo artifact audit commands listed above produced no forbidden artifact output.

## README Snapshot

`README.md` was updated compactly for the post-ASV1-P23 snapshot. It states that after ASV1-P23 merges the next phase is ASV1-P24, lists the new ML modules/docs/command, and confirms unchanged safety boundaries.

## Risk Status

- R-001 lookahead: mitigated by label availability validation, chronological splits, and purge/embargo tests.
- R-005 factor/label misalignment: mitigated by explicit factor and label version references.
- R-014 overclaiming: mitigated by docs/tests avoiding performance or tradability claims.
- R-015 promotion without review: mitigated by `ml_recorded` registry status and docs stating reviewed promotion is separate.
- R-030 ML leakage: mitigated by raw-column and label-as-feature rejection tests.
- R-037 CLI writing to local-only paths: mitigated by temp default output path and repository artifact-root rejection.
- R-013/R-038/R-039 heavy/DB/Parquet commits: mitigated by standard-library implementation, temp DB tests, and artifact audits.

## Known Limitations

- Exact `python -m alpha_system.cli ml run --help` and `alpha ml run --help` require either an installed package/console script or an environment with `PYTHONPATH=src`; those are not configured in this shell.
- Factor-store loading is not implemented; fixture rows must carry values keyed by versioned factor ids.
- Deferred model placeholders are intentionally non-executable.
- Score-to-portfolio remains a representation contract and does not implement sizing or execution.

## Review Focus

Review should focus on feature-store discipline, label exclusion, label availability semantics, split gap correctness, output path restrictions, registry reproducibility fields, no overclaim language, and the CLI packaging-path limitation above.
