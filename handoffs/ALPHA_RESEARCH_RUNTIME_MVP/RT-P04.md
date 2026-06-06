# RT-P04 Handoff - StudyRunSpec and RuntimePlan Contracts

Campaign: `ALPHA_RESEARCH_RUNTIME_MVP`  
Phase: `RT-P04` - StudyRunSpec and RuntimePlan Contracts  
Executor: Codex  
Status: implementation complete; review not run by executor

## Scope Completed

- Added `alpha_system.runtime.contracts.run_spec` with immutable, hashable
  `RuntimeRequest`, `StudyRunSpec`, `RuntimeLifecycleState`, and
  `RuntimeContractError`.
- Added `alpha_system.runtime.contracts.plan` with immutable, hashable
  `RuntimePlan`, `RuntimePlanValidationResult`, and `validate_runtime_plan`.
- Runtime requests require approved governance `AlphaSpec` /
  `StudySpec` objects, the governance `StudyInputPack`, a target accepted
  `DatasetVersion` id, and an RT-P03 `RuntimeInputPack`.
- Runtime plans validate bounded jobs, campaign partition windows, partition
  and session binding to the `RuntimeInputPack`, signal-probe variant budget
  references through `experiments.limits.CombinationLimit`, required
  `double_cost` cost stress, locked/shadow contamination metadata, and locked
  test selection rejection.
- Added scoped synthetic unit tests under `tests/unit/runtime/contracts/`.
- Added `docs/research_runtime/RUN_SPEC_AND_PLAN.md`.
- Updated the README snapshot for RT-P04 progress, next phase RT-P05, new
  runtime contracts package/doc, no runtime CLI, and unchanged safety
  boundaries.

## Explicit Staging List For Ralph

No files were staged by Codex. Per executor instructions, Ralph should stage
only these commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/contracts/__init__.py`
- `src/alpha_system/runtime/contracts/run_spec.py`
- `src/alpha_system/runtime/contracts/plan.py`
- `tests/unit/runtime/contracts/test_run_spec.py`
- `tests/unit/runtime/contracts/test_plan.py`
- `docs/research_runtime/RUN_SPEC_AND_PLAN.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04.md`

No `configs/runtime/**` files were added or edited for RT-P04. No
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04/**` files were created by Codex;
fresh review is owned by Ralph/reviewer.

## Git Status

`git status --short` was not run. The executor safety override explicitly
forbade `git status`, `git diff`, staging, committing, and pushing. No
`git add`, `git commit`, `git push`, `git status`, or `git diff` command was
run by Codex.

## Validation Commands

- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P04/STOP`
  - Result: exit 0, no STOP file present at the run or phase STOP paths.
- `find runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP -name STOP -type f -print`
  - Result: exit 1, run directory absent:
    `find: 'runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP': No such file or directory`.
- `python -c "import alpha_system.runtime.contracts.run_spec, alpha_system.runtime.contracts.plan"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not put `src` on `PYTHONPATH` for raw `python -c`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.contracts.run_spec, alpha_system.runtime.contracts.plan"`
  - Result: exit 0.
- `python -m ruff format src/alpha_system/runtime/contracts/__init__.py src/alpha_system/runtime/contracts/run_spec.py src/alpha_system/runtime/contracts/plan.py tests/unit/runtime/contracts/test_run_spec.py tests/unit/runtime/contracts/test_plan.py`
  - Result: exit 0, `5 files left unchanged` on the final run.
- `python -m ruff check src/alpha_system/runtime/contracts/__init__.py src/alpha_system/runtime/contracts/run_spec.py src/alpha_system/runtime/contracts/plan.py tests/unit/runtime/contracts/test_run_spec.py tests/unit/runtime/contracts/test_plan.py`
  - Result: exit 0, `All checks passed!`.
- `python -m pytest tests/unit/runtime/contracts -q`
  - Result: exit 0, `18 passed`.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0, `39 passed`.
  - Note: an earlier run failed on the stale RT-P00 scaffold expectation that
    `alpha_system.runtime.contracts.__all__ == []`; the package surface now
    preserves that scaffold invariant while exposing RT-P04 names lazily.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `test -f docs/research_runtime/RUN_SPEC_AND_PLAN.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0, empty output.
- `test ! -e reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P04`
  - Result: exit 0, no review artifact directory was created by Codex.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- `git diff --cached --name-only`
  - Reason: explicitly forbidden by the executor safety override, and Codex did
    not stage any files.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created or edited by Codex.
- The referenced run artifact directory was absent in this checkout, so no
  run-local `handoff.md`, `review.md`, or `verdict.json` was written.
- No review artifacts were created; Claude review is owned by Ralph/reviewer.
- No files were staged by Codex. Therefore no staged `runs/` path or forbidden
  heavy/data/cache/log/DB artifact was introduced by this executor.
- `git diff --cached --name-only` was not run because the executor safety
  override forbade `git diff` and Codex did no staging.

## README Snapshot Confirmation

`README.md` now states the RT-P04 snapshot as `RT-P04` complete / `5 of 27`,
next phase `RT-P05`, the new `alpha_system.runtime.contracts` package with
`run_spec` and `plan`, the new
`docs/research_runtime/RUN_SPEC_AND_PLAN.md` documentation, no `alpha runtime`
CLI surface, and unchanged local-first / accepted-DatasetVersion-only /
no-provider / no-broker / no-alpha-claim safety boundaries.

## Caveats

- `RuntimePlan` records a finite `CombinationLimit` budget reference for
  signal probes; full bounded-grid and variant-budget enforcement remains
  scoped to RT-P13.
- Tests use synthetic in-memory governance and runtime-input metadata only. No
  local data corpus, registry DB, raw provider files, FeatureStore values,
  LabelStore values, Databento calls, IBKR calls, diagnostics, probes, grids,
  cost runs, or audits were used.
- The package namespace keeps `__all__ == []` to satisfy the existing runtime
  scaffold test, while resolving the RT-P04 symbols via lazy module attributes.
