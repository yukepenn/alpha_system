# ML Layer

The ML layer is a local-first research scaffold for deterministic factor-combination experiments. It consumes versioned factor references through `FeatureSetSpec`, a versioned label reference through `LabelSpec`, a `ModelSpec`, and an explicit split config. It writes local run manifests, score summaries, and optional temp SQLite `ml_runs` records.

This layer is not a production ML system. It does not serve models, deploy models, perform live inference, route orders, or operate broker, paper, or live trading systems. Scores are research records only. A score-to-portfolio object is represented as a contract for later reviewed work; it does not size positions or execute anything.

## Durable Modules

- `src/alpha_system/experiments/feature_sets.py`: validates `FeatureSetSpec` and `LabelSpec` references.
- `src/alpha_system/experiments/splits.py`: provides train/validation, walk-forward, purge, and embargo utilities.
- `src/alpha_system/experiments/model_specs.py`: registers implemented MVP model specs and deferred placeholders.
- `src/alpha_system/experiments/scoring.py`: fits deterministic baseline score skeletons on fixture rows.
- `src/alpha_system/experiments/ml_outputs.py`: defines the score schema and score-to-portfolio contract.
- `src/alpha_system/experiments/ml_registry.py`: writes `ml_runs` records to local/temp SQLite registries.
- `src/alpha_system/experiments/ml.py`: assembles validation, scoring, manifests, and registry writes.
- `src/alpha_system/cli/ml.py`: provides `alpha ml run`.

## Contracts

`FeatureSetSpec` requires:

- `feature_set_id`;
- `data_version`;
- non-empty `factor_versions`;
- feature entries that reference `factor_id` and `factor_version`.

Raw columns, expressions, dataframe columns, canonical bar columns, ad hoc sources, and label sources are rejected. Features must resolve through declared factor versions.

`LabelSpec` records a versioned label id/version and the timestamp fields used to prove label availability. Labels are excluded from features and are used only as supervised targets for local fixture scoring.

`ModelSpec` supports deterministic MVP baseline types:

- `linear_baseline`;
- `ridge_baseline`;
- `ic_weighted_score`.

Deferred design-only placeholders are registered for `orthogonalized_score`, `lightgbm`, `xgboost`, `random_forest`, `meta_labeling`, `ensemble`, and `regime_conditioned_model`. Those placeholders validate as named future concepts but do not have executable training paths.

`ScoreOutput` uses schema `ml_score_output_v1` and includes run id, split id, instrument, decision timestamp, score, feature set id, model id, data version, factor versions, and label version.

`ScoreToPortfolioContract` records field names and constraints for a later conversion layer. Its sizing implementation is `deferred`, and its execution implementation is `none`.

## Local Artifacts

`alpha ml run` defaults to a directory under the system temp root. Explicit output directories are accepted, but repository-local `runs/`, `metadata/`, `data/`, and `artifacts/ml_experiments/` paths are rejected. The MVP writes JSON manifests and score summaries only; it does not write model binaries, prediction datasets, Parquet, Arrow, Feather, ONNX, pickle, or joblib artifacts.

When `--registry-path` is provided, the path is initialized as a local SQLite metadata registry and a row is inserted into `ml_runs`. Temp directories are expected for tests and examples.

## CLI

```bash
alpha ml run --config configs/ml/examples/run_config.json
```

The command accepts a full run config or separate `FeatureSetSpec`, `LabelSpec`, `ModelSpec`, split config, and tiny fixture observations. It also accepts overrides for data version, factor versions, label version, instruments, registry path, and output directory.

## Boundaries

The layer records local research evidence only. It does not create a second PnL truth, does not bypass the reference engine, and does not set candidate promotion status. Any later promotion requires reviewed decision artifacts outside this MVP.
