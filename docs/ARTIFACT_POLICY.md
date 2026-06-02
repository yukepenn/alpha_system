# Artifact Policy

## Commit-Eligible Artifacts

Commit-eligible artifacts are durable project files such as source code when a
later phase authorizes implementation, tests when a phase authorizes tests,
docs, specs, handoffs, reviews, decisions, curated configs, and tiny synthetic
fixtures under `tests/fixtures/**` only when a later phase explicitly allows
them.

For ASV1-P02, commit-eligible artifacts are limited to the allowed docs,
decision records, optional small README or project-status updates, and the
commit-eligible handoff.

## Local-Only Artifacts

The following remain local-only:

- `runs/**`
- raw data
- canonical generated data
- factor values
- label values
- caches
- local SQLite and DB files
- DB journals and WAL files
- Parquet, Arrow, and Feather files
- generated reports
- generated report bundles
- logs
- model binaries
- credential material
- local environment files

Markdown, CSV, and optional static HTML are valid local report formats. They do
not require a server. Generated reports remain local artifacts unless a later
spec explicitly authorizes a curated documentation artifact.

## Explicit Staging

Use explicit staging by path. Do not use `git add .`. Do not use `git add -A`.
Do not force push.

Before any commit or merge-gate evaluation, inspect the staged set with:

```bash
git diff --cached --name-only
```

The staged set must contain no `runs/` path and no forbidden data, metadata,
artifact, DB, cache, log, Parquet, Arrow, Feather, model, credential, or local
environment path.

## Run Artifacts

Run-local files such as specs, executor prompts, notes, checks, handoffs,
reviews, verdicts, repair attempts, state files, costs, events, progress, STOP
files, and run summaries under `runs/**` are for local audit and resume. They
must never be staged or committed.

Commit-eligible handoffs belong under `handoffs/<PHASE_ID>.md`.
