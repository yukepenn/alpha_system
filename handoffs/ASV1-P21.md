# ASV1-P21 Handoff - Management Grid Engine

## Status

Implemented the survivor-gated bounded Management Grid Engine. Codex did not
run Claude, reviewer, verdict parsing, PR creation, merge, broker/live/paper
scope, order routing, deployment, or PASS marking.

## Survivor Workflow Summary

`alpha management grid` now supports ASV1-P21 survivor-gated execution for
management-grid specs. Legacy management config shapes remain validation-only
and do not execute. The enforced workflow order is:

1. Factor diagnostics.
2. Simple signal grid.
3. Simple management baseline.
4. Survivor-only management grid.
5. Future finalist execution validation.

## Survivor Record Schema

`src/alpha_system/experiments/survivors.py` defines `SurvivorRecord` with all
required fields:

- `candidate_id`
- `source_run_id`
- `factor_versions`
- `label_versions`
- `strategy_version`
- `baseline_management_config`
- `baseline_portfolio_config`
- `source_grid_config_hash`
- `survivor_eligibility_reason`
- `warnings`
- `review_status`
- `allowed_management_grid_scope`

Human-readable field names from the spec are normalized to canonical
snake_case. `review_status` is required and validated.

## Eligibility And Gate Behavior

`candidate_policy.py` blocks execution unless the selected survivor has an
eligible review status, source grid hash, survivor reason, finite allowed
parameter paths, and a declared scope that covers the requested grid paths and
`max_combinations`. Missing survivor records or out-of-scope parameters produce
visible failures. Validation-only legacy configs do not run a grid.

## Grid Outputs

`management_outputs.py` writes the required local-only files:

- `baseline_comparison.csv`
- `leaderboard.csv`
- `rejected_configs.csv`
- `monthly_breakdown.csv`
- `cost_sensitivity.csv`
- `run_manifest.json`
- `warnings.json`
- `survivor_eligibility_summary.json`

Output paths inside the repo are constrained to
`artifacts/management_studies`; tests and example executions use temp paths.

## Rejected Config Behavior

`ManagementGridSpec` requires finite parameter lists and `max_combinations`.
Overflow raises `ManagementGridExpansionError` before materialization with a
visible rejected-grid reason. Scalar, empty, wildcard, and open-ended parameter
declarations are rejected. Runtime and declarative rejection-rule failures are
written to `rejected_configs.csv` with reasons.

## Overfit Controls

`overfit_controls.py` records survivor-only entry, finite lists,
`max_combinations`, path-dependent management warnings, rejected count, and a
candidate-decision status of `not_made_by_management_grid`. Warnings are
retained in `warnings.json` and the manifest.

## Execution Truth And Registry

Management-grid execution uses `run_reference_backtest_with_management`, which
reuses reference fills, costs, accounting, equity, and trade-journal
containers. Fast mode is parity-gated through P19 certification; unsupported
or uncertified feature sets route to reference fallback when allowed or fail
closed when fallback is disabled. The grid does not introduce a second PnL
truth.

Registry integration records management-grid runs in the existing `grid_runs`
table via temp SQLite DBs only. The registry row uses
`engine_version=management_grid_v1` and `decision_status=management_grid_recorded`.

## Files Changed And Staged

Source:

- `src/alpha_system/experiments/management_grid.py`
- `src/alpha_system/experiments/survivors.py`
- `src/alpha_system/experiments/candidate_policy.py`
- `src/alpha_system/experiments/overfit_controls.py`
- `src/alpha_system/experiments/management_outputs.py`
- `src/alpha_system/cli/management.py`

Docs/configs:

- `docs/MANAGEMENT_GRID_WORKFLOW.md`
- `docs/SURVIVOR_POLICY.md`
- `configs/management/grid_examples/tiny_management_grid.json`
- `README.md`

Tests:

- `tests/unit/experiments/test_management_grid_expansion.py`
- `tests/unit/experiments/test_management_grid_limits.py`
- `tests/integration/test_management_grid_tiny_fixture.py`
- `tests/unit/cli/test_management_grid_cli.py`
- `tests/unit/test_survivor_eligibility_gate.py`
- `tests/unit/test_survivor_record_schema.py`
- `tests/unit/test_management_grid_max_combinations.py`
- `tests/unit/test_management_grid_rejected_reasons.py`
- `tests/unit/test_management_grid_baseline_comparison.py`
- `tests/unit/test_management_grid_cost_sensitivity.py`
- `tests/unit/test_management_grid_monthly_breakdown.py`
- `tests/unit/test_management_grid_warnings.py`
- `tests/integration/test_management_grid_registry_tempdb.py`
- `tests/unit/test_management_grid_no_auto_approval.py`
- `tests/unit/test_management_grid_requires_review_status.py`
- `tests/integration/test_management_grid_cli_execution.py`
- `tests/unit/test_management_grid_artifact_policy.py`
- `tests/unit/test_management_grid_no_tradability_claims.py`

