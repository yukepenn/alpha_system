# RT-P06 Handoff - Diagnostics Report Contracts

Campaign: `ALPHA_RESEARCH_RUNTIME_MVP`  
Phase: `RT-P06` - Diagnostics Report Contracts  
Executor: Codex  
Status: implementation complete; review not run by executor

## Scope Completed

- Added `alpha_system.runtime.diagnostics.contracts` with immutable,
  reference-only `DiagnosticsRunSpec` and `DiagnosticsRunRecord` contracts.
- Added diagnostics references for RT-P04 / RT-P05 runtime objects:
  `RuntimePlanRef`, `DiagnosticsRunSpecRef`, `StudyRunRecordRef`, and
  `DiagnosticsReportRef`.
- Reused the established RT-P05 `StudyRunResultState` diagnostics states:
  `DIAGNOSTICS_READY`, `DIAGNOSTICS_RUNNING`, `DIAGNOSTICS_COMPLETE`,
  `DIAGNOSTICS_FAILED`, plus terminal `REJECTED`, `INCONCLUSIVE`, and
  `BLOCKED`.
- Linked failed, rejected, inconclusive, and blocked diagnostics outcomes to
  visible RT-P05 `RunRejectionReason` records.
- Added `alpha_system.runtime.diagnostics.report` with `DiagnosticsReport`,
  `DiagnosticsQualityGate`, scalar-only coverage / quality summaries, explicit
  limitations, lineage refs, non-promotional flags, and raw/heavy data guards.
- Added focused diagnostics unit tests and durable documentation.
- Updated the README snapshot for RT-P06 progress, next phase RT-P07, the new
  diagnostics package/doc, no new CLI surface, and unchanged safety boundaries.

## Explicit Staging List For Ralph

No files were staged by Codex. Per executor instructions, Ralph should stage
only these commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/diagnostics/__init__.py`
- `src/alpha_system/runtime/diagnostics/contracts.py`
- `src/alpha_system/runtime/diagnostics/report.py`
- `tests/unit/runtime/diagnostics/test_contracts.py`
- `tests/unit/runtime/diagnostics/test_report.py`
- `docs/research_runtime/DIAGNOSTICS_CONTRACTS.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P06.md`

No `runs/` path is included. No
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P06/**` files were created by Codex;
fresh review and verdict artifacts are owned by Ralph/reviewer.

## Git Status

`git status --short` was not run. The executor safety override explicitly
forbade `git status`, `git diff`, staging, committing, and pushing. No
`git add`, `git commit`, `git push`, `git status`, or `git diff` command was
run by Codex.

## Validation Commands

- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && printf 'RUN_STOP_PRESENT\n' || printf 'RUN_STOP_ABSENT\n'`
  - Result: exit 0, `RUN_STOP_ABSENT`.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P06/STOP && printf 'PHASE_STOP_PRESENT\n' || printf 'PHASE_STOP_ABSENT\n'`
  - Result: exit 0, `PHASE_STOP_ABSENT`.
- `python -m ruff format src/alpha_system/runtime/diagnostics/__init__.py src/alpha_system/runtime/diagnostics/contracts.py src/alpha_system/runtime/diagnostics/report.py tests/unit/runtime/diagnostics/test_contracts.py tests/unit/runtime/diagnostics/test_report.py`
  - Result: exit 0, final run reported `5 files left unchanged`.
- `python -m ruff check --fix src/alpha_system/runtime/diagnostics/__init__.py src/alpha_system/runtime/diagnostics/contracts.py src/alpha_system/runtime/diagnostics/report.py tests/unit/runtime/diagnostics/test_contracts.py tests/unit/runtime/diagnostics/test_report.py`
  - Result: exit 0, `Found 2 errors (2 fixed, 0 remaining)`.
- `python -m ruff check src/alpha_system/runtime/diagnostics/__init__.py src/alpha_system/runtime/diagnostics/contracts.py src/alpha_system/runtime/diagnostics/report.py tests/unit/runtime/diagnostics/test_contracts.py tests/unit/runtime/diagnostics/test_report.py`
  - Result: exit 0, `All checks passed!`.
- `python -c "import alpha_system.runtime.diagnostics.contracts"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not put `src` on `PYTHONPATH` for raw
    `python -c`, matching the RT-P05 executor environment.
- `python -c "import alpha_system.runtime.diagnostics.report"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not put `src` on `PYTHONPATH` for raw
    `python -c`, matching the RT-P05 executor environment.
- `PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.contracts"`
  - Result: exit 0.
- `PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.report"`
  - Result: exit 0.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/diagnostics -q`
  - Result: exit 0, `24 passed`.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0, `106 passed`.
- `test -f docs/research_runtime/DIAGNOSTICS_CONTRACTS.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0, empty output.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- `git diff --cached --name-only`
  - Reason: explicitly forbidden by the executor safety override, and Codex did
    not stage any files.
- Claude review, `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    reviewer orchestration and verdict parsing.
- `python tools/verify.py --all` and `python tools/hooks/canary_runner.py`
  - Reason: the spec requested narrow RT-P06 validation; lane-wide checks are
    owned by Ralph unless shared behavior beyond the new diagnostics package is
    broadened.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created or edited by Codex.
- No review artifacts were created by Codex.
- No files were staged by Codex. Therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- `git diff --cached --name-only` was not run because the executor safety
  override forbade `git diff` and Codex did no staging.
- Explicit staging is confirmed as Ralph-owned; the staging list above contains
  only commit-eligible RT-P06 paths.

## README Snapshot Confirmation

`README.md` now states the RT-P06 snapshot as `RT-P06` complete / `7 of 27`,
next phase `RT-P07` - Factor Diagnostics Runtime, the new shared diagnostics
contracts package `alpha_system.runtime.diagnostics` with `contracts`
(`DiagnosticsRunSpec` / `DiagnosticsRunRecord`) and `report`
(`DiagnosticsReport` / `DiagnosticsQualityGate`), the new
`docs/research_runtime/DIAGNOSTICS_CONTRACTS.md` doc, no new `alpha runtime`
CLI surface, and unchanged local-first / accepted-DatasetVersion-only /
no-provider / no-broker / no-claim safety boundaries.

## Caveats And RT-P07-RT-P11 Follow-Ups

- The current rejection linkage uses the RT-P05 `RunRejectionReason` surface so
  RT-P06 does not redefine the fuller `RejectionReasonRecord` scoped to RT-P15.
- `alpha_system.runtime.diagnostics.__all__` intentionally remains empty while
  symbols resolve lazily, matching the existing `alpha_system.runtime.contracts`
  scaffold pattern and preserving the RT-P02 package-skeleton expectation.
- RT-P07 through RT-P11 should specialize `DiagnosticsReport` with
  family-specific descriptive summaries only. They should keep raw diagnostic
  outputs local-only and attach only scalar summaries or references.
- Tests are synthetic and in-memory only. No data resolver, FeatureStore,
  LabelStore, provider, broker, paper/live/order, diagnostics math, signal
  probe, grid, cost stress, backtest, strategy, or portfolio behavior was run.
