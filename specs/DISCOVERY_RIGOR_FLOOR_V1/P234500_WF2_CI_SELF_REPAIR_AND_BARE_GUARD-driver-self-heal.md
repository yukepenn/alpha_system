---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P234500_WF2_CI_SELF_REPAIR_AND_BARE_GUARD
lane: yellow
status: in_progress
---

# P234500_WF2_CI_SELF_REPAIR_AND_BARE_GUARD: WF2 self-heals CI failures; core.bare can never silently persist

## Purpose

Two recurring coordinator-touch classes must become self-healing harness
behavior:

1. **CI_BLOCKED stops.** Today `ralph_driver.py` stops the run when a phase
   PR's CI fails (`CI_BLOCKED` at ~:3330 and resume path ~:4077), even though
   the driver already has a bounded repair loop for checks/review failures
   (`max_repair_attempts_for_phase` ~:2587, repair routing ~:4639). Every CI
   failure (LCFP-P08 saga, RIGOR-P01 tonight) requires a human/coordinator to
   diagnose, repair, push, and stage-resume. CI failures should route through
   the SAME bounded repair budget before stopping.
2. **core.bare=true flips.** `gh pr merge` (and gh branch-deletion paths)
   transiently flip the canonical repo's shared config to `core.bare=true`.
   The harness already restores it around its OWN gh calls
   (`tools/frontier/github_utils.py:140-161` `_run_gh`, `ralph_driver.py:3396-3419`),
   but coordinator-shell raw `gh pr merge` invocations and any unknown writer
   bypass that wrapper, leaving the repo broken until manually fixed.

## Scope (in-bounds)

### 1. CI_BLOCKED → bounded repair routing (ralph_driver.py, surgical)

- At both CI-failure sites (run path and resume path): before emitting
  `CI_BLOCKED` and stopping, if `repair_attempts[phase] < max_repair_attempts_for_phase(...)`:
  a. Check STOP file (existing stop-check helper) — active STOP wins.
  b. Collect failure evidence: failing CI job log excerpts via the existing
     github utils (e.g. `gh run view <id> --log-failed`, truncated to a sane
     byte budget) into
     `runs/<run_id>/phases/<phase_id>/repair_attempts/ci_attempt_<n>/ci_failure.log`
     (run-local only, never committed).
  c. Route a scoped Codex repair in the existing phase worktree using the
     existing repair-prompt machinery, with the phase spec + CI failure log +
     instruction to repair ONLY the CI failure in-scope (no gate weakening,
     no `git worktree`, no `.git` config edits).
  d. Re-run the phase's authorized checks; on green, commit (explicit paths)
     and push to the existing PR branch; increment `repair_attempts`; emit a
     `CI_REPAIR_ROUTED` event; re-enter CI wait.
  e. On budget exhausted or repair failure: current behavior (CI_BLOCKED stop)
     unchanged.
- No new state names in the public state order; this is internal routing
  inside the CI gate, mirroring how checks-stage repair routing works.

### 2. core.bare floor (never silently wrong)

- `tools/frontier/status_doctor.py`: add a check — canonical repo
  `core.bare` must be `false`; if `true`, report FAIL (not WARN) with the
  exact fix command. Doctor remains read-only (no auto-fix).
- `ralph_driver.py` preflight (RUN_INIT and resume entry): assert
  `core.bare=false`; if flipped, restore via existing
  `git(ROOT, "config", "core.bare", "false")` pattern and emit a
  `CORE_BARE_RESTORED` event (loud, never silent).
- `justfile`: add `pr-merge number` recipe that merges a PR through a tiny
  new `tools/frontier/pr_merge.py` entrypoint which calls the EXISTING locked
  `_run_gh`-based merge path (squash + update-branch-when-BEHIND + core.bare
  restore). This gives the coordinator a safe substitute for raw
  `gh pr merge`.
- INVESTIGATION (document, do not blind-apply): determine in a SCRATCH repo
  (under /tmp, never the canonical repo) whether `extensions.worktreeConfig=true`
  (enabled historically by sparse-checkout ops; all existing
  `config.worktree` files only hold sparse-checkout defaults) is a necessary
  enabler of the gh flip, and whether it can be safely removed once linked
  worktrees are pruned. Record findings + recommendation in the handoff and
  in `docs/TROUBLESHOOTING.md` under a new "core.bare flips" entry. Do NOT
  change the canonical repo's extensions config in this phase.

### 3. Tests

- Driver mock-mode tests (pattern: existing tests under
  `tests/unit/frontier/` for ralph_driver state machine): (a) CI failure with
  remaining budget routes repair (event sequence contains CI_REPAIR_ROUTED,
  not CI_BLOCKED) and re-enters CI wait; (b) CI failure with exhausted budget
  stops with CI_BLOCKED exactly as today; (c) STOP file present pre-repair →
  no repair routed.
- status_doctor test: core.bare=true in a temp repo → FAIL line present.
- Mutation-style assertion: deleting the budget check must break test (a)/(b)
  asymmetrically — reviewer will verify.

## Hard constraints

- `ralph_driver.py` edits must be SURGICAL: no reformatting, no import
  reordering, no wholesale style changes (local ruff differs from CI — do not
  format the file).
- Do not weaken any merge gate, review gate, artifact check, or STOP
  semantics. Repair routing must check STOP before every step.
- No changes under `src/alpha_system/**` (harness-only phase).
- No `git worktree` commands; no `.git` config edits in the canonical repo;
  explicit staging only; runs/** stays local.
- Research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/frontier -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
python tools/frontier/status_doctor.py
```

Exact counts in the handoff; note any skipped check with reason.

## Done criteria

- CI failures route through the bounded repair budget before stopping;
  exhausted budget preserves today's CI_BLOCKED semantics; core.bare cannot
  persist silently (doctor FAIL + driver preflight restore event + safe
  coordinator merge recipe); scratch-repo investigation documented; tests
  green; truthful handoff; fresh adversarial review PASS or
  PASS_WITH_WARNINGS under `reviews/DISCOVERY_RIGOR_FLOOR_V1/`.
