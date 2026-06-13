# FUTSUB-P30 Artifact Audit

Phase: `FUTSUB-P30` - Artifact Audit and Local-Only Value Verification  
Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`  
Date: 2026-06-13  

This is a value-free closeout audit. It did not materialize values, read raw
provider payloads, write registries, run diagnostics, create review artifacts,
stage files, commit, push, create a PR, or merge.

## Tracked-Artifact Audit

| Command | Exit | Output |
| --- | ---: | --- |
| `git ls-files runs` | 0 | Empty |
| `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` | 0 | Empty |
| `git ls-files '**/*.sqlite3' '**/*.db-journal' '**/*.wal' '**/*.log'` | 0 | Empty |
| `git ls-files 'registry/*' 'metadata/*'` | 0 | `metadata/README.md` |
| `git ls-files '*roll*calendar*' '*calendar*roll*'` | 0 | `configs/data/roll_calendar/futsub_p03_roll_guard.json`; `research/feature_compute_fast_path_v1/parity/session_calendar_roll/FCFP-P03_PARITY.md`; `src/alpha_system/features/fast/session_calendar_roll.py`; `tests/fixtures/feature_compute_fast_path/session_calendar_roll.py`; `tests/unit/data/test_roll_policy_calendar.py`; `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py` |
| `find . -path ./.git -prune -o -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.sqlite' -o -name '*.db' -o -name '*.dbn' -o -name '*.zst' \) -print \| sed -n '1,120p'` | 0 | Empty |
| `find . -path ./.git -prune -o -type f \( -name '*.sqlite3' -o -name '*.db-journal' -o -name '*.wal' -o -name '*.log' \) -print \| sed -n '1,120p'` | 0 | Empty |

The tracked roll-calendar matches are value-free config/code/test artifacts, not
local roll-calendar data payloads. The heavy/value/DB tracked-artifact command
returned empty output.

The executor prompt explicitly forbade `git status --short` and
`git diff --cached --name-only`, so those commands were not run by this executor.
No staging was performed by this executor; Ralph owns the authoritative staged
set before commit.

## Locality Confirmation

`ALPHA_DATA_ROOT` was set to `/home/yuke_zhang/alpha_data/alpha_system` and the
directory exists locally.

| Command | Exit | Output |
| --- | ---: | --- |
| `printf 'ALPHA_DATA_ROOT=%s\n' "${ALPHA_DATA_ROOT:-}"; test -n "${ALPHA_DATA_ROOT:-}"; test -d "${ALPHA_DATA_ROOT:-}"` | 0 | `ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system` |
| `for path in "${ALPHA_DATA_ROOT:-}/registry/datasets.sqlite" "${ALPHA_DATA_ROOT:-}/registry/features.sqlite" "${ALPHA_DATA_ROOT:-}/registry/labels.sqlite"; do if test -e "$path"; then printf 'PRESENT %s\n' "$path"; else printf 'MISSING %s\n' "$path"; fi; done` | 0 | `PRESENT /home/yuke_zhang/alpha_data/alpha_system/registry/datasets.sqlite`; `PRESENT /home/yuke_zhang/alpha_data/alpha_system/registry/features.sqlite`; `PRESENT /home/yuke_zhang/alpha_data/alpha_system/registry/labels.sqlite` |

Directory inspection under the local data root showed local-only materialized
feature and label roots (`features/materialized`, `labels/materialized`) and the
local SQLite registry roots under `ALPHA_DATA_ROOT`, outside the repository
worktree. No raw provider payload was opened or read.

`.gitignore` covers `runs/**`, heavy/value formats (`*.parquet`, `*.arrow`,
`*.feather`, `*.dbn`, `*.zst`), local databases (`*.sqlite`, `*.sqlite3`,
`*.db`, `*.db-journal`, `*.wal`), raw/canonical/value data roots, logs, caches,
and local metadata payloads. The campaign never-commit globs additionally cover
`registry/*.sqlite`, all heavy/value/DB globs, local values, local registries,
roll-calendar data files, provider responses, logs, caches, and `runs/**`.

## Validation

| Command | Exit | Result |
| --- | ---: | --- |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/verify.py --all'` | 1 | `1 failed, 3324 passed, 80 skipped in 85.69s`; failing test was `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`. The failure expected `RUN_ARTIFACTS` but got `ALPHA_DATA_ROOT` because `ALPHA_DATA_ROOT` was exported. Status doctor also warned that no run dir with `state.json` was present for this campaign in this checkout. |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; unset ALPHA_DATA_ROOT; PYTHONPATH=src python -m pytest tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only'` | 0 | `1 passed in 0.02s` |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/verify.py --smoke'` | 0 | Empty |
| `bash -lc 'for name in $(compgen -e FRONTIER_); do unset "$name"; done; PYTHONPATH=src python tools/hooks/canary_runner.py'` | 0 | All Frontier canaries passed. |
| `git rev-list --count main..HEAD` | 0 | `0` |
| `git rev-list --count HEAD..main` | 0 | `1` |
| `test -f research/futures_substrate_scaleout_v1/closeout/artifact_audit.md && test -f docs/futures_substrate_scaleout/ARTIFACT_AUDIT.md && test -f handoffs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P30.md && test -f README.md` | 0 | Empty |

The full verify failure matches the P30 validation note's documented
`ALPHA_DATA_ROOT`-export-sensitive cache-policy exception. The branch is 0
commits ahead of `main` and 1 commit behind `main` by `rev-list`; CI-green
campaign PR evidence is coordinator/Ralph-owned and was not checked by this
executor.

## Conclusion

The tracked-artifact audit found no tracked `runs/**` path and no tracked
Parquet, Arrow, Feather, SQLite, DB, SQLite journal/WAL, DBN, ZST, or log
artifact. Worktree scans found no untracked files with those heavy/value/DB/log
extensions either. Values, local SQLite registries, and roll-calendar data remain
local-only under `ALPHA_DATA_ROOT` or run-local state by policy. No values, DBs,
heavy artifacts, or `runs/**` paths were committed by this executor; no commit
was performed.
