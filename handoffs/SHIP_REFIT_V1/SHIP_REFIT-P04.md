# SHIP_REFIT-P04 Handoff

## Scope Completed

- Added shared Frontier cleanup plumbing in `tools/frontier/cleanup.py`.
  Post-merge driver cleanup now records `post_merge_cleanup.json` and runs the
  same cleanup path used by `just frontier-clean`.
- Extended the existing driver-owned post-merge seam in
  `tools/frontier/ralph_driver.py`:
  - worktree mode still uses `WorktreeManager.cleanup_after_merge`;
  - in-tree mode keeps `auto/` remote branch deletion in
    `cleanup_phase_worktree_after_merge`;
  - local `auto/` branch deletion is best-effort and only runs when that branch
    is not checked out;
  - stale Frontier worktree cleanup and `runs/` retention run after merge.
- Added local-only `runs/` retention in `tools/frontier/runs_retention.py`.
  It rotates only completed runs with readable `state.json`, protects the active
  run, protects any non-completed run, and protects any run with an unresolved
  `STOP`. Eligible completed runs are moved to
  `$ALPHA_SYSTEM_ROOT/.tmp/runs_backups/`.
- Added persistent temp-root helpers in `tools/frontier/runtime_paths.py` and
  routed Frontier temp scratch for `ci_parity.py` and `canary_runner.py` to
  `$ALPHA_SYSTEM_ROOT/.tmp`. The canary runner also passes `TMPDIR`/`TEMP`/`TMP`
  to nested subprocesses.
- Fixed done-check provenance: done-check warning/error handling writes
  `done_check.md` / `done_check.json` and phase state/events, but no longer
  rewrites reviewer-owned `verdict.json`.
- Added `just frontier-clean` and `just frontier-clean-dry-run`.
- Added focused regression tests under `tests/frontier/` and the durable note
  `docs/ship_refit_v1/CLEANUP_PROVENANCE.md`.
- Updated the compact README snapshot and the SHIP_REFIT docs index.

## Repair Attempt

- Repaired the CI failure in `tests/tools/test_system_map.py` by regenerating
  `docs/SYSTEM_MAP.md` with `just system-map`. The generated command surface now
  includes the new `frontier-clean` and `frontier-clean-dry-run` recipes.

## Validation

- `python -m py_compile tools/frontier/runtime_paths.py tools/frontier/runs_retention.py tools/frontier/cleanup.py tools/frontier/ci_parity.py tools/frontier/ralph_driver.py tools/hooks/canary_runner.py tests/frontier/test_cleanup_provenance.py`
  - PASS.
- `python tools/verify.py --smoke`
  - PASS.
- `PYTHONPATH=src python -m pytest tests/frontier -k "cleanup or worktree or provenance or runs_retention" -q`
  - PASS: `5 passed, 5 deselected in 0.13s`.
- `python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed, including `planted_fake_alpha`,
    `true_alpha_detection_detect_strong`, and
    `true_alpha_detection_no_detect_weak`.
- `python -c "import importlib.util,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"`
  - PASS; no output.
- `git ls-files runs`
  - PASS; no output.
- `PYTHONPATH=src python -m pytest tests/tools/test_system_map.py -q`
  - PASS: `2 passed in 0.02s`.
- `git diff --check`
  - PASS; no output.
- `python tools/frontier/status_doctor.py`
  - WARN only: no SHIP_REFIT_V1 run dir with `state.json` was present in this
    checkout; core.bare false, hooks armed, active campaign pointer set to
    SHIP_REFIT_V1, runtime contract consistent.

No requested command failed.

## Artifact And Safety Notes

- No `git add`, `git commit`, or `git push` command was run by the executor.
  Changes are left unstaged for Ralph. Read-only `git status`, `git diff`,
  `git diff --check`, and `git ls-files runs` checks were used for repair
  inspection and artifact verification.
- No PR, merge, review, reviewer call, `review.md`, or `verdict.json` was
  created by the executor.
- No `runs/` path was created for commit eligibility; the prompt-named
  run-local directory was not present in this worktree, and no run-local handoff
  was written.
- No live trading, paper trading, broker operation, order routing, deployment,
  destructive cleanup execution, or external provider call was performed.
- No numpy, pandas, polars, or other runtime dependency was introduced.
- No diagnostics, surrogate, detection-power, value/accounting, registry,
  broker/live/execution, or data path was modified.
- Because the executor staged nothing, no `runs/`, data, DB, cache, log, secret,
  or heavy artifact path was staged by the executor. `git ls-files runs`
  remained empty.

## Commit-Eligible Paths For Ralph

- `README.md`
- `justfile`
- `tools/frontier/runtime_paths.py`
- `tools/frontier/runs_retention.py`
- `tools/frontier/cleanup.py`
- `tools/frontier/ci_parity.py`
- `tools/frontier/ralph_driver.py`
- `tools/hooks/canary_runner.py`
- `tests/frontier/test_cleanup_provenance.py`
- `docs/ship_refit_v1/CLEANUP_PROVENANCE.md`
- `docs/ship_refit_v1/README.md`
- `docs/SYSTEM_MAP.md`
- `handoffs/SHIP_REFIT_V1/SHIP_REFIT-P04.md`

## Review Status

GREEN lane; review is optional and Ralph-owned. Per executor instructions, no
Claude call, reviewer artifact, PR, merge, staging, commit, push, or PASS marking
was performed by Codex.
