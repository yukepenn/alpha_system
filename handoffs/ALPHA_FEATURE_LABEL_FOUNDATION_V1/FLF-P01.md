# FLF-P01 Handoff

Campaign: `ALPHA_FEATURE_LABEL_FOUNDATION_V1`
Phase: `FLF-P01` - Entry Contract and DatasetVersion Consumption
Lane: YELLOW
Executor: Codex

## Summary

Created the `alpha_system.features` package root and the read-only
DatasetVersion consumption adapter at `alpha_system.features.consumption`.

The adapter:

- resolves one DatasetVersion through
  `alpha_system.data.foundation.version_registry.resolve_dataset_version`;
- requires lifecycle state `VERSIONED` or `READY_FOR_RESEARCH`;
- delegates quality, coverage, manifest, code-hash, config-hash, and
  quality-report hash checks to the existing DatasetVersion prerequisite
  methods;
- reconstructs records only through `CanonicalBarRecord.from_mapping`,
  `CanonicalBBORecord.from_mapping`, and `DenseGridBarRecord.from_mapping`;
- requires reconstructed `data_version` to match the accepted DatasetVersion id;
- routes every partition use through
  `require_governance_metadata_for_locked_partition_use(...)`;
- keeps each accepted handle bound to exactly one DatasetVersion provenance
  line.

Added synthetic unit tests for importability, accepted resolution, fail-closed
missing/inadmissible/blocking inputs, raw provider-shaped field rejection,
locked-partition contamination-metadata rejection, `data_version` mismatch
rejection, and distinct Databento/IBKR DatasetVersion handles.

Added the durable entry-contract doc and updated the README snapshot for FLF-P01.

No config placeholder was added because the adapter needs no config values.

## Staged Files

None. The executor was explicitly instructed not to run `git add`, `git
commit`, `git push`, `git status`, or `git diff`, and to leave changes unstaged
for Ralph.

Commit-eligible files created or modified for Ralph to stage explicitly:

```text
README.md
docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md
handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P01.md
src/alpha_system/features/__init__.py
src/alpha_system/features/consumption.py
tests/unit/features/test_consumption.py
```

No `configs/features/**` path was created.

## Validation Results

Requested FLF-P01 validation commands and safe supplementary scans:

```text
git status --short
  skipped: executor prompt explicitly forbids running git status

python -c "import alpha_system.features.consumption"
  exit 1
  stderr: ModuleNotFoundError: No module named 'alpha_system'
  reason: the bare shell did not have the repo's src directory on PYTHONPATH

PYTHONPATH=src python -c "import alpha_system.features.consumption"
  exit 0

python tools/verify.py --smoke
  exit 0
  output: none

python -m pytest tests/unit/features -q
  exit 0
  output: 9 passed

test -f docs/feature_label_foundation/ENTRY_CONTRACT_CONSUMPTION.md
  exit 0

git ls-files runs
  exit 0
  output: none

grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" \
  src/alpha_system/features 2>/dev/null \
  | grep -v "from_mapping\|resolve_dataset_version" \
  || echo "no direct provider/file readers found in feature code"
  exit 0
  output: no direct provider/file readers found in feature code

git ls-files | grep -E '\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|dbn|zst|log)$' \
  | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"
  exit 0
  output: no committed heavy/db/log artifacts
```

STOP check before validation:

```text
test -f runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/STOP && printf STOP_PRESENT || printf NO_STOP
  exit 0
  output: NO_STOP
```

## Artifact Policy

- No staging or commit was performed by the executor.
- `git ls-files runs` returned no tracked `runs/` paths.
- No run-local `handoff.md`, `review.md`, `verdict.json`, checks, or repair
  attempt artifacts were created or staged.
- No raw market data, canonical data, feature values, label values, provider
  responses, parquet/arrow/feather files, DB/SQLite/WAL files, logs, caches, or
  heavy artifacts were created.
- No review artifact was created. Review and verdict are Ralph/reviewer-owned.

## Git Discipline

- Did not run `git add`, `git commit`, `git push`, `git status`, or `git diff`.
- Did not use `git add .` or `git add -A`.
- Did not force push.
- Left all changes unstaged for Ralph.

## DAG Metadata

- `parallel_safe: false`
- `must_run_alone: true`
- `merge_group: foundation`
- `conflicts_with: none`
- `resource_class: none`
- Disjoint-path analysis is not applicable because this is a run-alone
  bootstrap/core-contract phase.
- No shared-core collisions were introduced outside the allowed package root,
  docs, tests, README snapshot, and handoff.
- `ACTIVE_CAMPAIGN.md` was not written.

## Scope Confirmation

- The new feature/label consumption path consumes accepted DatasetVersions only.
- The adapter exposes canonical records through existing `from_mapping` loaders
  only.
- Inadmissible, missing, blocking-quality, and blocking-coverage DatasetVersions
  fail closed.
- Locked-test partition use without governance contamination metadata fails
  closed.
- Databento and IBKR DatasetVersions remain distinct handles and are not merged.
- Governance modules were not edited or duplicated.
- No raw provider file access, canonical/value materialization, external
  provider call, provider client import, broker/live/paper/order/account scope,
  deployment scope, strategy/backtest/portfolio scope, alpha search, alpha
  claim, tradability claim, profitability claim, or prohibited MVP lifecycle
  state was added.
