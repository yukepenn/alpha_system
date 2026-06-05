# FLF-P21 Handoff — Label Materialization Engine

## Scope Completed

Implemented the local-only label materialization engine in
`src/alpha_system/labels/engine.py`.

The engine:

- Builds deterministic `LabelMaterializationPlan` objects for approved
  governance-bound label definitions.
- Requires `AcceptedDatasetVersion` handles and canonical row mappings; input
  views are built through `alpha_system.features.consumption` and canonical
  `from_mapping` loaders only.
- Dispatches to the existing fixed-horizon, cost-adjusted, path, and event
  label family calculators.
- Enforces `MATERIALIZATION_ALLOWED`, DatasetVersion lifecycle
  `{VERSIONED, READY_FOR_RESEARCH}`, partition/locked-test metadata gates,
  labels-only consumer policy, label-as-feature rejection, and output paths
  under `ALPHA_DATA_ROOT`.
- Validates every `LabelValueRecord` for in-plan label version,
  timezone-aware `label_available_ts`, `label_available_ts >= horizon_end_ts`,
  and `label_available_ts >= LabelSpec.availability_time`.
- Supports dry-run planning without writing values and idempotent atomic JSONL
  writes for non-dry-run materialization.

Added scoped unit and integration tests using tiny inline synthetic fixtures
only. Added durable documentation and updated the README snapshot for FLF-P21.

## Files For Ralph To Stage

Executor staged files: none. I did not run `git add`, `git commit`,
`git push`, `git status`, or `git diff`.

Commit-eligible files created or edited:

- `src/alpha_system/labels/engine.py`
- `tests/unit/labels/test_label_engine.py`
- `tests/integration/labels/test_label_materialize.py`
- `docs/feature_label_foundation/LABEL_MATERIALIZATION.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P21.md`

No `runs/**` files were created or staged by the executor. No review artifacts,
`review.md`, or `verdict.json` were created.

## Git And Artifact State

- `git status --short`: not run because the executor prompt explicitly forbids
  `git status`. Ralph should run this outside the executor.
- `git ls-files runs`: passed; returned empty.
- `runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/STOP`: not present.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print`: passed;
  returned empty.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`: passed;
  returned empty.
- `find artifacts -type f -size +1M -print`: passed; returned empty.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`: passed;
  returned empty.

## Validation

Passed:

- `PYTHONPATH=src python -c "import alpha_system.labels.engine"`
- `python tools/verify.py --smoke`
- `python tools/verify.py --typecheck`
- `python -m ruff format --check src/alpha_system/labels/engine.py tests/unit/labels/test_label_engine.py tests/integration/labels/test_label_materialize.py`
- `python -m ruff check src/alpha_system/labels/engine.py tests/unit/labels/test_label_engine.py tests/integration/labels/test_label_materialize.py`
- `python -m pytest tests/unit/labels/test_label_engine.py -q` (`8 passed`)
- `python -m pytest tests/integration/labels/test_label_materialize.py -q`
  (`1 passed`)
- `python -m pytest tests/unit/labels/test_label_engine.py tests/integration/labels/test_label_materialize.py -q`
  (`9 passed`)
- `python -m pytest tests/unit/labels tests/integration/labels -q`
  (`43 passed`)
- `test -f docs/feature_label_foundation/LABEL_MATERIALIZATION.md`
- `python tools/hooks/canary_runner.py`

Failed or skipped:

- `python -c "import alpha_system.labels.engine"` failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because this bare shell
  does not put `src/` on `PYTHONPATH`. The same import passed with
  `PYTHONPATH=src`, and pytest/verify imported the module successfully.
- `git status --short` was not run due the explicit executor override.
- `python tools/verify.py --all` failed after final edits with
  `17 failed, 2047 passed`. The FLF-P21 label tests passed inside this run.
  The failures are outside the FLF-P21 label engine scope:
  - `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network`
  - Ralph driver provider/push/DAG resume tests in `tests/test_ralph_driver.py`
  - four pre-existing `tests/unit/features/test_feature_store.py` failures in
    feature-store request-gate fixtures.

## DAG And Boundary Confirmation

- FLF-P21 was treated as run-alone label integration work; no parallel/global
  coordinator files were edited.
- `ACTIVE_CAMPAIGN.md` was not edited.
- Governance modules and existing label family/contract modules were consumed,
  not edited.
- No raw provider access, external provider calls, Databento/IBKR calls,
  broker/live/paper/order/account scope, PR creation, merge, reviewer call, or
  Claude call was performed.
- No materialized label values, raw/canonical data, provider responses,
  SQLite/DB files, Parquet/Arrow/Feather files, logs, caches, or heavy artifacts
  were added to the repository.
- No alpha, profitability, tradability, production, strategy, backtest, or
  portfolio claim was added.
