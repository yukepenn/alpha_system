# ASV1-P03 Handoff

## Phase

- Phase ID: `ASV1-P03`
- Phase name: Python Workspace and Package Skeleton
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p03-python-workspace-and-package-skeleton`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P03` (local-only)
- Commit: not created by Codex in this execution because the exact editable-install validation is blocked by the host Python PEP 668 policy.

## Scope Completed

Created the Python workspace skeleton with a `src/` package layout, importable
subpackage placeholders, a minimal CLI shell, unit tests, and commit-eligible
placeholder directories.

The package layout now includes:

- `alpha_system` top-level package with `__init__.py` and `__main__.py`.
- Placeholder subpackages: `core`, `data`, `factors`, `labels`, `research`,
  `signals`, `strategies`, `management`, `portfolio`, `backtest`, `execution`,
  `l2`, `experiments`, `reports`, and `cli`.
- `alpha_system.cli` with `main.py`, `__init__.py`, and `__main__.py`.
- `execution/` contains only `__init__.py`; no broker, paper, live, or
  order-router modules were added.
- Test layout directories: `tests/unit`, `tests/integration`,
  `tests/no_lookahead`, `tests/parity`, `tests/performance`, and
  `tests/fixtures`.
- Top-level `factors/.gitkeep` and `strategies/.gitkeep` placeholders only.

## Dependency Rationale

`pyproject.toml` declares an installable setuptools package with the
`alpha-system` project name and `alpha_system` source package. Runtime
dependencies are intentionally empty in this skeleton phase because no domain
logic is implemented and imports/CLI help must not require NumPy, Numba,
Polars, DuckDB, local data, a metadata database, network access, or credentials.

The only declared optional extra is:

```text
dev = ["pytest>=7.4"]
```

The approved local-first research stack from ASV1-P02 remains limited to
stdlib/SQLite, NumPy, Numba, Polars, DuckDB, and pytest/dev tooling. This phase
added no cloud service, hosted or paid database, database server, broker SDK,
live market-data client, web framework/server, Ray, MLflow server, Dagster,
Prefect, ClickHouse, QuestDB, ArcticDB, DolphinDB, or kdb+ dependency.

The `alpha` console script is configured:

```text
alpha = "alpha_system.cli.main:main"
```

Because the exact editable install was blocked by the host Python policy, the
installed `alpha --help` command was not available in this environment.

## Validation Results

All commands below were run locally by Codex unless noted. Ralph still owns
formal checks recording, review routing, verdict parsing, done-check, PR, CI,
and merge gates.

```text
find runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1 -maxdepth 2 -name STOP -print
PASS - returned empty before execution/checks.

git status --short
PASS - before staging, showed only expected untracked ASV1-P03 files under
allowed paths.

python -m pip install -e ".[dev]"
FAIL - host Python rejected the install with PEP 668
externally-managed-environment. Pip recommended using a virtual environment or
overriding with --break-system-packages. Codex did not use the override.

python -m venv --system-site-packages /tmp/asv1_p03_venv
FAIL - supplemental check; the host lacks ensurepip/python3.12-venv, so a
throwaway venv could not be created.

python -m pytest tests/unit
PASS - 6 passed.

python -m alpha_system --help
FAIL - No module named alpha_system because editable install was blocked and the
src-layout package is not installed into the system interpreter.

python -m alpha_system.cli --help
FAIL - No module named alpha_system for the same install-resolution reason.

python -c "import alpha_system; print(alpha_system.__name__)"
FAIL - No module named alpha_system for the same install-resolution reason.

PYTHONPATH=src python -m alpha_system --help
PASS - returned help text and exit code 0.

PYTHONPATH=src python -m alpha_system.cli --help
PASS - returned help text and exit code 0.

PYTHONPATH=src python -c "import alpha_system; print(alpha_system.__name__)"
PASS - printed alpha_system.

PYTHONPATH=src python -c "<import all ASV1-P03 subpackages>"
PASS - imported every listed subpackage.

python -m ruff check . || true
NON-BLOCKING - Ruff is not installed or configured; output was
"/usr/bin/python: No module named ruff".

python -m mypy src || true
NON-BLOCKING - Mypy is not installed or configured; output was
"/usr/bin/python: No module named mypy".

alpha --help || true
NON-BLOCKING - command not found because editable install was blocked.

git diff --check
PASS.

find data -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find metadata -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find . -path ./tests/fixtures -prune -o -type f -name "*.parquet" -print
PASS - returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

git diff --cached --name-only
PASS - returned exactly the staged set listed below.

git diff --cached --name-only | grep '^runs/' || true
PASS - returned empty.

git diff --cached --name-only | grep -E '(^data/|^metadata/|^artifacts/|\.parquet$|\.arrow$|\.feather$|\.sqlite$|\.sqlite3$|\.db$|\.db-journal$|\.wal$|\.log$|__pycache__|\.pyc$|\.pkl$|\.pickle$|\.joblib$|\.onnx$|\.npy$|\.npz$)' || true
PASS - returned empty.

git diff --cached --check
PASS.

find src/alpha_system -type f \( -path "*broker*" -o -path "*live*" -o -path "*paper*" -o -path "*order_router*" \) -print
PASS - returned empty.

find src/alpha_system/execution -type f -print
PASS - returned only src/alpha_system/execution/__init__.py after generated
bytecode caches from the validation run were removed from new src/tests paths.
```

