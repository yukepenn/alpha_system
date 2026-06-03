# ASV1-P20 Handoff - Strategy Grid Engine MVP

## Status

Implemented the bounded local Strategy Grid Engine MVP. No review, verdict,
PR, merge, live/paper/broker operation, order routing, deployment, or PASS
marking was performed by Codex.

## Scope Summary

Grid type coverage:

- Factor parameter grid: finite `factor.*` dimensions are parsed, ordered, and
  recorded.
- Strategy signal grid: deterministic synthetic long/short and no-trade signal
  patterns are supported.
- Execution cost grid: `execution.fixed_bps` and `execution.minimum_cost` feed
  the reference cost model.
- Risk sizing grid: `risk.default_quantity` feeds the reference engine sizing
  parameter.
- Position management grid: simple EOD, fixed stop, and target settings feed
  conservative reference/fast behavior.

Grid discipline is represented as factor diagnostics, simple signal grid, simple
management baseline, survivor-management hook, and finalist execution
validation. Expansion enforces parameter order as factor, strategy, risk,
management, then execution. The survivor workflow remains out of scope for
ASV1-P21.

## Controls And Outputs

Explosion controls:

- `GridSpec` requires explicit finite parameter lists and `max_combinations`.
- Empty, scalar, unknown, or unbounded dimensions fail validation.
- Expansion above the declared bound raises `GridExpansionError` with a visible
  rejected-grid reason; it never truncates.

Output schemas:

- `leaderboard.csv`
- `grid_summary.md`
- `monthly_breakdown.csv`
- `cost_sensitivity.csv`
- `top_configs.yaml`
- `rejected_configs.csv`
- `run_manifest.json`

Rejected configs are always written to `rejected_configs.csv` with config id,
status, reason, and serialized parameters. Runtime validation failures, explicit
rejection rules, and zero-cost policy failures are visible rather than dropped.

## Fast/Reference Behavior

Reference is the default engine and remains the single canonical 1-minute PnL
truth. Fast mode runs `certify_parity()` and
`assert_grid_fast_path_allowed()` before acceleration. Certified accelerated
feature sets run through P19 fast path with fallback disabled. Unsupported or
uncertified feature sets route to `engine_used=reference_fallback` when
`reference_fallback=true`, or fail closed with a recorded reason when disabled.

Same-bar stop/target behavior inherits the existing conservative reference and
P19 parity-gated fast semantics; no second PnL truth was added.

## Registry And Reproducibility

Grid runs can insert one row into the existing `grid_runs` SQLite table via the
repo's `RunRecord`/`insert_run_record` API. Tests use temp DBs only. The
manifest and registry row carry run id, timestamp, git commit, dirty-tree
indicator, code hash, config hash, data version, factor versions, label
versions, engine version, parameters, artifact paths, decision status, warnings,
and failed-step visibility.

## Files Changed And Staged

Source:

- `src/alpha_system/experiments/grid.py`
- `src/alpha_system/experiments/runner.py`
- `src/alpha_system/experiments/limits.py`
- `src/alpha_system/experiments/leaderboard.py`
- `src/alpha_system/experiments/grid_outputs.py`
- `src/alpha_system/experiments/grid_config.py`
- `src/alpha_system/experiments/grid_manifest.py`
- `src/alpha_system/cli/main.py`
- `src/alpha_system/cli/grid.py`

Docs/configs:

- `docs/GRID_ENGINE.md`
- `docs/GRID_OVERFIT_POLICY.md`
- `configs/grids/examples/tiny_strategy_grid.json`
- `README.md`

Tests:

- `tests/unit/test_grid_expansion_count.py`
- `tests/unit/test_grid_max_combination_rejection.py`
- `tests/unit/test_grid_deterministic_ordering.py`
- `tests/unit/test_grid_rejected_configs.py`
- `tests/unit/test_grid_rejected_reasons.py`
- `tests/unit/test_grid_leaderboard_schema.py`
- `tests/unit/test_grid_output_schemas.py`
- `tests/unit/test_grid_manifest_fields.py`
- `tests/unit/test_grid_requires_versions.py`
- `tests/unit/cli/test_grid_cli.py`
- `tests/unit/test_grid_artifact_policy.py`
- `tests/unit/test_grid_no_tradability_claims.py`
- `tests/integration/test_grid_tiny_fixture.py`
- `tests/integration/test_grid_registry_tempdb.py`
- `tests/integration/test_grid_fast_path_parity_gate.py`
- `tests/integration/test_grid_reference_fallback.py`
- `tests/integration/test_grid_cli_help.py`

