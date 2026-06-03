# Onboarding

## Purpose

This guide is the local-first starting point for a researcher or AI Agent using
`alpha_system`. The repository is an offline research harness. It is not a
broker, paper-trading adapter, live-trading system, order router, deployment
target, or production execution service.

Do not treat fixture output, diagnostics, grids, ML scores, backtests, reports,
or review bundles as proof that a hypothesis is alpha, profitable, robust,
tradable, or ready for use. Promotion requires review.

## Required Location

Use the WSL2 Linux filesystem:

```text
~/projects/alpha_system
```

Do not run the active repo or active Workflow 2 worktrees from `/mnt/c`,
`/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders,
network drives, temporary directories, or other synced/nonlocal paths. This
path policy protects local file semantics, artifact guards, and run resume.

## Local-First Stack

The v0.1 surface is local-first and file-backed:

| Component | Role |
| --- | --- |
| Local files | Data inputs, generated tables, manifests, and reports. |
| SQLite | Local metadata and registry state. SQLite DB files are local-only. |
| DuckDB | Local analytical queries over file-backed data. |
| Polars | Lazy dataframe-style processing where implemented. |
| NumPy | Deterministic array operations. |
| Numba | Acceleration only after reference parity. |
| Markdown, CSV, static HTML | Local reports with no server requirement. |

Cloud storage, paid databases, database servers, workflow servers, web UIs,
broker connections, paper accounts, live accounts, and order-routing services
are outside this campaign.

## Environment Setup

Use Python 3.12 or newer inside WSL2. From the repository root:

```bash
cd ~/projects/alpha_system
python --version
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

If the console script is not installed yet, use the source-tree form:

```bash
PYTHONPATH=src python -m alpha_system --help
```

After editable install, the normal smoke check is:

```bash
alpha --help
```

Use each command's help as the source of truth for exact flags:

```bash
alpha data validate --help
alpha report build --help
```

## First Safe Steps

Start with read-only orientation:

1. Read `README.md`, `ACTIVE_CAMPAIGN.md`, `AGENTS.md`, and this guide.
2. Read `docs/RESEARCHER_GUIDE.md` for the human workflow or
   `docs/AI_AGENT_GUIDE.md` for Workflow 2 execution.
3. Run `alpha --help` or `PYTHONPATH=src python -m alpha_system --help`.
4. Inspect registry state with `alpha registry status --help` before using a
   registry path.
5. Use tiny synthetic fixtures or temp directories for initial command checks.
6. Keep generated outputs local-only and out of git.

## Artifact Discipline

Never stage or commit:

- `runs/**`
- raw data
- canonical generated data
- materialized factor values
- materialized label values
- caches
- local SQLite, DB, journal, or WAL files
- generated reports or review bundles
- logs
- model binaries
- Parquet, Arrow, or Feather files outside explicitly allowed tiny fixtures
- credential material or local environment files

Use explicit staging only. These are forbidden examples, not instructions:

```text
git add .
git add -A
```

Before any commit or merge-gate evaluation, inspect:

```bash
git status --short
git diff --cached --name-only
git ls-files runs
```

`git ls-files runs` must return empty for this campaign baseline.

## Policy Links

- `docs/LOCAL_FIRST_STACK.md`
- `docs/ARTIFACT_POLICY.md`
- `docs/GIT_AND_ARTIFACT_DISCIPLINE.md`
- `docs/NO_LOOKAHEAD_POLICY.md`
- `docs/RESEARCH_INTERPRETATION_POLICY.md`
- `docs/CLI_REFERENCE.md`
- `docs/TROUBLESHOOTING.md`
