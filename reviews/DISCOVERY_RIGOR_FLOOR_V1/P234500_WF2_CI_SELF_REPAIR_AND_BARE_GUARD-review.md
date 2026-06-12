# Review: P234500_WF2_CI_SELF_REPAIR_AND_BARE_GUARD

- Campaign: DISCOVERY_RIGOR_FLOOR_V1
- Lane: yellow
- Reviewer: fresh adversarial Claude (Workflow 1)
- Worktree reviewed: `/home/yuke_zhang/projects/alpha_system-wf1-ci-selfheal` (branch `repair/wf2-ci-selfheal`, uncommitted diff off `4e7c21e`)
- Diff fingerprint at review start AND end: `git diff | sha256sum` = `58b981a5c75fcba8ed0c7cc164eff137f5f0613a1c63136cb3eab3730908e82d` (byte-identical after all mutation tests; untracked files `pr_merge.py` = `bf3d3433…`, `test_ralph_driver_ci_repair.py` = `89a400c7…` also unchanged)

## Verdict

**PASS_WITH_WARNINGS**

## 1. Scope — PASS

Changed set (`git status --short` + `git diff --stat`, 464 insertions, 0 deletions):
`tools/frontier/ralph_driver.py`, `tools/frontier/github_utils.py`,
`tools/frontier/status_doctor.py`, `tools/frontier/pr_merge.py` (new),
`justfile`, `docs/TROUBLESHOOTING.md`, `tests/unit/frontier/test_ralph_driver_ci_repair.py` (new),
`tests/unit/test_status_doctor.py`, `tests/test_github_utils.py`.
Exactly the authorized set. Zero `src/alpha_system/**` changes. `git ls-files runs` = empty.

## 2. Safety semantics — PASS (read line by line)

- **Insertions only.** `git diff tools/frontier/ralph_driver.py | grep -c "^-"` = 1 (the
  `--- a/` header). Zero deleted/reformatted lines; no import churn beyond one added
  `collect_failed_ci_logs` import. Surgical as required.
- **STOP checks**: `run_ci_repair_attempt` checks `stop_requested(run_dir)` at 5 points —
  before routing (entry), before evidence collection, before Codex prompt/dispatch, before
  validation, and before the commit/push/re-enter-CI step (`post_phase_git_github`). Each
  emits `CI_REPAIR_SKIPPED_STOP` and returns `"BLOCKED"`, which falls through to the
  unchanged `CI_BLOCKED` stop.
- **Budget exhaustion**: `start_attempt >= max_repair_attempts_for_phase(...)` returns
  `"BLOCKED"` immediately; the caller then executes the byte-identical pre-existing
  `block_provider_gate(..., CI_BLOCKED, f"CI_BLOCKED: CI status was {ci_status}.", event="CI_BLOCKED", ...)`
  lines (unchanged in the diff) at both the run path (~ralph_driver.py:3496) and the resume
  path (~:4253). Same event name, same reason shape, same stop-state writes.
- **No gate changes**: no merge-gate, review-gate, verdict-parsing, or artifact-check hunk
  touched (insertion-only diff confirms). No new public state names; the routing is internal
  to the existing CI gate. `stage_index` and the state-order module are untouched (diff stat
  covers all changed files).
- **No double-stop on nested re-entry**: after a routed repair re-enters
  `post_phase_git_github` and the budget exhausts at depth, `run_ci_repair_attempt` returns
  `str(state.get("status"))` = `"CI_BLOCKED"` (set by the nested `block_provider_gate`),
  which is != `"BLOCKED"`, so the outer frame returns `False` without emitting a second
  `CI_BLOCKED`. Bounded recursion: each level consumes one `repair_attempts` slot.
- **Explicit staging**: new code stages nothing itself; the commit path is the pre-existing
  `commit_phase_changes` → `git add -- <path>` per file (git_utils.py:373/376), and
  git_utils.py:133 hard-blocks `add .`/`add -A`. No `git add` in any new code.
- **CI failure log locality**: `ci_failure.log` + `ci_failure_log_result.json` are written
  only under `runs/<run_id>/phases/<phase_id>/repair_attempts/ci_attempt_<n>/`
  (`provider_phase_dir`); `runs/**` is in `frontier.yaml` `artifacts.forbid_commit`
  (line 425) and untracked.

## 3. core.bare floor — PASS

- `status_doctor.check_core_bare`: `core.bare=true` → `report.fail(...)` with the exact fix
  command; unset/false → ok; other values → warn. Wired into `build_report` first. FAIL, not
  WARN (mutation-verified below).
- Driver preflight: `ensure_core_bare_false` probes `rev-parse --is-bare-repository`,
  restores via `git(ROOT, "config", "core.bare", "false")`, and emits `CORE_BARE_RESTORED`
  (with restore ok/stderr) — called at RUN_INIT (`initialize_provider_wired_run`), resume
  (`resume_provider_wired_run`), and stage-resume (`resume_provider_wired_stage`). Loud,
  never silent.
