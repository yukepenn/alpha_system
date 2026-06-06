# Lessons

Project-specific lessons for `alpha_system`.

Add concise entries only after they are validated by real work.

## Workflow 2 — parallel dag_wave execution

- **Serialize all git/gh in parallel mode.** In `dag_wave` parallel mode the build
  workers run as threads sharing one repo. A `gh pr merge` can transiently flip the
  shared repo to `core.bare=true`, which makes a sibling phase's concurrent `git`
  fail with `fatal: this operation must be run in a work tree`. Hold a process-wide
  RLock around every `git()` and every gh call, and restore `core.bare=false` after
  each gh call (`tools/frontier/git_utils.GIT_SERIAL_LOCK`,
  `github_utils._run_gh`). Validated by 4 clean parallel waves on
  `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.

- **The coordinator owns git; the executor must not.** In worktree mode the shared
  `.git` is effectively read-only to the executor — it leaves all changes UNSTAGED
  and the unsandboxed driver stages/commits per curated path on its behalf. A git
  failure on the executor side is expected and is not a phase blocker.

- **Union-merge README only — never `**/*.md`.** A blanket markdown union-merge in
  `.git/info/attributes` silently concatenates conflicting same-region edits in
  load-bearing docs (`specs/`, `ACCEPTANCE.md`, `decisions/`, `handoffs/`) and
  defeats the pre-merge base-sync conflict detection (which relies on a non-zero
  merge return to block truthfully). Only the append-only README snapshot is safe
  to union-merge.

- **Branch deletion is driver-owned in both modes.** `merge_pr` does not pass
  `--delete-branch` (it can flip `core.bare` while a branch is checked out in a
  worktree). The driver deletes the branch after merge: worktree mode via
  `WorktreeManager.cleanup_after_merge`; in-tree mode via
  `cleanup_phase_worktree_after_merge` (guarded to `auto/` branches). Forgetting
  the in-tree path leaks remote branches in the default serial mode.

## Validation environment

- **Run authoritative `verify.py --all` in a clean shell.** Inherited Workflow-2
  control env vars (`FRONTIER_CREATE_PR`, `FRONTIER_ALLOW_AUTOMERGE`,
  `FRONTIER_MERGE_DRY_RUN`, `FRONTIER_PARALLEL`, `FRONTIER_MAX_PARALLEL_PHASES`)
  force PR/merge/parallel driver paths during tests and fail exactly 13 driver
  tests (`tests/test_ralph_driver.py`, `tests/test_github_utils.py`) on otherwise
  green main — a false negative with zero substrate tests affected. This caused the
  `FLF-P31` closeout to be wrongly `BLOCKED`; the fix was to re-validate in a clean
  environment (`2120 passed`) and reissue `COMPLETE_WITH_WARNINGS`. Tests run via
  `PYTHONPATH=src` (the bare `python -c "import alpha_system..."` smoke commands in
  specs only resolve with it).

- **Manual gh ops from a worktree need a core.bare check.** A manual
  `gh pr merge` / push from a worktree can leave the shared root repo with
  `core.bare=true` and may error `'main' is already used by worktree` on gh's local
  branch cleanup — but the **remote merge still succeeds**. Always
  `git config core.bare false` afterward (safe only when no driver is running, as
  the in-process git-lock does not cover external shells).

## Verdict artifacts

- **Specific review warnings live in `review.md`, not `verdict.json`.** The verdict
  parser often writes the placeholder *"Review passed with warnings but did not
  enumerate warning bullets"* and may set `external_providers_called`/`network_used`
  to `true` by default; these contradict the review prose and the no-external-call
  contract. Read the `review.md` narrative for the real residual warnings, and
  treat the boolean flags as parser defaults, not evidence of provider calls.
