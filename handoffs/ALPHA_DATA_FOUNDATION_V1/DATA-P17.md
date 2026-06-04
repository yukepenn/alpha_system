# DATA-P17 Handoff - Dataset Version Registry Integration

## Scope Executed

Implemented DATA-P17 under `src/alpha_system/data/foundation/`.

`DatasetVersion` is now a frozen, fail-closed dataclass with exactly these
fields:

- `dataset_version_id`
- `source`
- `symbol_universe`
- `bar_size`
- `what_to_show`
- `start_ts`
- `end_ts`
- `contract_universe`
- `roll_policy_id`
- `manifest_hash`
- `code_hash`
- `config_hash`
- `quality_report_hash`
- `created_at`

Construction and `from_mapping(...)` reject missing fields, extra fields, blank
or malformed IDs, empty or duplicate universes, malformed SHA-256 hashes,
non-timezone-aware timestamps, and `end_ts < start_ts` with
`DataFoundationValidationError`.

## Lifecycle And Hash Binding

Added `compute_quality_report_hash(...)` and
`DatasetVersion.require_lifecycle_prerequisites(...)`.

The lifecycle gate accepts only `VERSIONED` and `READY_FOR_RESEARCH` data
admissibility states. It requires:

- a non-blocking `DataQualityReport` for the same `dataset_version_id`;
- a non-blocking `CoverageReport` for the same `dataset_version_id`;
- successful `CoverageReport.require_linked_quality_report(...)`;
- a source manifest object or mapping exposing `manifest_hash`;
- caller-supplied code and config hashes;
- exact binding of `manifest_hash`, `code_hash`, `config_hash`, and
  `quality_report_hash`.

Missing reports, blocking reports, mismatched dataset IDs, missing manifest
references, and mis-bound manifest/code/config/quality hashes fail closed. The
object remains a data admissibility record only and does not imply research
approval, alpha value, tradability, or production readiness.

## Registry Integration

Added `src/alpha_system/data/foundation/version_registry.py` with:

- `persist_dataset_version(registry_path, dataset_version)`
- `resolve_dataset_version(registry_path, dataset_version_id)`

The adapter reuses `core.registry.resolve_registry_path`,
`is_local_only_registry_path`, `init_registry`, and `connect_registry`. It does
not open an ad-hoc SQLite connection.

Registry writes call `DatasetVersion.require_versioned_prerequisites(...)`
before insert, so persistence requires a linked non-blocking quality report,
non-blocking coverage report, source manifest hash binding, and caller-supplied
code/config hash bindings.

The existing schema version 1 `dataset_versions` table was sufficient. No
migration was required and no `src/alpha_system/core/**` file was modified.
The adapter maps:

- `data_version` -> `DatasetVersion.dataset_version_id`
- `created_at` -> `DatasetVersion.created_at`
- `source_uri` -> `DatasetVersion.source`
- `content_hash` -> `DatasetVersion.manifest_hash`
- `config_hash` -> `DatasetVersion.config_hash`
- `metadata_json` -> complete DATA-P17 object plus adapter schema marker

Resolve reconstructs `DatasetVersion` from `metadata_json` and verifies the row
columns still match the stored object. Duplicate `dataset_version_id` writes are
rejected before insert and again on SQLite integrity failure; there is no
overwrite path.

## Tests And Docs

Added unit tests under `tests/unit/data/test_dataset_version.py` for:

- exact dataclass fields and JSON-stable mapping;
- missing field, extra field, blank ID, malformed hash, naive timestamp, and
  reversed timestamp failures;
- `VERSIONED` and `READY_FOR_RESEARCH` lifecycle acceptance with bound inputs;
- fail-closed rejection for mis-bound quality hash, mis-bound manifest hash,
  missing coverage, blocking quality, and mismatched coverage.

Added integration tests under
`tests/integration/data/test_dataset_version_registry.py` using only `tmp_path`
registry DB files for:

- persist -> resolve round-trip against the existing registry table;
- duplicate ID rejection without overwrite;
- missing ID returning `None`;
- mis-bound table column detection;
- non-local-only registry path rejection.

