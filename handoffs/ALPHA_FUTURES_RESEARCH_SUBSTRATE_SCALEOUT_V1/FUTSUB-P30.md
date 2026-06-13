# FUTSUB-P30 Handoff

Phase: `FUTSUB-P30` - Artifact Audit and Local-Only Value Verification  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-13  
Executor: Codex

## Scope Executed

- Ran the allowed tracked-artifact audit commands.
- Confirmed `ALPHA_DATA_ROOT` exists locally and contains the expected local
  SQLite registry files.
- Confirmed materialized feature/label roots are under `ALPHA_DATA_ROOT`, not
  the tracked repository tree.
- Wrote the value-free audit report at
  `research/futures_substrate_scaleout_v1/closeout/artifact_audit.md`.
- Wrote the durable docs mirror at
  `docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md`.
- Updated the README snapshot for the post-`FUTSUB-P30` merge state.

This handoff does not mark the phase `PASS`, does not create a review, does not
create a verdict artifact, does not create a PR, and does not stage or commit
anything.

## Files For Ralph To Stage If Accepted

- `README.md`
- `research/futures_substrate_scaleout_v1/closeout/artifact_audit.md`
- `docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md`
- `handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P30.md`

No `runs/` path, review artifact, value artifact, registry, Parquet, SQLite, or
heavy artifact was created by this executor.

## Validation

| Command | Outcome |
| --- | --- |
| `git ls-files runs` | Exit 0, empty output |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` | Exit 0, empty output |
| `git ls-files '**/*.sqlite3' '**/*.db-journal' '**/*.wal' '**/*.log'` | Exit 0, empty output |
| `git ls-files 'registry/*' 'metadata/*'` | Exit 0, output: `metadata/README.md` |
| `git ls-files '*roll*calendar*' '*calendar*roll*'` | Exit 0, output only value-free config/code/test paths: `configs/data/roll_calendar/futsub_p03_roll_guard.json`, `research/feature_compute_fast_path_v1/parity/session_calendar_roll/FCFP-P03_PARITY.md`, `src/alpha_system/features/fast/session_calendar_roll.py`, `tests/fixtures/feature_compute_fast_path/session_calendar_roll.py`, `tests/unit/data/test_roll_policy_calendar.py`, `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py` |
| `find . -path ./.git -prune -o -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.sqlite' -o -name '*.db' -o -name '*.dbn' -o -name '*.zst' \) -print \| sed -n '1,120p'` | Exit 0, empty output |
| `find . -path ./.git -prune -o -type f \( -name '*.sqlite3' -o -name '*.db-journal' -o -name '*.wal' -o -name '*.log' \) -print \| sed -n '1,120p'` | Exit 0, empty output |
| `printf 'ALPHA_DATA_ROOT=%s\n' "${ALPHA_DATA_ROOT:-}"; test -n "${ALPHA_DATA_ROOT:-}"; test -d "${ALPHA_DATA_ROOT:-}"` | Exit 0, output: `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system` |
| `for path in "${ALPHA_DATA_ROOT:-}/registry/datasets.sqlite" "${ALPHA_DATA_ROOT:-}/registry/features.sqlite" "${ALPHA_DATA_ROOT:-}/registry/labels.sqlite"; do if test -e "$path"; then printf 'PRESENT %s\n' "$path"; else printf 'MISSING %s\n' "$path"; fi; done` | Exit 0, all three registry SQLite files present under `ALPHA_DATA_ROOT/registry/` |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/verify.py --all'` | Exit 1; `1 failed, 3324 passed, 80 skipped in 85.69s`; failing test: `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`; expected `RUN_ARTIFACTS`, got `ALPHA_DATA_ROOT` because `ALPHA_DATA_ROOT` was exported. Status doctor also warned no run dir with `state.json` was present for this campaign in this checkout. |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; unset ALPHA_DATA_ROOT; PYTHONPATH=src python -m pytest tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only'` | Exit 0, `1 passed in 0.02s` |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/verify.py --smoke'` | Exit 0, empty output |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/hooks/canary_runner.py'` | Exit 0, all Frontier canaries passed |
| `git rev-list --count main..HEAD` | Exit 0, output: `0` |
| `git rev-list --count HEAD..main` | Exit 0, output: `1` |
| `test -f research/futures_substrate_scaleout_v1/closeout/artifact_audit.md && test -f docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md && test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P30.md && test -f README.md` | Exit 0, empty output |

Commands intentionally not run because the executor prompt explicitly forbade
them:

- `git status --short`
- `git diff --cached --name-only`

Staged files as observed by `git diff --cached --name-only`: not inspected by
this executor because that command was forbidden. No staging was performed by
this executor; Ralph must run the authoritative staged-set check before commit.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty output.
- `git ls-files` for Parquet, Arrow, Feather, SQLite, DB, SQLite journal/WAL,
  DBN, ZST, and logs returned empty output.
- Worktree scans found no untracked heavy/value/DB/log files under the repo.
- Values and materialized feature/label roots are local-only under
  `ALPHA_DATA_ROOT`.
- Local SQLite registries are local-only under `ALPHA_DATA_ROOT/registry/`.
- Roll-calendar data remains local-only by policy; the tracked roll-calendar
  match is config/code/test, not data payload.
- `.gitignore` and campaign never-commit globs cover `runs/**`, raw/canonical
  data, feature/label values, local DBs and registries, roll-calendar data,
  heavy artifacts, logs, caches, secrets, and credentials.
- No source file under `src/**` was edited.
- No forbidden execution, broker, live, signal, strategy, portfolio,
  management, L2, backtest, or agent-factory path was edited.
- No new AlphaSpec, StudySpec, feature family, label family, parameter search,
  materialization, registry mutation, Strategy Reference validation,
  FactorLibrary ingestion, AlphaBook behavior, paper/live/broker/order action,
  deployment action, capital-allocation decision, profitability claim, or
  tradability claim was created.
- No feature values, label values, raw/canonical data, provider payload,
  Parquet, Arrow, Feather, DBN/ZST, SQLite/DB, model artifact, cache, log,
  secret, or local data artifact was created inside the repository.
- No values, DBs, heavy artifacts, or `runs/**` paths were committed by this
  executor; no commit was performed.

All repository changes are intentionally unstaged for Ralph.
