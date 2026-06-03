# DATA-P01 Handoff - Data Package Skeleton and Naming

## Scope Completed

Implemented an additive `alpha_system.data.foundation` namespace under the
pre-existing `src/alpha_system/data/` package. Existing data modules were not
deleted, renamed, or modified.

Skeleton layout:

- `alpha_system.data.foundation.sources`: `DataSourceProfile`,
  `LocalDataRootPolicy`, `DataAccessMode`
- `alpha_system.data.foundation.ibkr`: `IBKRConnectionProfile`,
  `IBKRClientIdPolicy`, `run_connection_doctor` placeholder
- `alpha_system.data.foundation.requests`: `HistoricalRequestSpec`,
  `HistoricalRequestManifest`, `HistoricalChunkRecord`,
  `HistoricalPullLedger`, `ProviderErrorRecord`, `RequestPacingPolicy`,
  `DataIngestionRunRecord`
- `alpha_system.data.foundation.bars`: `RawDataObject`, `ParsedBarRecord`,
  `CanonicalBarRecord`, `TimestampSemanticsPolicy`
- `alpha_system.data.foundation.instruments`: `InstrumentMasterRecord`,
  `FuturesContractRecord`, `ContractDetailsSnapshot`
- `alpha_system.data.foundation.sessions`: `SessionTemplate`,
  `TradingCalendarRecord`
- `alpha_system.data.foundation.rolls`: `RollPolicy`, `RollCalendarRecord`
- `alpha_system.data.foundation.series`: `ContinuousFuturesSeriesRecord`,
  `DatedFuturesSeriesRecord`
- `alpha_system.data.foundation.batches`: `SymbolBatchPlan`,
  `MicroBatchPolicy`
- `alpha_system.data.foundation.datasets`: `DatasetVersion`,
  `DataQualityReport`, `CoverageReport`, `DatasetPartitionPlan`

The skeleton contains importable placeholders only. It performs no network access,
filesystem writes, credential reads, registry writes, validation, persistence, or
provider calls at import time.

## Naming Conventions

`docs/data_foundation/NAMING.md` defines the canonical object names, ID prefixes,
canonical modules, Python module naming, file naming, commit-eligible directory
roots, local-only `ALPHA_DATA_ROOT` pointer, and run-artifact boundaries.

The naming doc records that the new skeleton lives under
`src/alpha_system/data/foundation/` alongside the existing `alpha_system.data`
modules, avoiding collisions with prior sibling modules such as `bar_schema.py`,
`calendar.py`, `contracts.py`, `paths.py`, `quality.py`, `sessions.py`,
`storage.py`, `universe.py`, `validation.py`, and `versions.py`.

## Commit-Eligible Files

Curated files intended for explicit staging:

- `README.md`
- `configs/data/README.md`
- `docs/data_foundation/NAMING.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P01.md`
- `src/alpha_system/data/foundation/__init__.py`
- `src/alpha_system/data/foundation/bars.py`
- `src/alpha_system/data/foundation/batches.py`
- `src/alpha_system/data/foundation/datasets.py`
- `src/alpha_system/data/foundation/ibkr.py`
- `src/alpha_system/data/foundation/instruments.py`
- `src/alpha_system/data/foundation/requests.py`
- `src/alpha_system/data/foundation/rolls.py`
- `src/alpha_system/data/foundation/series.py`
- `src/alpha_system/data/foundation/sessions.py`
- `src/alpha_system/data/foundation/sources.py`
- `templates/data/README.md`
- `tests/unit/data/test_data_foundation_package_skeleton.py`

Explicit staging was attempted with:

```bash
git --git-dir=/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-alpha_data_foundation_v1-data-p01 --work-tree=/home/yuke_zhang/projects/alpha_system-alpha_data_foundation_v1-data-p01 add README.md configs/data/README.md docs/data_foundation/NAMING.md handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P01.md src/alpha_system/data/foundation/__init__.py src/alpha_system/data/foundation/bars.py src/alpha_system/data/foundation/batches.py src/alpha_system/data/foundation/datasets.py src/alpha_system/data/foundation/ibkr.py src/alpha_system/data/foundation/instruments.py src/alpha_system/data/foundation/requests.py src/alpha_system/data/foundation/rolls.py src/alpha_system/data/foundation/series.py src/alpha_system/data/foundation/sessions.py src/alpha_system/data/foundation/sources.py templates/data/README.md tests/unit/data/test_data_foundation_package_skeleton.py
```

The command failed with exit 128:

```text
fatal: Unable to create '/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-alpha_data_foundation_v1-data-p01/index.lock': Read-only file system
```

Reason: the sandbox permits repository file writes but exposes the linked
worktree's `.git` metadata as read-only. No files were staged; `git diff
--cached --name-only` returned empty.

## Validation Results

- `git status --short` failed with exit 128:
  `fatal: this operation must be run in a work tree`
  - Reason: this linked worktree's common Git config has `core.bare=true`.
    The equivalent explicit linked-worktree command succeeded:
    `git --git-dir=/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-alpha_data_foundation_v1-data-p01 --work-tree=/home/yuke_zhang/projects/alpha_system-alpha_data_foundation_v1-data-p01 status --short`.
- `python -c "import alpha_system.data"` failed with exit 1:
  `ModuleNotFoundError: No module named 'alpha_system'`
  - Reason: the shell environment does not have the src-layout package installed
    and the exact command does not set `PYTHONPATH=src`.
  - Source-path import check passed:
    `PYTHONPATH=src python -c "import alpha_system.data; import alpha_system.data.foundation"`.
- `python tools/verify.py --smoke` passed.
- `python -m pytest tests/unit/data -q` passed: `3 passed in 0.01s`.
- `test -f docs/data_foundation/NAMING.md` passed.
- `git ls-files runs` passed and returned empty.

## Artifact Policy

- `runs/**` remains local-only and was not staged or committed.
- No run-local `handoff.md`, `review.md`, `verdict.json`, checks, or repair
  artifact was created or staged.
- No raw data, canonical data, provider response, local DB, cache, log, Parquet,
  Arrow, Feather, pickle, NumPy, model artifact, credential, account, broker,
  paper, live, order-routing, real-time, or deployment artifact was added.
- Existing sample files under `configs/data/` were left unchanged; DATA-P01 added
  only the placeholder README there.

## Explicit Staging

Staging was attempted with explicit file paths only. `git add .` and `git add -A`
were not used. Commit and push were not possible because the `.git` worktree index
is read-only in this execution sandbox. The cached diff remained empty, so no
`runs/` path or forbidden artifact path was staged.

## Repair Update

Ralph initially stopped this phase at `GIT_PHASE_BLOCKED` because the curated
files existed in the linked worktree but had not been committed. The local Git
configuration for the main worktree had `core.bare=true`, which also caused
root-level `git status` checks to fail. The repair restored the repository to a
normal worktree configuration with `core.bare=false`, preserved the existing
DATA-P01 content, and re-ran explicit-path staging for only the curated files
listed above. No `runs/**` path or forbidden artifact path was staged.

CI then failed because the original data test basename collided with the
pre-existing governance test module `tests/unit/governance/test_package_skeleton.py`
under full-suite pytest collection. The repair renamed the data smoke test to
`tests/unit/data/test_data_foundation_package_skeleton.py` without changing test
coverage or weakening assertions.

## Scope Boundaries

No object validation logic, field-level schemas, registry integration, persistence
integration, IBKR connection implementation, broker surface, live surface, paper
surface, order-routing behavior, real-time feed behavior, real data ingestion,
alpha claim, profitability claim, tradability claim, or production-readiness claim
was added.
