# Troubleshooting

## Wrong Path Or Filesystem

Symptom: commands behave differently across shells, paths include `/mnt/c`, or
artifact guards flag path contamination.

Fix: move active work to the WSL2 Linux filesystem and operate from:

```text
~/projects/alpha_system
```

Do not use `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive,
Windows-synced folders, network drives, or temporary directories for active
repo or Workflow 2 worktrees.

## `alpha` Command Not Found

Symptom:

```text
alpha: command not found
```

Fix: install editable mode inside the active Python environment:

```bash
python -m pip install -e ".[dev]"
alpha --help
```

For source-tree checks without install:

```bash
PYTHONPATH=src python -m alpha_system --help
```

If a specific subcommand is missing, confirm the current phase has introduced
it. Do not document or depend on a command from a future phase.

## Missing Flags Or Argument Errors

Symptom: a command rejects a flag or requires another argument.

Fix: use command help as the source of truth:

```bash
alpha <group> <command> --help
```

Do not infer flags from older docs or examples. Prefer temp/local output paths
and registry paths outside commit-eligible locations.

## Accidental Raw, Heavy, Or Local-DB Staging

Symptom: `git status --short` shows data payloads, generated artifacts, SQLite
files, DB journals, WAL files, Parquet, Arrow, Feather, logs, caches, or
`runs/**`.

Fix: unstage the forbidden path and leave it local-only. Do not delete failure
evidence to hide a run. Re-run the artifact audit:

```bash
git diff --cached --name-only
git ls-files runs
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
```

`git ls-files runs` must return empty for this campaign baseline.

## Forbidden Bulk Staging

These are forbidden examples, not instructions:

```text
git add .
git add -A
```

Fix: stage only the allowed files from the active phase spec, one path at a
time or as an explicit path list. Inspect the staged set before committing:

```bash
git diff --cached --name-only
```

## Dirty Tree

Symptom: unrelated files are already modified.

Fix: do not revert user or unrelated changes unless explicitly instructed.
Separate the active phase changes by path, and stage only the phase-allowed
paths. If unrelated changes affect the phase and make accurate execution
impossible, write a blocked handoff instead of broadening scope.

## Active STOP File

Symptom: `runs/<RUN_ID>/STOP` exists.

Fix: stop Workflow 2 progression for that run. Ralph owns STOP/resume state.
Codex must not ignore an active STOP file when acting inside a Workflow 2 run.
Resume only after the STOP condition is removed or resolved and recorded state
is used.

## `core.bare` Flips

Symptom:

```text
fatal: this operation must be run in a work tree
```

Check:

```bash
python tools/frontier/status_doctor.py
git config --get --bool core.bare
git rev-parse --is-bare-repository
```

Root cause, proven in a scratch reproduction on 2026-06-12: a push from a
linked worktree runs `.githooks/pre-push` with `GIT_DIR` exported to the
linked-worktree gitdir (`<main>/.git/worktrees/<wt>`). The hook then launches
the smoke and canary checks. If that hook Git context is inherited,
`tools/hooks/canary_runner.py` can run its scratch `git init` against the real
linked-worktree gitdir instead of the scratch directory, rewriting the shared
`<main>/.git/config` with `core.bare=true`.

Minimal reproduction shape, using only a disposable repo:

```bash
GIT_DIR=/tmp/main/.git/worktrees/wt git -C "$(mktemp -d)" init
```

Pushes from the canonical repo are immune to this specific failure because the
hook-exported `GIT_DIR` is relative (`.git`), so the canary scratch cwd resolves
it inside the scratch directory instead of the shared repo gitdir.

Current prevention: `pre_push.py` scrubs `GIT_*` from the environment passed to
its smoke/canary subprocesses, and `canary_runner.py` scrubs `GIT_*` before its
own subprocesses. If an older checkout or interrupted run still leaves the repo
bare, restore it explicitly:

```bash
git config core.bare false
```

Defense-in-depth layers remain:

- `python tools/frontier/status_doctor.py` fails closed when `core.bare=true`.
- Workflow 2 restores `core.bare=false` during RUN_INIT/resume preflight and
  emits `CORE_BARE_RESTORED` when it repairs the local repo.
- The safe coordinator merge wrapper serializes GitHub/Git operations and
  restores `core.bare=false` before releasing its lock:

```bash
just pr-merge <number>
```

## Hidden Failed Runs

Symptom: a command fails, then a later successful rerun is the only evidence
left.

Fix: preserve the failure in run-local artifacts and handoffs. Failed steps,
warnings, rejected configs, missing artifacts, and unavailable tools are part
of the research and automation record.

## Overclaiming In Reports

Symptom: report text says or implies a candidate is profitable, robust,
tradable, approved, production-ready, or suitable for broker/live trading.

Fix: rewrite the text using `docs/RESEARCH_INTERPRETATION_POLICY.md`. Use
neutral descriptions such as "diagnostic observation", "candidate for review",
"requires review", or "fixture correctness check".
