# RT-P01 Handoff — Runtime Entry Contract After Feature/Label

## Scope Completed

- Added the importable runtime package surface:
  - `src/alpha_system/runtime/__init__.py`
  - `src/alpha_system/runtime/entry_contract.py`
- Added fail-closed synthetic unit tests:
  - `tests/unit/runtime/test_entry_contract.py`
- Added durable entry-contract documentation:
  - `docs/research_runtime/ENTRY_CONTRACT.md`
- Updated the compact README campaign snapshot for RT-P01 complete / RT-P02 next.

The contract consumes `alpha_system.governance.study_input_pack.StudyInputPack`
and does not edit or re-implement governance, research, experiments, backtest,
features, labels, or data primitives. It performs no data access, registry
resolution, FeatureStore/LabelStore reads, provider calls, CLI work, diagnostics,
probe execution, cost stress, evidence drafting, candidate creation, trading, or
deployment behavior.

## Explicit File List

Executor-staged files: none. The prompt explicitly forbids the executor from
running `git add`, `git status`, `git diff`, `git commit`, or `git push`; Ralph
owns authoritative explicit staging.

Files created or edited for Ralph to stage explicitly:

- `src/alpha_system/runtime/__init__.py`
- `src/alpha_system/runtime/entry_contract.py`
- `tests/unit/runtime/test_entry_contract.py`
- `docs/research_runtime/ENTRY_CONTRACT.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P01.md`

No `configs/runtime/**` file was needed. No review artifact was created by the
executor.

## Validation

- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`: PASS;
  output `NO_STOP`.
- `git status --short`: SKIPPED. The executor safety override explicitly
  forbids `git status`; Ralph owns worktree/staging inspection.
- `python -c "import alpha_system.runtime.entry_contract"`: FAIL in this shell
  with `ModuleNotFoundError: No module named 'alpha_system'`; the bare shell did
  not have the `src/` package path installed.
- `PYTHONPATH=src python -c "import alpha_system.runtime.entry_contract"`: PASS.
- `python tools/verify.py --smoke`: PASS.
- `python -m pytest tests/unit/runtime -q`: PASS, `11 passed`.
- `test -f docs/research_runtime/ENTRY_CONTRACT.md`: PASS.
- `git ls-files runs`: PASS, empty output.
- `python -m ruff check src/alpha_system/runtime tests/unit/runtime`: PASS.
- `python tools/hooks/canary_runner.py`: PASS, all Frontier canaries passed.
- `python tools/verify.py --all`: FAIL, `13 failed, 2138 passed`. The failures
  are in existing Workflow 2/GitHub harness tests, not in `tests/unit/runtime`:
  `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` and
  twelve `tests/test_ralph_driver.py` cases covering provider-wired mock phase
  completion, resume, branch preparation, push-block resume, usage-limit state,
  and DAG-wave completion behavior.

## Artifact Audit

- `git ls-files runs` returned empty.
- No staging was performed by the executor.
- `git diff --cached --name-only` was not run because the prompt explicitly
  forbids `git diff`; no cached/staged set was modified by the executor.
- No `runs/`, data, DB, cache, log, parquet, arrow, feather, DBN, Zstd, model,
  raw provider, canonical, feature, label, or runtime value artifact was staged
  by the executor.
- Python may have generated local `__pycache__` files during tests; Ralph must
  not stage them.

## README Snapshot

`README.md` was updated per policy: RT-P01 is recorded as complete, RT-P02 is
named as next, the durable runtime entry contract module and
`docs/research_runtime/ENTRY_CONTRACT.md` are named, and no `alpha runtime` CLI
surface is claimed. The README update contains only no-claim safety boundary
language for broker/live/paper/order/account and alpha/tradability/profitability
scope.

## Caveats And Follow-Ups

- RT-P02 should extend the runtime package skeleton and naming conventions
  without changing this entry contract's fail-closed posture.
- RT-P03 must implement the actual `RuntimeInputPack` resolver: accepted
  DatasetVersion lifecycle resolution, no Databento+IBKR DatasetVersion merge,
  FeatureStore/LabelStore handle resolution, and locked-test governance
  contamination metadata checks.
- Ralph or the environment should ensure either the package is installed or
  `PYTHONPATH=src` is set when running bare `python -c` import checks.
