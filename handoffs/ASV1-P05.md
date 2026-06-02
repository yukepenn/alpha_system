# ASV1-P05 Handoff

## Phase

- Phase ID: `ASV1-P05`
- Phase name: SQLite Metadata Registry MVP
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p05-sqlite-metadata-registry-mvp`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P05` (local-only)

## Scope Completed

Implemented the SQLite metadata registry MVP with:

- stdlib `sqlite3` registry initialization and read-only status inspection,
- idempotent SQL migration loading/application with checksum tracking,
- schema version `1` in `001_registry_mvp.sql`,
- all 13 required registry tables,
- shared experiment-style run record columns on the five run tables,
- deterministic hashing utilities,
- graceful git metadata capture,
- injectable deterministic run-id generation,
- experiment run insert/read helpers with deterministic JSON round-trips,
- read-only `registry status` CLI wiring,
- tiny local-only default config,
- registry documentation and required unit/integration tests.

No external database server, cloud service, broker/paper/live/order-routing
code, data ingestion, factor computation, label generation, strategy execution,
backtest engine, or generated production registry database was introduced.

## Migration Summary

Schema version: `1`

Migration file:

```text
src/alpha_system/core/migrations/001_registry_mvp.sql
```

Migration tracking table:

```text
schema_migrations(version, name, checksum, applied_at)
```

The runner loads version-prefixed SQL files, applies missing versions once,
records a SHA-256 checksum, and verifies checksums on later idempotent runs.

## Table And Column Coverage

| Table | Coverage |
| --- | --- |
| `dataset_versions` | dataset/version metadata, content/config hashes, metadata JSON, status message |
| `factor_registry` | factor identity, owner/status, metadata JSON, status message |
| `factor_versions` | git commit/dirty, code/config hashes, data version, parameters JSON, artifact paths JSON, decision status |
| `factor_validation_runs` | full experiment run-record columns |
| `label_versions` | git commit/dirty, code/config hashes, data version, parameters JSON, artifact paths JSON, decision status |
| `study_runs` | full experiment run-record columns |
| `strategy_registry` | strategy identity, owner/status, metadata JSON, status message |
| `strategy_versions` | git commit/dirty, code/config hashes, data/factor versions, parameters JSON, artifact paths JSON, decision status |
| `grid_runs` | full experiment run-record columns |
| `ml_runs` | full experiment run-record columns |
| `backtest_runs` | full experiment run-record columns |
| `artifact_manifest` | run id/table, artifact key/path, content hash, metadata JSON, status message |
| `promotion_decisions` | subject/run identity, decision status, artifact paths JSON, metadata JSON, status message |

Experiment-style run tables:

```text
factor_validation_runs
study_runs
grid_runs
ml_runs
backtest_runs
```

Shared run-record columns:

```text
run_id
timestamp
git_commit
git_dirty
code_hash
config_hash
data_version
factor_versions_json
label_versions_json
engine_version
parameters_json
artifact_paths_json
decision_status
warnings_json
status_message
```

JSON text columns are documented in `docs/METADATA_REGISTRY.md` and are
round-tripped in `tests/integration/test_registry_required_columns.py`.

## Registry Status CLI

Introduced:

```text
alpha registry status
python -m alpha_system.cli registry status
```

Inputs:

```text
--registry-path
--config
--json
```

The command is read-only. It reports registry path, existence, local-only path
status, schema version, migration currency, required-table presence, and
missing/invalid state. It returns a non-success exit code for missing or invalid
registries and does not create a database as a side effect of `--help` or
missing-registry inspection.

## Utility Behavior

- Hashing: deterministic canonical JSON, config hashing, file hashing, and
  code-path manifest hashing.
- Git metadata: captures commit and dirty state when git is available; returns
  a well-defined unavailable result without crashing when git is missing or the
  path is not a git worktree.
- Run ids: deterministic for injected timestamp/clock, seed, and components;
  uses a normalized prefix, UTC timestamp token, and SHA-256-derived suffix.

## Validation Results

Codex ran the following local checks. Ralph still owns formal checks recording,
handoff validation, review routing, verdict parsing, PR, CI, merge gate, and
done-check.

