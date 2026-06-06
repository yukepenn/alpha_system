# Handoff — AGENT-P06: Research Queue and Work Item Contracts

## Branch And Commit Context

- Branch: `auto/alpha_agent_factory_mvp/agent-p06-research-queue-and-work-item-contracts`
- Base HEAD observed: `ecf31b7`
- Commits by Codex: none. Per executor safety rules, Codex did not stage, commit, push, create a PR, merge, call Claude, run reviewer, create `review.md`, or create `verdict.json`.

## Explicit File List For Ralph Staging

Stage these paths explicitly if Ralph accepts this executor output:

- `src/alpha_system/agent_factory/queue/__init__.py`
- `src/alpha_system/agent_factory/queue/models.py`
- `tests/unit/agent_factory/queue/__init__.py`
- `tests/unit/agent_factory/queue/test_models.py`
- `docs/agent_factory/RESEARCH_QUEUE.md`
- `templates/agent_factory/research_task.template.yaml`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P06.md`

No `runs/` path should be staged.

## Scope Completed

- Added `alpha_system.agent_factory.queue.models` with frozen, value-free contracts for `ResearchQueue`, `ResearchTask`, `AgentAssignment`, `ResearchBudget`, `VariantBudget`, `ComputeBudget`, `RetryPolicy`, `ReviewRequirement`, `BlockerRecord`, `QueuePriorityPolicy`, and `FamilyBudgetPolicy`.
- Enforced mandatory finite budgets, small-set alpha-family scope, accepted DatasetVersion states, id/ref-only FeaturePack and LabelPack inputs, allowed/blocked partitions, locked-test metadata guard, bounded retries, required independent reviews, and per-family queue caps.
- Rejected prohibited MVP lifecycle states including `AUTONOMOUS_RESEARCH_RUNNING`.
- Kept the queue single-task-bounded: no scheduler, next-cycle field, auto-enqueue-from-results behavior, continuous runner, data read, runtime call, alpha search, promotion, or broker/paper/live/order scope.
- Added focused unit tests, durable documentation, a synthetic value-free research task template, and the compact README snapshot update for P06/P07.

## Validation Run

- `test -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP`
  - Result: exit 1; interpreted as no active STOP file present at that run path.
- `python -c "import alpha_system.agent_factory.queue.models"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not have the repository `src/` directory on `PYTHONPATH`; no package install was performed because that would create environment/repo side effects outside the phase spec.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.queue.models"`
  - Result: PASS, exit 0, no stdout.
- `python tools/verify.py --smoke`
  - Result: PASS, exit 0, no stdout.
- `python -m pytest tests/unit/agent_factory/queue -q`
  - Initial implementation runs failed during collection with helper-order `NameError`s; the tests were corrected.
  - Final result: PASS, `40 passed in 0.04s`.
- `test -f docs/agent_factory/RESEARCH_QUEUE.md`
  - Result: PASS, exit 0.
- `test -f templates/agent_factory/research_task.template.yaml`
  - Result: PASS, exit 0.
- `test -f README.md`
  - Result: PASS, exit 0.
- `git ls-files runs`
  - Result: PASS, empty output.

## Required Skips And Artifact Audit

- `git status --short`: SKIPPED. The executor safety rules explicitly forbade `git status`; no output was collected.
- `git diff` / `git diff --cached`: SKIPPED. The executor safety rules explicitly forbade `git diff`.
- Staging audit: Codex performed no staging. Because `git status` and `git diff --cached` were forbidden, the staged-set audit is left to Ralph. Codex created no staged forbidden path.
- Run artifact audit: `git ls-files runs` returned empty output.
- Run-local handoff: not written. The commit-eligible handoff is this file, and all `runs/**` artifacts remain local-only.
- Reviewer artifacts: not created by Codex, per executor safety rules. Ralph/Claude owns review and verdict generation.

## Caveats And Review Focus

- Review should focus on strict phase scope: contracts only, no runtime/data access, no continuous runner shape, finite variant/compute budgets, prohibited lifecycle states rejected, value-free validation, partition/blocker semantics, assignment not granting permissions, README snapshot accuracy, and no consumed primitive edits.
- The exact bare `python -c` import command failed only because this local shell lacks `PYTHONPATH=src`; the import passed with the repository source path set, and pytest/verify smoke passed from the repo context.

## Next Recommended Step

Ralph should perform the authoritative staging audit, stage the explicit file list above, run its configured validation, then route the required independent YELLOW review.