The integration writes pass linked synthetic quality, coverage, and source
manifest inputs plus code/config hash bindings into
`persist_dataset_version(...)`; all DB files are temp DBs under pytest
`tmp_path`.

Added `docs/data_foundation/DATASET_VERSION.md` and updated
`docs/data_foundation/README.md` and `README.md` for the DATA-P17 snapshot.

## Validation Results

No requested validation command was skipped.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; output showed only DATA-P17 allowed-path changes: `README.md`, `docs/data_foundation/README.md`, `src/alpha_system/data/foundation/__init__.py`, `src/alpha_system/data/foundation/datasets.py`, `tests/unit/data/test_data_foundation_package_skeleton.py`, plus new DATA-P17 doc, handoff, adapter, unit test, and integration test directory. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `303 passed in 0.24s`. |
| `python -m pytest tests/integration/data -q` | Passed: `5 passed in 0.67s`. |
| `test -f docs/data_foundation/DATASET_VERSION.md` | Passed with no output. |
| `find metadata -type f ! -name README.md ! -name .gitkeep -print` | Passed with empty output. |
| `git ls-files runs` | Passed with empty output. |
| `python -m ruff check src/alpha_system/data/foundation/datasets.py src/alpha_system/data/foundation/version_registry.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_dataset_version.py tests/unit/data/test_data_foundation_package_skeleton.py tests/integration/data/test_dataset_version_registry.py` | Additional check passed: `All checks passed!`. |
| `python -m pytest tests/unit/data/test_dataset_version.py tests/integration/data/test_dataset_version_registry.py -q` | Additional narrow check passed: `12 passed in 0.70s`. |
| `git diff --check` | Additional check passed with no output. |
| `git diff --cached --name-only` | Passed with empty output. |
| `test -w .git` | Audit command exited non-zero; `.git` is not writable in this sandbox. |
| `test -w .git/index` | Audit command exited non-zero; `.git/index` is not writable in this sandbox. |

## Exact Staged File Set

`git diff --cached --name-only` returns the exact staged file set below:

```text
```

The staged set is empty because this execution sandbox exposes `.git` and
`.git/index` as non-writable. No `runs/**` path is staged.

The intended explicit commit-eligible file set for Ralph or a writable-git
executor is:

```text
README.md
docs/data_foundation/DATASET_VERSION.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P17.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/datasets.py
src/alpha_system/data/foundation/version_registry.py
tests/integration/data/test_dataset_version_registry.py
tests/unit/data/test_data_foundation_package_skeleton.py
tests/unit/data/test_dataset_version.py
```

`git add .`, `git add -A`, force push, commit, push, PR creation, merge,
reviewer execution, `review.md`, and `verdict.json` were not used or created.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` returned empty.
- No `runs/**` path is staged or intended for staging.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- `find metadata -type f ! -name README.md ! -name .gitkeep -print` returned
  empty output.
- Integration tests used only temp DBs under pytest `tmp_path`.
- No metadata SQLite/DB/WAL/journal file was produced under the repository
  `metadata/` directory.
- No raw data, provider response, canonical data, factor data, label data,
  cache data, local DB, log, Parquet/Arrow/Feather file, model artifact,
  secret, credential, account artifact, or heavy artifact is staged or intended
  for staging.
- Explicit staging discipline was preserved; the actual staged set is empty
  because the Git index is not writable in this sandbox.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create a
verdict, create a PR, merge, mark the phase PASS, perform any external IBKR
call, pull real data, write raw/canonical provider data, operate broker/order/
account/paper/live/real-time surfaces, deploy production code, or make alpha,
profitability, tradability, or production-readiness claims.

Review artifacts are required later for the YELLOW lane, but the executor was
explicitly instructed not to call Claude, run reviewer, create `review.md`, or
create `verdict.json`. Ralph remains responsible for validation orchestration,
review, verdict parsing, semantic done-check, PR/CI, merge gate, and final
phase outcome.
