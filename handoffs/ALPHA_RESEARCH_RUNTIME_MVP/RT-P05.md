# RT-P05 Handoff - StudyRunRecord, Manifest, and Runtime Artifact Contract

Campaign: `ALPHA_RESEARCH_RUNTIME_MVP`  
Phase: `RT-P05` - StudyRunRecord, Manifest, and Runtime Artifact Contract  
Executor: Codex  
Status: implementation complete; review not run by executor

## Scope Completed

- Added `alpha_system.runtime.contracts.run_record` with immutable, hashable
  `StudyRunRecord`, reference-only `StudyRunSpec` / manifest / artifact refs,
  legal runtime result states, and visible rejection reasons for terminal
  `REJECTED`, `INCONCLUSIVE`, and `BLOCKED` records.
- Added `alpha_system.runtime.contracts.manifest` with immutable, hashable
  `StudyRunManifest`, dataset / feature / label / code / config version and
  hash lineage, availability metadata references, optional cost-model version
  slot, deterministic `manifest_hash`, and a guard against `runs/**` path
  leakage into that hash.
- Added `alpha_system.runtime.contracts.artifacts` with immutable, hashable
  `RuntimeArtifactManifest` and artifact entries defaulting to
  `local_only=True` / `commit_allowed=False`; commit-allowed artifacts are
  restricted to tiny row-free summary kinds and heavy/value-bearing artifacts
  are blocked.
- Added scoped synthetic unit tests for run records, study-run manifests, and
  runtime artifact manifests.
- Added `docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`.
- Updated the README snapshot for RT-P05 progress, next phase RT-P06, the new
  runtime contract modules/doc, no new CLI surface, and unchanged safety
  boundaries.

## Explicit Staging List For Ralph

No files were staged by Codex. Per executor instructions, Ralph should stage
only these commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/contracts/run_record.py`
- `src/alpha_system/runtime/contracts/manifest.py`
- `src/alpha_system/runtime/contracts/artifacts.py`
- `tests/unit/runtime/contracts/test_run_record.py`
- `tests/unit/runtime/contracts/test_manifest.py`
- `tests/unit/runtime/contracts/test_artifacts.py`
- `docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05.md`

No `runs/` path is included. No
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05/**` files were created by Codex;
fresh review and verdict artifacts are owned by Ralph/reviewer.

## Git Status

`git status --short` was not run. The executor safety override explicitly
forbade `git status`, `git diff`, staging, committing, and pushing. No
`git add`, `git commit`, `git push`, `git status`, or `git diff` command was
run by Codex.

## Validation Commands

- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`
  - Result: exit 0, no run-level STOP file present.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P05/STOP`
  - Result: exit 0, no phase-level STOP file present.
- `python -m ruff format src/alpha_system/runtime/contracts/run_record.py src/alpha_system/runtime/contracts/manifest.py src/alpha_system/runtime/contracts/artifacts.py tests/unit/runtime/contracts/test_run_record.py tests/unit/runtime/contracts/test_manifest.py tests/unit/runtime/contracts/test_artifacts.py`
  - Result: exit 0, final run reported `6 files left unchanged`.
- `python -m ruff check src/alpha_system/runtime/contracts/run_record.py src/alpha_system/runtime/contracts/manifest.py src/alpha_system/runtime/contracts/artifacts.py tests/unit/runtime/contracts/test_run_record.py tests/unit/runtime/contracts/test_manifest.py tests/unit/runtime/contracts/test_artifacts.py`
  - Result: exit 0, `All checks passed!`.
- `python -c "import alpha_system.runtime.contracts.run_record, alpha_system.runtime.contracts.manifest, alpha_system.runtime.contracts.artifacts"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not put `src` on `PYTHONPATH` for raw
    `python -c`, matching the RT-P04 executor environment.
- `PYTHONPATH=src python -c "import alpha_system.runtime.contracts.run_record, alpha_system.runtime.contracts.manifest, alpha_system.runtime.contracts.artifacts"`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/contracts -q`
  - Result: exit 0, `61 passed`.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0, `82 passed`.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `test -f docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`
  - Result: exit 0.
- `test -f README.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0, empty output.
- `test ! -e reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P05`
  - Result: exit 0, no review artifact directory was created by Codex.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- `git diff --cached --name-only`
  - Reason: explicitly forbidden by the executor safety override, and Codex did
    not stage any files.
- Claude review, `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    reviewer orchestration and verdict parsing.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created or edited by Codex.
- The referenced run artifact phase directory was absent in this checkout, so
  no run-local `handoff.md`, `review.md`, `verdict.json`, or
  `repair_attempts/` artifact was written.
- No review artifacts were created by Codex.
- No files were staged by Codex. Therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- `git diff --cached --name-only` was not run because the executor safety
  override forbade `git diff` and Codex did no staging.

## README Snapshot Confirmation

`README.md` now states the RT-P05 snapshot as `RT-P05` complete / `6 of 27`,
next phase `RT-P06`, the new `run_record`, `manifest`, and `artifacts` runtime
contract modules, `docs/research_runtime/RUN_RECORD_AND_MANIFEST.md`, no new
`alpha runtime` CLI surface, and unchanged local-first / accepted-DatasetVersion
only / no-provider / no-broker / no-claim safety boundaries.

## Caveats

- `StudyRunResultState` is defined in `run_record.py` because the RT-P04
  `RuntimeLifecycleState` currently contains only pre-execution states. The
  record constructor accepts RT-P04 `RuntimeLifecycleState` values and rejects
  prohibited MVP states by enum construction.
- `RunRejectionReason` is intentionally minimal because the full
  `RejectionReasonRecord` decision-state contract is scoped to RT-P15.
- Tests are synthetic and in-memory only. No local data corpus, registry DB,
  raw provider files, FeatureStore values, LabelStore values, Databento calls,
  IBKR calls, diagnostics, probes, grids, cost runs, or audits were used.
