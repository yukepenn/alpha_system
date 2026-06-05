# Harness Notes (maintainability backlog)

The Frontier Harness machinery under `tools/frontier/` and `tools/hooks/` is
**real, complete, and safe**. This note records non-blocking maintainability
observations for a possible future, test-backed refactor. **None of these are
bugs or blockers**, and none should be acted on inside an unrelated campaign.

## Observations (deferred)

- **`tools/frontier/ralph_driver.py` is large (~4,750 lines).** It is the
  Workflow-2 driver (run init, phase execution, git/GitHub orchestration, CI/merge
  gates, repair loops, prompts). A future refactor could extract the prompt
  templates, the run-init helpers, and the per-stage phase logic into separate
  modules. This needs characterization tests first and is out of scope for routine
  work.
- **Guard constants are duplicated** between `tools/hooks/artifact_guard.py`
  (the pre-commit hook, kept dependency-light) and
  `tools/frontier/artifact_policy.py` (the frontier library). The duplication is
  intentional for hook speed but is a maintenance burden; a shared constants
  module would remove it. Behavior is currently correct and canary-verified.

## Do NOT alter semantics

If/when this backlog is addressed, the following must be preserved exactly:

- the Workflow-2 state machine and legal transitions (`state_machine.py`);
- the merge-gate decision and Red-lane authorization gates
  (`PROJECT_OP_AUTHORIZED` / `PROJECT_OP_SCOPE` / `PROJECT_OP_EXPIRES`);
- STOP-file checking and resume-precondition validation;
- artifact-policy enforcement and the explicit-staging / no-force-push /
  no `git add .` / no `git add -A` guards;
- the safety canary suite must stay green.

Strong safety behavior is the reason these remain *notes*, not *tasks*.
