# Adversarial Review: P003000_HOOK_GITDIR_SCRUB

- Campaign: DISCOVERY_RIGOR_FLOOR_V1
- Phase: P003000_HOOK_GITDIR_SCRUB (core.bare root-cause fix: GIT_* scrub in hook-spawned subprocesses)
- Lane: yellow
- Reviewer: fresh adversarial (Claude, Workflow 1)
- Date: 2026-06-11
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-ci-selfheal`, branch `repair/hook-gitdir-scrub`, HEAD `6b398ff`
- Verdict: **PASS_WITH_WARNINGS**

## Diff base clarification (important)

`origin/main` is one commit ahead of this branch's base (`2811c7b`, PR #376
FUTSUB session-reset truth repoint, landed after the branch was cut). A raw
`git diff origin/main` therefore shows ~1,481 lines of reverse-noise under
`src/alpha_system/**`, `reviews/**`, `tests/**` that are NOT part of this
phase. The actual phase diff is the uncommitted working tree vs HEAD
(`6b398ff`):

```text
docs/TROUBLESHOOTING.md        | 47 +++++++++++++++---------
tools/frontier/github_utils.py |  9 ++--
tools/frontier/ralph_driver.py | 12 ++---
tools/hooks/canary_runner.py   | 10 +++++
tools/hooks/pre_push.py        | 10 ++++-
tests/unit/hooks/test_git_env_scrub.py (new, untracked)
```

No file overlap between the phase diff and PR #376 (verified: identical
per-file stat vs HEAD and vs origin/main for the five modified files).
Recommend rebasing onto origin/main before PR.

## 1. Scope — PASS

- Only the four authorized files plus the new test file and the two
  spec-item-5 comment annotations are touched. No `src/alpha_system/**`, no
  `evals/canaries/**`.
- Canary semantics untouched: the `canary_runner.py` diff adds only `import
  os`, `Mapping` import, `_scrub_git_env()`, and `env=clean_env` wiring on
  the two existing `subprocess.run` calls. Zero changes inside `scenarios()`
  or any canary definition.
- `tools/frontier/github_utils.py` and `tools/frontier/ralph_driver.py`
  changes proven comment/docstring-only by deterministic AST comparison
  (HEAD vs working tree, docstrings normalized): **AST-identical for both
  files**. No state-machine, gate, or behavior change.

## 2. Correctness — PASS

- Scrub removes ALL `GIT_*`-prefixed variables (superset of the six required:
  GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE, GIT_COMMON_DIR, GIT_PREFIX,
  GIT_OBJECT_DIRECTORY) while preserving PATH and everything else
  (dict comprehension over `os.environ`).
- No canary legitimately needs repo git context: every canary runs in a
  scratch `tempfile.TemporaryDirectory` with its own `git init`; no canary
  performs `git commit`/`git config` (so losing `GIT_AUTHOR_*`/`GIT_COMMITTER_*`
  is harmless); governance canaries import via explicit `sys.path` insert of
  `ROOT/src`, not git.
- `pre_push.py` scrubs only the spawned check subprocesses
  (`verify.py --smoke`, `canary_runner.py`). The hook's own
  `git merge-base --is-ancestor` (force-push guard) correctly keeps the
  inherited hook git context — read-only query, cannot `git init`, and is the
  one place hook GIT_DIR is legitimate. Correct boundary placement.

## 3. Regression test honesty — PASS

`tests/unit/hooks/test_git_env_scrub.py` (3 tests):

- `test_canary_runner_git_init_ignores_leaked_linked_worktree_gitdir` builds a
  REAL temp main repo (`git init` under pytest `tmp_path`), constructs real
  linked-worktree gitdir metadata by hand (`commondir`, `gitdir`, `HEAD` —
  complying with the spec's no-`git worktree`-command constraint), sets
  `GIT_DIR` to the worktree gitdir via monkeypatch, then calls the REAL
  `run_canary()` (real scratch `git init`, no mocking of the scrub or of
  subprocess), and asserts (a) the canary subprocess saw zero `GIT_*` vars and
  the scratch `.git/config` exists in the scratch cwd, and (b) the temp main
  repo `core.bare` stays `false`.
- `test_git_env_scrub_removes_all_git_context_and_keeps_path` covers both
  scrub functions on all six required keys + `GIT_TRACE`, preserving
  PATH/HOME.
- `test_pre_push_check_subprocesses_receive_scrubbed_git_env` mocks
  `subprocess.run` to assert the env kwarg passed by `pre_push.main()` is
  scrubbed and PATH-preserving. This one is plumbing-level (mocked
  subprocess), acceptable for the defense layer; the end-to-end unmocked path
  is the canary_runner test.

## 4. Mutation tests — PASS (both mutations caught)

Worktree integrity: `git diff HEAD | sha256sum` baseline
`faf59fb3b778c879cc6e1bb29751716bc54534d8722e2a034bc05c3cd413e8a0`; identical
after all mutations were reverted (verified twice, including after the final
restore). Final state byte-identical to the executor's diff.

- **Mutation A** (remove `env=clean_env` from both `run_canary` subprocess
  calls): `test_canary_runner_git_init_ignores_leaked_linked_worktree_gitdir`
  **FAILED** (`assert passed` → canary subprocess saw leaked `GIT_*`). A
  direct probe with the mutated code additionally **reproduced
  `core.bare=true` in the temp main repo** (`git config --get --bool
  core.bare` → `true` after `run_canary` with leaked worktree `GIT_DIR`),
  confirming the test guards the real failure mode, not a proxy.
- **Mutation B** (remove `env=clean_env` from `pre_push.py` check loop only):
  `test_pre_push_check_subprocesses_receive_scrubbed_git_env` **FAILED**
  (`KeyError: 'env'` — subprocess called without env kwarg); exactly 1 failed,
  27 passed. The defense layer IS test-covered (via the mocked-subprocess
  test), so the spec's "untested defense layer" warning case does not apply.

Reviewer disclosure: during mutation A restore I initially ran `git checkout
-- tools/hooks/canary_runner.py`, which restored to HEAD and wiped the
executor's UNCOMMITTED scrub. I reconstructed it by applying the exact diff
captured verbatim at review start; the post-restore `git diff HEAD` sha256
matches the baseline exactly and the full suite re-passed (28/28), so the
final worktree is byte-identical to the executor's submission.

## 5. Validation — PASS (exact counts)

All run with `~/.venvs/alpha_system_research/bin/python`:

| Command | Result |
|---|---|
| `pytest tests/unit -k "hook or canary" -q` | **28 passed, 2644 deselected** (exit 0) |
| `tools/hooks/canary_runner.py` | **21 PASS, 0 FAIL**, "All Frontier canaries passed." (exit 0) |
| `tools/verify.py --smoke` | exit 0, no output |
| `tools/frontier/status_doctor.py` | exit 0, **VERDICT: WARN** — sole WARN = "No run dir with state.json for DISCOVERY_RIGOR_FLOOR_V1" (expected: WF1 phase, no live WF2 run); core.bare ok, hooks armed, runtime contract ok |

All four match the executor notes exactly.

## 6. Docs accuracy — PASS (one content-removal note)

The rewritten `docs/TROUBLESHOOTING.md` core.bare entry: states the proven
mechanism (hook-exported `GIT_DIR` → inherited by canary scratch `git init` →
re-inits the real linked-worktree gitdir → rewrites shared `.git/config` with
`core.bare=true`), gives the disposable-repo reproduction one-liner
(`GIT_DIR=/tmp/main/.git/worktrees/wt git -C "$(mktemp -d)" init`), explains
canonical-repo immunity (relative `GIT_DIR=.git` resolves inside the scratch
cwd), supersedes the prior `gh pr merge` attribution (also corrected in the
`github_utils.py`/`ralph_driver.py` comments), and keeps all three
defense-in-depth layers documented (status_doctor fail-closed, WF2
RUN_INIT/resume restore + `CORE_BARE_RESTORED`, locked `just pr-merge`
wrapper). The "2026-06-12" date matches the spec's UTC proof timestamp
(2026-06-12T00:20Z).

## 7. Artifact policy — PASS

- Nothing staged (`git diff --cached` empty).
- `git status --short`: 5 modified + untracked `tests/unit/hooks/` only; no
  `runs/` paths.
- `git ls-files runs` → empty.
- No commit was made (matches executor notes; commit/PR is a separate step).

## Findings

1. **[info] Branch base behind origin/main.** PR #376 (`2811c7b`) landed
   after the branch was cut; no file overlap with the phase diff. Rebase
   before PR to keep the PR diff clean.
2. **[low] Multi-line docstring annotation vs spec letter.** Spec item 5
   authorizes "single-line comment touch-ups only"; the
   `restore_local_repo_after_merge` docstring edit in `ralph_driver.py`
   rewrites ~5 docstring lines. Proven AST-identical (no behavior change) and
   within the spirit of the authorization; flagging for the record.
3. **[low] TROUBLESHOOTING removed the P234500 worktreeConfig investigation
   notes.** The deleted paragraph included a standing recommendation about
   not removing `extensions.worktreeConfig` from the canonical repo. The
   removal is defensible (it was an investigation log of the superseded
   misdiagnosis), but that recommendation is now undocumented; consider
   re-homing it if linked-worktree pruning becomes a task.
4. **[low] pre_push defense layer verified only at plumbing level.** Mutation
   B is caught, but by a mocked-subprocess test asserting env kwargs, not an
   end-to-end leak test. The end-to-end guarantee rests on the canary_runner
   scrub (which IS tested end-to-end with a real flip reproduction under
   mutation). Acceptable for a defense-in-depth layer.

## Verdict

**PASS_WITH_WARNINGS** — root cause fixed at both layers, regression test is
real and mutation-validated (including a deterministic reproduction of the
`core.bare=true` flip when the scrub is removed), all validation green with
exact counts matching the executor's handoff, docs corrected, artifact policy
clean. Warnings are informational/low only.