Handoff:

- `handoffs/ASV1-P20.md`

These files were staged explicitly by path for the implementation commit. No
`runs/` path was staged.

## Validation Results

Passed:

- `python -m pytest tests/unit tests/integration tests/parity` - PASS, 429
  passed.
- Focused ASV1-P20 suite - PASS, 23 passed.
- `python -m pytest tests/unit/test_grid_expansion_count.py tests/unit/test_grid_max_combination_rejection.py tests/unit/test_grid_deterministic_ordering.py` - PASS, 3 passed.
- `python -m pytest tests/unit/test_grid_leaderboard_schema.py tests/unit/test_grid_output_schemas.py tests/unit/test_grid_manifest_fields.py` - PASS, 3 passed.
- `PYTHONPATH=src python -m alpha_system.cli grid run --help` - PASS.
- `python -m compileall src` - PASS.
- `git diff --check` - PASS.
- `find artifacts/strategy_grids -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` - PASS, no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - PASS, no output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - PASS, no output.
- `git ls-files runs` - PASS, no output.
- `git diff --cached --name-only | grep '^runs/'` - PASS after staging, no output.

Command exceptions / unavailable tools:

- `python -m pytest tests/unit/experiments tests/integration/test_grid_tiny_fixture.py tests/unit/cli/test_grid_cli.py || true` - pytest reported `ERROR: file or directory not found: tests/unit/experiments`; command exited 0 only because the spec includes `|| true`.
- `alpha grid run --help` - unavailable in this shell: `/bin/bash: line 1: alpha: command not found`.
- `python -m ruff check src tests || true` - ruff unavailable: `/usr/bin/python: No module named ruff`.
- `python -m mypy src || true` - mypy unavailable: `/usr/bin/python: No module named mypy`.

## Artifact Policy

No full grid outputs, generated `artifacts/strategy_grids/**` files, temporary
multiprocessing outputs, local SQLite/DB/journal/WAL files, Parquet/Arrow/Feather
files, raw/canonical data, generated factor/label/signal stores, logs, caches,
model binaries, full trade logs, or heavy artifacts were staged or committed.

All CLI and runner tests write grid outputs and registry DBs under temp paths.
The example config is bounded and has no real data references.

## Safety Boundary

No broker, live, paper, order-routing, deployment, candidate-promotion, or
production execution behavior was introduced. Grid outputs use research-evidence
language only and do not make alpha or tradability claims. The README snapshot
was updated compactly for ASV1-P20 complete / ASV1-P21 next while preserving the
existing safety boundaries.

## Risk Status

- R-007: mitigated by finite parameter validation, `max_combinations`, and
  overflow tests.
- R-009: mitigated by reference-default execution and no second PnL truth.
- R-010: mitigated by P19 parity gate before fast acceleration.
- R-014: mitigated by output language checks and evidence-only docs.
- R-015: mitigated; no promotion or approval path exists.
- R-016: mitigated by rejected-config and failed-step visibility.
- R-033: mitigated by non-zero default cost and explicit zero-cost rejection.
- R-035: mitigated by fast-path gate and reference fallback tests.
- R-036: mitigated by deterministic long/short fixture runs plus parity-gated
  fast/reference coverage.
- R-037: mitigated by temp-path CLI tests and output path guards.
- R-039: mitigated by Parquet audit and no generated columnar outputs.

## Known Limitations

- The MVP uses tiny synthetic correctness fixtures only; no real data IO grid is
  implemented.
- Grid configs are JSON in this phase.
- Survivor-based management workflow is represented only as the ASV1-P21 seam.
- Local multiprocessing is not needed for the tiny MVP fixture runner and no Ray
  or distributed path was added.
- The `alpha` console script is not installed in this shell; source-tree CLI
  help passes with `PYTHONPATH=src`.

## Recommended Review Focus

Review should focus on bounded search discipline, grid discipline order,
rejected-config visibility, manifest completeness, registry row fidelity,
fast-path gate strictness, reference fallback behavior, cost-model rejection,
artifact policy, and absence of broker/live/paper scope or unsupported claim
language.

## Next State

Ready for Ralph handoff validation and fresh Claude review. Ralph owns review,
verdict parsing, done-check, PR, CI, and merge gates.
