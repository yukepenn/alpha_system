# P014500_WF2_RESUME_COMPLETENESS — Fresh Adversarial Review

- Reviewer: Claude (fresh adversarial, Workflow 1)
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-ci-selfheal` (branch `repair/wf2-resume-completeness`, base a8c62fe)
- Diff under review: UNCOMMITTED — `tools/frontier/ralph_driver.py` (+63/-2) + new
  `tests/unit/frontier/test_ralph_driver_resume_completeness.py` (untracked).
- Diff fingerprint (`git diff | sha256sum`): `391bdb4c710212fab100a93368f7d8857f2d31376f9e13bc240c84ff6f1b24aa`
  — verified identical before and after all mutation testing.

## 1. Scope — PASS

- Only `tools/frontier/ralph_driver.py` modified; one new test file. No
  `src/alpha_system/**`, no `tools/frontier/resume.py` change needed.
- No `WORKFLOW2_STAGES` reorder, no state-name changes
  (`PROVIDER_MIDPIPELINE_STATUSES` is a new constant naming six EXISTING
  statuses — exactly the provider-stage subset of `_resumable_statuses()`
  already used by `next_pending_provider_phase` / `next_scheduled_provider_phase`).
- STOP semantics untouched (no stop-check sites in the diff).
- Surgical: zero reformatting churn; `git diff --check` clean.

## 2. Verdict fidelity — PASS (one REWORK finding on tests, §4a)

Line-by-line on the exhaustion block in `run_provider_repair_loop`:

- **Same parser, no new lenient parser.** `parse_final_repair_review` calls
  `parse_review_text` (tools/frontier/verdict.py) — the identical function used
  by the normal review stage (ralph_driver.py:4724) and the in-loop repair
  review (:4959). It never reads JSON verdict files and never constructs a
  `ReviewVerdict` by hand.
- **Adoption condition**: `final_review.verdict in PASSING_VERDICTS and not
  final_review.required_repairs`. `PASSING_VERDICTS = {"PASS",
  "PASS_WITH_WARNINGS"}` (line 113). Note the required_repairs guard is
  provably defense-in-depth: `parse_review_text` forces
  `required_repairs=[]` for passing verdicts (verdict.py:221,
  `repairs if verdict in {"REWORK", "BLOCKED"} else []`), so a passing verdict
  with repairs is unreachable through this path (see mutation b).
- **Fail-closed on everything else**: unparseable/ambiguous review → parser
  returns synthetic BLOCKED with required_repairs → not adopted; missing
  `repair_review.md` inside an existing final attempt dir → `None` → not
  adopted. The synthetic-BLOCKED branch itself is byte-unchanged
  (`source="repair_exhausted"`, no parsed object → `raw_review_path: null`,
  event without `source` key) — asserted by the new negative test.
- **Never synthesizes/upgrades**: only a parser-produced verdict is adopted,
  recorded with the distinct source `repair_exhausted_final_review` in BOTH
  `verdict.json` and the `REPAIR_EXHAUSTED` event (with `verdict=` field).
- **No gate skipping**: the path mirrors the in-loop pass path byte-for-byte
  in effect (`write_provider_verdict` + `set_provider_phase_status("REVIEWED")`
  + return verdict). The caller (`execute_provider_phase`) then continues the
  NORMAL pipeline: handoff → semantic done_check (with REWORK/BLOCKED
  handling) → `post_phase_git_github` (commit → PR → CI → branch protection →
  merge gate → merge). Additionally the caller independently re-gates
  `if verdict not in PASSING_VERDICTS: block_provider_run(...)` — even a
  hypothetically mis-adopted non-passing verdict cannot pass a later gate.
- Minor (informational): when `attempt > 0` but the final attempt dir is
  absent, the helper falls back to phase `review.md`. That file is always
  reviewer-authored (the repair loop mirrors every repair review into it; the
  pre-repair content is the REWORK review that triggered repairs), so the
  fallback cannot adopt non-reviewer text. Acceptable.

## 3. Mid-pipeline resume — PASS

- `ready_wave_phases` now returns the current (then any) mid-pipeline provider
  phase as a one-phase wave BEFORE computing PENDING waves. The consumer
  (`run_dag_wave_parallel` → `run_wave_build` → `execute_provider_phase`)
  resumes via the EXISTING per-status if-chain: a REVIEWED phase emits
  `PHASE_RESUME`, reads cached `spec.md` / `executor_output.md` /
  `validation.md` / `review.md` / `verdict.json`, and continues at done_check.
  No spec regeneration, no re-execution of completed checkpointed stages;
  `prepare_phase_branch_for_execution` runs only at SPEC_READY, so resumed
  phases do not touch branch setup.
- Statuses with dedicated self-heal paths (GATE_BLOCKED, GIT_PHASE_BLOCKED,
  MERGE_PENDING/READY, WAITING_*) are correctly excluded from the new set.
- No infinite loop: a mid-pipeline phase that fails to progress leaves the
  set (block_provider_run → BLOCKED) or stalls the wave, which STOPs the run
  with a reason.
- Normal fresh runs unaffected: after every WAVE_COMPLETE all wave phases are
  PASS or stalled-non-mid-pipeline; the new branch only fires on resume entry.
- Genuine dependency starvation still deadlocks: with no mid-pipeline phase
  the function falls through to `dag_scheduler.compute_waves` unchanged
  (test d passes; mutation c reproduces the original deadlock).

## 4. Mutation tests (all under `~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/frontier tests/test_ralph_driver.py -q`; worktree restored byte-identically after each — final sha256 matches `391bdb4c…`)

| # | Mutation | Result | Outcome |
|---|----------|--------|---------|
| a | Fidelity path adopts REWORK (`PASSING_VERDICTS \| {"REWORK"}`) | **84 passed — SURVIVED** | **FINDING (required repair)** |
| b | Drop `and not final_review.required_repairs` | 84 passed — survived, **proven equivalent mutant** | Documented, no repair |
| c | Remove mid-pipeline continuation block | **1 failed** (`test_targeted_done_check_resume…` hits SCHEDULE_DEADLOCK) | KILLED |
| d | Skip done_check gate (`if False:`) — REVIEWED jumps to commit | **2 failed** (`test_targeted_done_check_resume…` checkpoint assert + `test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase`) | KILLED |

- **(a) detail**: no test in the repo exercises repair-exhaustion with a
  PARSEABLE failing final review (`grep -rn repair_exhausted tests/` matches
  only the new file; its negative test uses an UNPARSEABLE review, which the
  parser maps to BLOCKED, so widening the adoption set to REWORK is invisible
  to the suite). Spec scope item 3b explicitly required
  "failing/unparseable"; only unparseable was delivered. Severity context: the
  mutant cannot merge a non-passing phase (caller's `verdict not in
  PASSING_VERDICTS` gate blocks it), so the exposure is verdict-artifact
  fidelity (a REWORK recorded with `source=repair_exhausted_final_review`
  and transient REVIEWED status), not auto-approval. Still a hard miss against
  the phase's own test contract on the most safety-critical surface.
- **(b) detail**: equivalent-mutant proof — `parse_final_repair_review` only
  produces verdicts via `parse_review_text`, which structurally zeroes
  `required_repairs` for PASS/PASS_WITH_WARNINGS (verdict.py:221). No test can
  kill this mutant without bypassing the shared parser; the protected property
  is enforced one layer down in the SAME parser the normal VERDICT_PARSE stage
  uses. Guard retained as defense-in-depth — correct.

## 5. Validation (this reviewer, in the worktree)

- `pytest tests/unit/frontier tests/test_ralph_driver.py -q`: **84 passed**
  (18 in tests/unit/frontier incl. the 4 new; 66 in test_ralph_driver.py), exit 0.
- `python tools/verify.py --smoke`: exit 0.
- `python tools/hooks/canary_runner.py`: **21 PASS**, "All Frontier canaries passed.", exit 0.
- `python tools/frontier/status_doctor.py`: **4 ok / 1 WARN**, exit 0
  (WARN = no live run dir with state.json for DISCOVERY_RIGOR_FLOOR_V1 in this
  worktree — expected, no live run there).

## 6. Artifact policy — PASS

- Nothing staged (`git diff --cached` empty); working tree contains exactly
  the two intended paths.
- No `runs/` directory exists in the worktree; test runs write under pytest
  tmp_path (monkeypatched ROOT). `git ls-files runs` → empty.

## Reviewer incident disclosure

During mutation testing this reviewer briefly reverted the uncommitted diff
with `git checkout -- tools/frontier/ralph_driver.py` (restore step of
mutation a). The diff was re-applied from the captured patch and verified
byte-identical via sha256 (`391bdb4c…` before review == after all mutations),
and the full suite re-passed (84). No content was lost.

## Findings

1. **[REQUIRED REPAIR — test gap, spec 3b]** Add one test:
   repair-exhaustion whose final `repair_review.md` parses to `VERDICT: REWORK`
   (no repair-section bullets, so `required_repairs == []`) → assert
   `verdict.json` is the synthetic BLOCKED (`source == "repair_exhausted"`,
   `raw_review_path` null) and the phase does NOT get
   `repair_exhausted_final_review`. This kills surviving mutation (a). One
   test function in the existing new test file; no production-code change
   required.
2. [INFO] `parse_final_repair_review` fallback to phase `review.md` when the
   final attempt dir is missing is reviewer-authored-only; acceptable.
3. [INFO] Mutation (b) is an equivalent mutant; property enforced by the
   shared parser (verdict.py:221). Keep the guard.

## VERDICT: REWORK

Single required repair (finding 1). Everything else — scope, verdict-fidelity
semantics, gate continuity, mid-pipeline resume mechanics, deadlock
preservation, validation, artifact policy — is clean and deterministic.

## REWORK resolution (re-review)

- Re-reviewer: Claude (fresh re-review, Workflow 1), 2026-06-11. Scope:
  finding 1 only.
- **Delta since review is test-only.** `git diff --name-only` shows only
  `tools/frontier/ralph_driver.py`, and
  `git diff tools/frontier/ralph_driver.py | sha256sum` still equals
  `391bdb4c710212fab100a93368f7d8857f2d31376f9e13bc240c84ff6f1b24aa` — the
  production diff is byte-identical to the one this review examined. The only
  other working-tree path is the untracked test file, which gained exactly one
  new test.
- **Repair delivered**:
  `test_repair_exhaustion_parseable_rework_final_review_stays_synthetic_blocked`
  (tests/unit/frontier/test_ralph_driver_resume_completeness.py:198). Final
  `repair_review.md` is a clean parseable `VERDICT: REWORK` with no repair
  bullets; the test asserts the exhaustion path returns BLOCKED, the phase
  stays REWORK (no REVIEWED transition), `verdict.json` is the synthetic
  BLOCKED (`source == "repair_exhausted"`, `raw_review_path` null), and the
  `REPAIR_EXHAUSTED` event carries neither `source` nor `verdict` keys —
  exactly the contract finding 1 demanded, plus the status assertion.
- **Suite**: `pytest tests/unit/frontier tests/test_ralph_driver.py -q` →
  **85 passed** (84 + the new test), exit 0.
- **Mutation (a) re-run by this re-reviewer**: widened the fidelity-path
  adoption set to `PASSING_VERDICTS | {"REWORK"}` (ralph_driver.py:4985) →
  **1 failed, 84 passed**; the single failure is the new test
  (`assert 'REWORK' == 'BLOCKED'`). Mutation (a) is **KILLED**. Side proof:
  under the mutant the adopted verdict was REWORK, confirming the test review
  parses to a clean REWORK with `required_repairs == []` (parseable path, not
  the unparseable fallback).
- **Restore verified**: mutant reverted; production diff sha256 again
  `391bdb4c…`; suite re-passed (85).
- Informational findings 2 and 3 stand as documented; no repair required.

## FINAL VERDICT: PASS_WITH_WARNINGS

Required repair resolved with deterministic mutation evidence; warnings are
the two informational findings only.