## Files Changed And Staged

Files were staged explicitly by path. `git add .`, `git add -A`, and force
push were not used.

```text
factors/.gitkeep
handoffs/ASV1-P03.md
pyproject.toml
src/alpha_system/__init__.py
src/alpha_system/__main__.py
src/alpha_system/backtest/__init__.py
src/alpha_system/cli/__init__.py
src/alpha_system/cli/__main__.py
src/alpha_system/cli/main.py
src/alpha_system/core/__init__.py
src/alpha_system/data/__init__.py
src/alpha_system/execution/__init__.py
src/alpha_system/experiments/__init__.py
src/alpha_system/factors/__init__.py
src/alpha_system/l2/__init__.py
src/alpha_system/labels/__init__.py
src/alpha_system/management/__init__.py
src/alpha_system/portfolio/__init__.py
src/alpha_system/reports/__init__.py
src/alpha_system/research/__init__.py
src/alpha_system/signals/__init__.py
src/alpha_system/strategies/__init__.py
strategies/.gitkeep
tests/fixtures/.gitkeep
tests/integration/.gitkeep
tests/no_lookahead/.gitkeep
tests/parity/.gitkeep
tests/performance/.gitkeep
tests/unit/test_cli_help.py
tests/unit/test_imports.py
tests/unit/test_no_local_data_required.py
```

## Commit-Eligible Vs Local-Only

Commit-eligible ASV1-P03 files are limited to the package skeleton,
`pyproject.toml`, tests, permitted `.gitkeep` placeholders, and this handoff.
All `runs/**` artifacts remain local-only and were not staged. Codex did not
create `runs/<run_id>/phases/ASV1-P03/review.md` or
`runs/<run_id>/phases/ASV1-P03/verdict.json`.

## Artifact Policy Confirmation

No `runs/**`, raw data, canonical data, factor values, label values, generated
reports, heavy artifacts, local SQLite files, DB files, Parquet, Arrow,
Feather, logs, caches, model binaries, secrets, local environment files, or
forbidden generated artifacts were staged by Codex.

Generated Python bytecode caches created under the new `src/alpha_system` and
`tests/unit` paths by local validation were removed before staging. Pre-existing
ignored cache files elsewhere in the repo were not modified.

## Scope Confirmation

No domain contracts, registries, migrations, SQLite logic, data ingestion,
factor logic, label logic, signal logic, strategy logic, management logic,
portfolio logic, backtest engine, diagnostics, reports, grids, ML workflows, or
L2 processing were implemented.

No broker integration, paper trading, live trading, order routing, production
execution, deployment, PR creation, auto-merge, Claude call, reviewer run,
`review.md`, or `verdict.json` was introduced by Codex.

No alpha, profitability, robustness, tradability, or production-readiness claim
was introduced.

## Relevant Risks

- R-023 Cloud/server dependency creep: mitigated; runtime dependencies are empty
  and the only dev extra is pytest.
- R-022 Accidental broker/live scope creep: mitigated; `execution/` is an empty
  placeholder package only.
- R-017 Test weakening/gaming: mitigated; no existing tests were removed or
  relaxed, and the new unit tests exercise imports, CLI help, and no-local-data
  behavior.
- R-013/R-038/R-039 Heavy artifact/SQLite/Parquet committed: mitigated; artifact
  checks returned empty and `git ls-files runs` returned empty.
- R-019/R-020 Local path contamination: mitigated; worktree is under
  `/home/yuke_zhang/projects/alpha_system`, and no Windows-synced absolute
  paths were added.
- R-026 Handoff completeness: mitigated by this handoff.
- R-014 Unsupported claims: mitigated; no performance, profitability, or
  tradability claim was added.

## Known Limitations

- The exact editable install command could not run under the system Python
  because the environment is PEP 668 externally managed.
- A supplemental virtual environment install check could not run because
  `python3.12-venv`/`ensurepip` is unavailable.
- Exact installed CLI/import commands failed only because the package could not
  be installed into the interpreter; the same CLI/import checks passed with
  `PYTHONPATH=src`.
- Ruff and Mypy are not installed or configured in this phase.
- Fresh Claude Opus review, verdict parsing, formal done-check, PR, CI, merge
  gate, and merge are Ralph-owned and were not run by Codex.

## Review Focus

- Verify the skeleton matches the ASV1-P02 architecture and contains no domain
  logic.
- Verify dependency discipline: no cloud/server/broker/live/web dependencies
  were introduced.
- Verify the CLI is help-only shell scaffolding and both module entry points are
  correct.
- Verify the unit tests are meaningful and not weakened or gamed.
- Verify `execution/` contains no broker, paper, live, or order-router modules.
- Verify artifact policy, explicit staging, and `runs/**` local-only handling.
- Assess the PEP 668 validation limitation separately from code behavior.

## Next Recommended Step

Ralph should validate the explicit staged set, record the environment-blocked
install commands, route review, and decide whether the PEP 668 limitation
requires a repair environment with `python3.12-venv` or an approved install
policy.
