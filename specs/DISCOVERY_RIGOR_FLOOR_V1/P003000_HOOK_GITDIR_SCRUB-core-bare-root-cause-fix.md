---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P003000_HOOK_GITDIR_SCRUB
lane: yellow
status: in_progress
---

# P003000_HOOK_GITDIR_SCRUB: fix the proven core.bare root cause (leaked GIT_DIR into hook-spawned git subprocesses)

## Purpose

The recurring `core.bare=true` flips on the canonical repo are now root-caused
with a deterministic scratch reproduction (coordinator, 2026-06-12T00:20Z):

1. `git push` from a LINKED worktree runs `.githooks/pre-push` with `GIT_DIR`
   exported (git hook contract), pointing at the worktree gitdir
   (`.git/worktrees/<wt>`).
2. The hook (`tools/hooks/pre_push.py`) spawns `tools/verify.py --smoke` and
   `tools/hooks/canary_runner.py` with the INHERITED environment.
3. `canary_runner.py` (line ~34) runs `["git", "init"]` in a scratch
   directory. With the leaked `GIT_DIR`, `git init` re-initializes the REAL
   repo gitdir instead of the scratch dir and rewrites the SHARED
   `.git/config` with `core.bare = true`.

Scratch proof: `GIT_DIR=<main>/.git/worktrees/<wt> git init <scratch>` flips
`<main>/.git/config` `core.bare` to true on git 2.43. Pushes from the
canonical repo do not flip because the exported `GIT_DIR` is relative and
resolves harmlessly inside the canary scratch cwd. This also explains flips
during WF2 runs (every phase-branch push from a driver worktree). The prior
attribution to `gh pr merge` internals (comments in
`tools/frontier/github_utils.py:149-152`, `ralph_driver.py:3396-3402`, and the
new `docs/TROUBLESHOOTING.md` entry from PR #375) was a misdiagnosis of the
same symptom; the restore mitigations stay as defense in depth.

## Scope (in-bounds)

1. `tools/hooks/canary_runner.py`: every spawned `git` subprocess must run
   with a scrubbed environment — remove all `GIT_*` variables (at minimum
   `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR`,
   `GIT_PREFIX`, `GIT_OBJECT_DIRECTORY`) from the env passed to
   `subprocess.run`. Keep `PATH`/everything else.
2. `tools/hooks/pre_push.py`: scrub the same `GIT_*` set from the environment
   passed to its check subprocesses (`verify.py --smoke`, `canary_runner.py`)
   so nothing they spawn can inherit hook git context either.
3. Regression test (`tests/unit/hooks/` or alongside existing hook tests):
   build a temp main repo + linked worktree, set `GIT_DIR` to the worktree
   gitdir in the test env, invoke the canary runner's git-scratch path (or
   `canary_runner.py` main against a temp cwd), and assert the temp main
   repo's `core.bare` remains false AND the scratch repo got initialized in
   the scratch dir. The test must FAIL if the scrub is removed (mutation
   target).
4. `docs/TROUBLESHOOTING.md`: correct the "core.bare flips" entry — proven
   root cause (leaked GIT_DIR through hooks into scratch `git init`),
   reproduction one-liner, why pushes from the canonical repo are immune,
   and the defense-in-depth layers that remain (driver preflight restore,
   status_doctor FAIL, locked pr-merge wrapper).
5. Leave the `_run_gh`/driver restore mitigations and comments in place;
   optionally annotate them as defense-in-depth for a now-fixed root cause
   (single-line comment touch-ups only).

## Hard constraints

- No changes under `src/alpha_system/**`, `evals/canaries/**` canary
  SEMANTICS (env scrub only — canary checks themselves must not weaken),
  `ralph_driver.py` state machine, or merge/review gates.
- Surgical diffs; no reformatting.
- Explicit staging only; no runs/ or values; no `git worktree` commands; do
  not modify .git config of any real repo (tests use temp repos only).
- Research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "hook or canary" -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
python tools/frontier/status_doctor.py
```

All 21 canaries must still pass. Exact counts in the handoff.

## Done criteria

- Hook-spawned git subprocesses cannot inherit GIT_* context; regression
  test proves the flip cannot recur and fails when the scrub is removed;
  canaries unchanged and green; TROUBLESHOOTING corrected; truthful handoff;
  fresh adversarial review PASS or PASS_WITH_WARNINGS under
  `reviews/DISCOVERY_RIGOR_FLOOR_V1/`.
