# Metadata Registry

## Purpose

The metadata registry is a local SQLite database for reproducibility metadata.
It records dataset versions, factor and label versions, strategy versions,
experiment-style run records, artifact manifests, and promotion decisions. It
does not ingest market data, compute factors or labels, run backtests, route
orders, or store generated research payloads.

## Local-Only Policy

The default example path is:

```text
metadata/registry.sqlite3
```

`metadata/**` and `*.sqlite*` / `*.db*` files are ignored by git. Registry
database files, journal files, and WAL files must remain local-only and must
not be staged or committed. Tests must create registry databases only under
pytest temporary directories.

The registry path must avoid Windows-mounted and synced locations such as
`/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, and Google Drive.

## Migration Model

Migrations live under `src/alpha_system/core/migrations/` as version-prefixed
SQL files. `001_registry_mvp.sql` creates schema version `1`.

Applied migrations are tracked in:

| Table | Purpose |
| --- | --- |
| `schema_migrations` | Records migration version, file name, checksum, and apply timestamp. |

The runner applies each migration once and verifies the stored checksum if a
version was already applied. Re-running migrations is expected to be a no-op.

## Table Matrix

| Table | Primary role | Required reproducibility support |
| --- | --- | --- |
| `dataset_versions` | Dataset version metadata | `data_version`, config/content hashes, metadata JSON, status message |
| `factor_registry` | Factor identity and lifecycle metadata | factor id, status, owner, metadata JSON, status message |
| `factor_versions` | Versioned factor specifications | git commit, dirty indicator, code hash, config hash, data version, parameters JSON, artifact paths JSON, decision status |
| `factor_validation_runs` | Experiment-style factor validation run | full run-record column set |
| `label_versions` | Versioned label specifications | git commit, dirty indicator, code hash, config hash, data version, parameters JSON, artifact paths JSON, decision status |
| `study_runs` | General research study run | full run-record column set |
| `strategy_registry` | Strategy identity and lifecycle metadata | strategy id, status, owner, metadata JSON, status message |
| `strategy_versions` | Versioned strategy specifications | git commit, dirty indicator, code hash, config hash, data version, factor versions JSON, parameters JSON, artifact paths JSON, decision status |
| `grid_runs` | Bounded grid run metadata | full run-record column set |
| `ml_runs` | ML experiment metadata | full run-record column set |
| `backtest_runs` | Backtest run metadata | full run-record column set |
| `artifact_manifest` | Artifact path manifest entries | run id, run table, artifact key/path, content hash, metadata JSON, status message |
| `promotion_decisions` | Review or promotion decision record | subject identity/version, run id, decision status, artifact paths JSON, metadata JSON, status message |

The experiment-style run tables are:

```text
factor_validation_runs
study_runs
grid_runs
ml_runs
backtest_runs
```

Each experiment-style run table has this shared run-record column set:

| Column | Format |
| --- | --- |
| `run_id` | Text primary key |
| `timestamp` | UTC ISO-8601 text |
| `git_commit` | Commit hash text when available, otherwise null |
| `git_dirty` | Integer boolean when available, otherwise null |
| `code_hash` | SHA-256 hex text |
| `config_hash` | SHA-256 hex text |
| `data_version` | Dataset version text |
| `factor_versions_json` | JSON object mapping factor ids to version strings |
| `label_versions_json` | JSON object mapping label ids to version strings |
| `engine_version` | Engine/version text |
| `parameters_json` | JSON object of run parameters |
| `artifact_paths_json` | JSON object mapping artifact names to local paths |
| `decision_status` | Decision status text from the contract vocabulary |
| `warnings_json` | JSON array of warning strings |
| `status_message` | Human-readable status or warning message |

## JSON Text Columns

JSON columns are stored as deterministic UTF-8 JSON text produced with sorted
object keys and compact separators. The MVP keeps these values denormalized:

```json
{"factor_a":"v1","factor_b":"v2"}
```

```json
{"max_window":20,"session_reset":true}
```

```json
{"summary":"artifacts/example/summary.json"}
```

Later phases may normalize relationships, but schema version `1` requires the
JSON text columns above to round-trip through the registry access layer.

## Status CLI

The read-only status command is:

```bash
alpha registry status
python -m alpha_system.cli registry status
```

Inputs:

```text
--registry-path PATH
--config PATH
--json
```

The command reports the registry location, existence, local-only path status,
schema version, migration status, and required-table presence. It does not
create or migrate a missing registry during status inspection. Missing or
invalid registry state returns a non-success exit code with an explicit error
message.