- `pr_merge.py` → `merge_pr` only. Every gh execution inside `merge_pr`
  (github_utils.py:1139–1471) goes through `gh_auth_status`/`view_pr`/`_run_gh`, all of
  which route through `_run_gh` — which holds `GIT_SERIAL_LOCK` and restores `core.bare`
  before releasing it (github_utils.py:144–162). No raw subprocess/gh outside the lock.
- BEHIND handling: `_pr_is_behind` → `gh pr update-branch <pr>` via `_run_gh`, re-view, then
  merge; update failure returns blocked `MERGE_BRANCH_UPDATE_BLOCKED` and the test verifies
  no merge command is issued afterward.
- `justfile` adds only `pr-merge number: python tools/frontier/pr_merge.py "{{number}}"`.

## 4. Test honesty + mutation tests — PASS with one warning

Runs with `~/.venvs/alpha_system_research/bin/python -m pytest` in the worktree:

- `tests/unit/frontier` → **14 passed**
- `tests/unit/test_status_doctor.py` → **9 passed**
- `tests/test_github_utils.py` → **28 passed**
- Combined run of all three → **51 passed** (matches executor's 14 / 40-subset claims:
  3 new ci-repair + 9 + 28 = 40).

Mutation tests (worktree verified byte-identical via diff sha256 before/after):

| name | expected | observed | result |
|---|---|---|---|
| budget check removed (`start_attempt >= max_attempts` dropped) | ≥1 test fails | `test_ci_failure_with_exhausted_budget_stops_with_ci_blocked` FAILED (driver routed a repair past budget; CI-wait fake queue exhausted) | CAUGHT |
| entry STOP check only bypassed (`if False and stop_requested` at first check) | ≥1 test fails | **3 passed** — later STOP checks compensate before `CI_REPAIR_ROUTED`/Codex | NOT CAUGHT (see W1) |
| ALL 5 STOP checks bypassed in `run_ci_repair_attempt` | ≥1 test fails | `test_stop_file_prevents_ci_repair_routing` FAILED | CAUGHT |
| status_doctor core.bare=true downgraded FAIL→WARN | status_doctor test fails | `test_core_bare_true_is_hard_failure_in_temp_repo` FAILED | CAUGHT |

The genuine "routing skips STOP" mutation (all checks removed) IS caught, so STOP semantics
are tested; the per-checkpoint granularity gap is a warning, not REWORK (see findings).

## 5. Project checks — PASS

- `python tools/verify.py --smoke` → exit 0 (no stdout, consistent with executor's honest
  note that it emits no count line).
- `python tools/hooks/canary_runner.py` → exit 0, all canaries PASS
  (`All Frontier canaries passed.`).
- `python tools/frontier/status_doctor.py` → exit 0, VERDICT: WARN (no live run state in
  this worktree — same WARN the executor reported; not caused by this diff).

## 6. TROUBLESHOOTING accuracy — PASS (independently reproduced)

Reproduced in a fresh `/tmp` scratch repo: `extensions.worktreeConfig=true` +
`--worktree core.sparseCheckout=true` left `rev-parse --is-bare-repository` = `false`;
`core.bare=true` immediately produced `fatal: this operation must be run in a work tree`;
`core.bare=false` restored function; removing the extension afterwards left the repo
non-bare and usable. Matches the doc's claims exactly: worktreeConfig is not sufficient by
itself; `core.bare=true` is the direct break. The diff contains no canonical-repo
extensions-config change; the only runtime `.git` write is the spec-authorized
`core.bare=false` restore.

## Findings

- **W1 (warning, test granularity)**: The STOP tests pin the aggregate property ("active
  STOP prevents CI repair routing") but not each individual checkpoint — bypassing only the
  entry STOP check leaves all tests green because the four downstream checks compensate.
  Under that single-check bypass the attempt counter is incremented and the phase is set
  `REWORK` before the second check blocks (budget slot consumed under active STOP), though
  no evidence collection, Codex call, push, or `CI_REPAIR_ROUTED` occurs. Suggested
  follow-up (non-blocking): a test that asserts `repair_attempts` is NOT consumed when STOP
  is present at entry.
- **W2 (observation, by design)**: CI repairs share the same `repair_attempts` budget as
  checks/review repairs — this matches the spec's "SAME bounded repair budget" wording, but
  it means earlier checks-stage repairs reduce remaining CI-repair headroom. Documenting so
  nobody mistakes it for a bug later.
- **W3 (observation)**: `test_stop_file_prevents_ci_repair_routing` does not assert the
  `CI_REPAIR_SKIPPED_STOP` event is emitted; coverage relies on the absence of
  `CI_REPAIR_ROUTED`/codex calls. Minor.

No scope violations, no gate weakening, no second truth, no committed run artifacts, no
reformatting churn, no untested safety floor.
