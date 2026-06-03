# Strategy Grid Engine

The strategy grid engine is a local, bounded research tool for small factor,
signal, execution-cost, risk-sizing, and position-management sweeps. It writes
schema-defined evidence artifacts and one optional SQLite registry record. It
does not promote candidates or change the Tier 1 PnL truth boundary.

## Command

```bash
alpha grid run --config configs/grids/examples/tiny_strategy_grid.json
```

Source-tree usage:

```bash
PYTHONPATH=src python -m alpha_system.cli grid run --help
```

The command accepts a grid config plus optional declared strategy, management,
portfolio, execution, data, factor, and label version overrides. Tests must pass
`--output-dir` and `--registry-path` under `tmp_path`.

## Grid Types

Supported parameter groups:

- `factor`: factor parameter diagnostics, such as lookback or normalization.
- `strategy`: signal settings, such as direction or signal pattern.
- `risk`: sizing settings, such as default quantity.
- `management`: simple position-management settings, such as EOD flattening,
  fixed stop, or target percentage.
- `execution`: final execution-cost validation settings, such as fixed bps and
  minimum cost.

Every parameter must be an explicit finite list. Empty dimensions, scalar
dimensions, unknown groups, and grids exceeding `max_combinations` fail closed.
The engine never truncates a Cartesian product.

## Discipline Order

The required order is represented as:

1. `factor_diagnostics`
2. `simple_signal_grid`
3. `simple_management_baseline`
4. `survivor_strategy_management_hook`
5. `finalist_execution_validation`

Expansion follows the matching parameter order: factor, strategy, risk,
management, then execution. The survivor-management workflow itself remains
reserved for ASV1-P21; ASV1-P20 only keeps the named seam visible.

## Outputs

Each run writes exactly:

- `leaderboard.csv`
- `grid_summary.md`
- `monthly_breakdown.csv`
- `cost_sensitivity.csv`
- `top_configs.yaml`
- `rejected_configs.csv`
- `run_manifest.json`

Rejected configurations are written with `config_id`, `status`, `reason`, and
`parameters_json`. Rejections are never silently dropped.

## Engine Selection

`reference` is the default engine and remains the canonical 1-minute PnL truth.
`fast` is acceleration only. Fast execution first runs the ASV1-P19 parity gate
and requires accelerated parity for every requested feature. If a requested
feature is not certified and `reference_fallback` is true, the configuration is
run through the reference engine and records `engine_used=reference_fallback`.
If fallback is disabled, the configuration fails closed and its reason is
recorded.

Same-bar stop/target ambiguity inherits the conservative reference and
parity-gated fast behavior; the grid layer does not define a second execution
truth.

## Reproducibility

The manifest and optional registry row include run id, timestamp, git commit,
dirty-tree indicator, code hash, config hash, data version, factor versions,
label versions, engine version, parameters, artifact paths, decision status,
warnings, and failed-step visibility.

## Artifact Policy

Generated grid artifacts are local-only. They may be written under
`artifacts/strategy_grids/` for local inspection, but they must not be staged or
committed. Temp directories are preferred for tests and automation. SQLite
registry paths must be temp/local paths outside the repository.
