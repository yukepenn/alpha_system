# Artifact Audit

`FUTSUB-P30` verifies the closeout artifact boundary for
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`. It is a value-free audit of
tracked files and local-only substrate storage. It does not materialize values,
write registries, read raw provider payloads, run diagnostics, promote research,
or create paper/live/broker/deployment behavior.

## Audit Result

- `git ls-files runs` returned empty output.
- `git ls-files '**/*.parquet' '**/*.arrow' '**/*.feather' '**/*.sqlite' '**/*.db' '**/*.dbn' '**/*.zst'` returned empty output.
- Additional tracked SQLite journal/WAL/log globs returned empty output.
- Worktree scans found no untracked heavy/value/DB/log files under the repo.
- The only tracked metadata-path match was `metadata/README.md`.
- Tracked roll-calendar matches were value-free config/code/test files, not
  roll-calendar data payloads.
- `ALPHA_DATA_ROOT` was set to `/home/yuke_zhang/alpha_data/alpha_system`.
- The local SQLite registries were present under `ALPHA_DATA_ROOT/registry/`:
  `datasets.sqlite`, `features.sqlite`, and `labels.sqlite`.
- Local materialized feature and label roots were present under
  `ALPHA_DATA_ROOT/features/materialized` and
  `ALPHA_DATA_ROOT/labels/materialized`.

The detailed command log is in
`research/futures_substrate_scaleout_v1/closeout/artifact_audit.md`.

## Validation Note

`python tools/verify.py --all` was run with `FRONTIER_*` cleared and
`PYTHONPATH=src`. It reported `1 failed, 3324 passed, 80 skipped`; the single
failure was the known exported-`ALPHA_DATA_ROOT` cache-policy case in
`tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`.
The same targeted test passed when `ALPHA_DATA_ROOT` was unset. The standalone
smoke command and standalone canary runner passed after the audit files were
written.

The executor prompt forbade `git status --short` and
`git diff --cached --name-only`, so the executor did not run them and did not
stage anything. Ralph owns the authoritative staged-set check before commit.

## Boundary

Only value-free summaries, docs, tests, code, handoffs, and reviews are
commit-eligible. Feature values, label values, local SQLite registries,
roll-calendar data, raw/canonical/provider data, heavy artifacts, logs, caches,
secrets, and `runs/**` remain local-only and are never committed.