```text
git status --short
PASS - exit 0; before staging, showed only ASV1-P05 files under allowed paths.

python -m pytest tests/unit tests/integration
PASS - exit 0; 46 passed.

python -m alpha_system.cli registry status --help
FAIL - exit 1; /usr/bin/python: Error while finding module specification for
'alpha_system.cli' (ModuleNotFoundError: No module named 'alpha_system').
Reason: the src-layout package is still not installed into the host interpreter,
matching the ASV1-P03/ASV1-P04 environment limitation. This phase did not alter
packaging or host installation state because those paths/operations are outside
the generated spec's allowed implementation scope.

PYTHONPATH=src python -m alpha_system.cli registry status --help
PASS - exit 0; registry status help printed.

find metadata -type f ! -name README.md ! -name ".gitkeep" -print
PASS - exit 0; returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - exit 0; returned empty.

git ls-files runs
PASS - exit 0; returned empty.

alpha registry status --help || true
NON-BLOCKING - exit 0 due to `|| true`; output was `/bin/bash: line 1: alpha:
command not found`. The console script is not installed in this host
interpreter.

python -m ruff check . || true
NON-BLOCKING - exit 0 due to `|| true`; output was `/usr/bin/python: No module
named ruff`.

python -m mypy src || true
NON-BLOCKING - exit 0 due to `|| true`; output was `/usr/bin/python: No module
named mypy`.

git diff --check
PASS - exit 0; returned empty.

find src/alpha_system -type f \( -path "*broker*" -o -path "*live*" -o -path "*paper*" -o -path "*order_router*" \) -print
PASS - exit 0; returned empty.
```

## Files Changed And Staged

Files were staged explicitly by path. `git add .`, `git add -A`, force push,
PR creation, merge, reviewer execution, `review.md`, and `verdict.json` were
not used.

```text
configs/registry/default.yaml
docs/METADATA_REGISTRY.md
handoffs/ASV1-P05.md
src/alpha_system/cli/main.py
src/alpha_system/cli/registry.py
src/alpha_system/core/git_info.py
src/alpha_system/core/hashing.py
src/alpha_system/core/migrations.py
src/alpha_system/core/migrations/001_registry_mvp.sql
src/alpha_system/core/registry.py
src/alpha_system/core/run_ids.py
src/alpha_system/experiments/registry.py
tests/integration/test_no_committed_sqlite.py
tests/integration/test_registry_init_tempdb.py
tests/integration/test_registry_migrations_idempotent.py
tests/integration/test_registry_required_columns.py
tests/integration/test_registry_required_tables.py
tests/integration/test_registry_status_cli.py
tests/unit/test_git_info.py
tests/unit/test_hashing.py
tests/unit/test_run_ids.py
```

Staged-set audit after explicit staging:

```text
git diff --cached --name-only
PASS - exit 0; returned exactly the staged files listed above.

git diff --cached --name-only | rg '^runs/'
PASS - exit 1; returned empty, so no runs path is staged.

git diff --cached --name-only | rg '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)'
PASS - exit 1; returned empty, so no forbidden artifact path is staged.

git diff --cached --check
PASS - exit 0; returned empty.
```

## Artifact Policy Confirmation

- No SQLite, DB, journal, or WAL file was committed or staged; the repository
  `find` command returned empty for those patterns.
- `git ls-files runs` returned empty.
- No raw data, generated canonical data, factor values, label values, Parquet,
  Arrow, Feather, logs, caches, model binaries, generated report bundles, or
  heavy artifacts were staged.
- No `runs/**` path was staged.
- No external/cloud/server database dependency was introduced; the registry
  uses Python stdlib `sqlite3`.
- No broker, paper trading, live trading, order routing, production execution,
  or unsupported alpha/tradability claim was introduced.
- No test was weakened, skipped, or marked xfail.

## Relevant Risks

- R-018 SQLite schema drift: mitigated with migration/idempotence tests,
  required-table tests, required-column tests, and documentation.
- R-038 Generated SQLite DB committed: mitigated with temp DB tests, repository
  DB-file find audit, and `git ls-files` DB audit test.
- R-037 CLI writes to local-only paths during tests: mitigated with subprocess
  CLI tests that run under `tmp_path` and assert missing status does not create
  a database.
- R-023 Cloud/server dependency creep: mitigated; no dependency was added.
- R-016/R-017 Hidden failed runs/test weakening: exact command outcomes are
  recorded, including the bare CLI import failure.
- R-020 Windows/OneDrive path contamination: default config uses a repo-relative
  ignored metadata path only.

## Known Limitations

- The exact `python -m alpha_system.cli registry status --help` command still
  fails in this host interpreter unless `PYTHONPATH=src` is set or the package
  is installed. This is the same src-layout install-state limitation recorded in
  ASV1-P03 and ASV1-P04. The supplemental `PYTHONPATH=src` command passes.
- The `alpha` console script is not installed in this environment.
- Ruff and mypy are not installed in this environment.
- Schema version `1` intentionally stores version maps, parameters, artifact
  paths, warnings, and metadata as JSON text. Later phases may normalize these
  relationships.

## Review Focus

Review should focus on schema completeness, reproducibility column coverage,
migration idempotence and checksum behavior, read-only status CLI behavior,
temp-DB-only test discipline, JSON round-trip coverage, artifact-policy
separation, and whether the narrow CLI wiring changed only subcommand dispatch.