Handoff:

- `handoffs/ASV1-P21.md`

These files were staged explicitly by path. No `runs/` path is included.

## Validation Results

Passed:

- `python -m pytest tests/unit tests/integration` - PASS, 440 passed.
- `python -m pytest tests/unit/experiments/test_management_grid_expansion.py tests/unit/experiments/test_management_grid_limits.py tests/integration/test_management_grid_tiny_fixture.py tests/unit/cli/test_management_grid_cli.py || true` - PASS, 7 passed.
- `python -m pytest tests/unit/test_survivor_eligibility_gate.py tests/unit/test_management_grid_max_combinations.py tests/unit/test_management_grid_no_auto_approval.py` - PASS, 4 passed.
- `PYTHONPATH=src python -m alpha_system.cli management grid --help` - PASS.
- `python -m compileall src` - PASS.
- `git diff --check` - PASS.
- `PYTHONPATH=src python -m alpha_system.cli management grid --config configs/management/grid_examples/tiny_management_grid.json --output-dir /tmp/alpha_system_p21_example --json` - PASS, completed 2 configs, rejected 0, output under `/tmp`.
- `find artifacts/management_studies -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` - PASS, no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` - PASS, no output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - PASS, no output.
- `git ls-files runs` - PASS, no output.

Command exceptions / unavailable tools:

- `python -m alpha_system.cli management grid --help` - failed in the plain shell with `/usr/bin/python: Error while finding module specification for 'alpha_system.cli' (ModuleNotFoundError: No module named 'alpha_system')`. The repo is source-layout and not installed in this shell; the same command succeeds with `PYTHONPATH=src`, and pytest uses `pythonpath = ["src"]` from `pyproject.toml`.
- `alpha management grid --help || true` - console script unavailable: `/bin/bash: line 1: alpha: command not found`.
- `python -m ruff check src tests || true` - ruff unavailable: `/usr/bin/python: No module named ruff`.
- `python -m mypy src || true` - mypy unavailable: `/usr/bin/python: No module named mypy`.

## Artifact Policy

No generated management-grid outputs, DBs, Parquet/Arrow/Feather files,
logs, raw/canonical data, generated factor/label/signal stores, full trade
logs, generated equity curves, caches, model artifacts, heavy artifacts, or
`runs/` paths are intended to be staged or committed.

The example run wrote to `/tmp/alpha_system_p21_example`. Tests write outputs
and temp registry DBs under pytest temp directories.

## Safety Confirmations

- No automatic candidate decision is made by the grid.
- No promotion decision is recorded by the grid.
- No management-grid outputs were committed.
- No broker, live, paper, order-routing, deployment, or production execution
  behavior was introduced.
- No unsupported claim language was introduced in management-grid outputs,
  docs, configs, or README.
- Reference 1-minute execution remains the single PnL truth.
- Fast path remains acceleration-only and parity-gated.
- README snapshot was updated compactly for ASV1-P21 complete / ASV1-P22 next
  with unchanged safety boundaries.

## Known Limitations

- The exact plain `python -m alpha_system.cli management grid --help` command
  requires the package to be installed or `PYTHONPATH=src` in this shell.
- `docs/MANAGEMENT_OVERFIT_POLICY.md` still reflects pre-P21 validation-only
  wording; updating it was outside the allowed path list for this phase.
- Execution uses tiny synthetic correctness fixtures only. No real data IO,
  finalist execution validation, or broader event-driven engine scope was
  added.
- Management-grid registry rows reuse the existing `grid_runs` table until the
  future registry-hardening phase.

## Recommended Review Focus

Review should focus on survivor eligibility enforcement, finite parameter and
`max_combinations` handling, rejected-config visibility, output schemas,
baseline comparison, cost/monthly summaries, overfit warnings, temp-DB registry
recording, no promotion decision, reference/parity-gated execution behavior,
artifact policy, README snapshot wording, and absence of broker/live/paper
scope or unsupported claim language.
