# Handoff - AGENT-P08: Hypothesis Scout Role Contract

## Branch And Commit Context

- Phase: `AGENT-P08`
- Campaign: `ALPHA_AGENT_FACTORY_MVP`
- Executor: Codex
- Codex staging/commit/push: none. Per executor safety rules, Codex did not
  run `git add`, `git commit`, `git push`, create a PR, merge, call Claude, run
  reviewer, create `review.md`, create `verdict.json`, or mark the phase PASS.

## Explicit File List For Ralph Staging

Stage these paths explicitly if Ralph accepts this executor output:

- `src/alpha_system/agent_factory/roles/hypothesis_scout.py`
- `tests/unit/agent_factory/roles/test_hypothesis_scout.py`
- `docs/agent_factory/roles/hypothesis_scout.md`
- `templates/agent_factory/roles/hypothesis_scout.md`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P08.md`

No `runs/` path should be staged.

## Scope Completed

- Added `alpha_system.agent_factory.roles.hypothesis_scout`.
- The role self-registers through `roles.registry.register` at import time and
  does not edit `roles/__init__.py` or `roles/registry.py`.
- The `AgentRole` contract declares purpose, readable inputs, callable tool
  ids, producible outputs, allowed decisions, forbidden decisions/actions,
  handoff format, reviewer independence, and failure modes.
- Added value-free contract helper shapes for `AlphaSpecDraftRef`,
  `RejectionReasonRecordRef`, and an AGENT-P08-local `AgentHandoff` shape until
  the shared AGENT-P17 record exists.
- Added pure validation helpers for 3-5 draft refs, scoped task/assignment
  matching, VariantBudget enforcement, prior-rejection surfacing, value-free
  `AgentToolResult` construction, handoff construction, `BLOCKED`, and
  `INPUTS_BLOCKED` result shapes.
- Added unit tests with synthetic fixtures only.
- Added the durable role doc and role operating template.
- Applied the compact README snapshot for AGENT-P08 in the campaign-progress
  region.

## Validation Run

- `find runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP -maxdepth 1 -name STOP -print`
  - Result: exit 1, `No such file or directory`.
  - Interpretation: the requested run directory is absent in this worktree, so
    no STOP file was present at that path.
- `python -c "import alpha_system.agent_factory.roles.hypothesis_scout"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not expose repository `src/` on `PYTHONPATH`; no
    package install was performed because that would create environment side
    effects outside the phase.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.hypothesis_scout"`
  - Result: PASS, exit 0, no stdout.
- `python tools/verify.py --smoke`
  - Result: PASS, exit 0, no stdout.
- `python -m pytest tests/unit/agent_factory/roles/test_hypothesis_scout.py -q`
  - Result: PASS, `8 passed in 0.04s`.
- `test -f docs/agent_factory/roles/hypothesis_scout.md`
  - Result: PASS, exit 0.
- `test -f templates/agent_factory/roles/hypothesis_scout.md`
  - Result: PASS, exit 0.
- `test -f README.md`
  - Result: PASS, exit 0.
- `test -f handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P08.md`
  - Result: PASS, exit 0.
- `git ls-files runs`
  - Result: PASS, empty output.
- `rg -n "hypothesis_scout" src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py`
  - Result: exit 1, empty output.
  - Interpretation: neither shared role package file hard-imports the concrete
    Hypothesis Scout module.
- `find reviews/ALPHA_AGENT_FACTORY_MVP -maxdepth 2 -path '*AGENT-P08*' -print`
  - Result: exit 1, `No such file or directory`.
  - Interpretation: no review artifact was created by Codex.
- `find runs -path '*AGENT-P08*' -maxdepth 5 -print`
  - Result: exit 1, `No such file or directory`.
  - Interpretation: no run-local AGENT-P08 artifact was created by Codex.

## Required Skips And Artifact Audit

- `git status --short`: SKIPPED. The executor safety rules explicitly forbade
  `git status`; no output was collected.
- `git diff --name-only HEAD -- src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py`:
  SKIPPED. The executor safety rules explicitly forbade `git diff`.
- `git diff --cached --name-only`: SKIPPED. The executor safety rules
  explicitly forbade `git diff`, and Codex performed no staging.
- Staged-set audit: left to Ralph. Codex did not stage anything.
- Run artifact audit: `git ls-files runs` returned empty output.
- Run-local handoff: not written. The commit-eligible handoff is this file.
- Reviewer artifacts: not created by Codex. Ralph/Claude owns review and
  verdict generation.

## Boundary Confirmations

- `roles/__init__.py` and `roles/registry.py` were not edited by Codex; the role
  registers by discovery when `alpha_system.agent_factory.roles.hypothesis_scout`
  is imported.
- No consumed primitive package was edited: no changes were made under
  `runtime`, `governance`, `research`, `experiments`, `backtest`, `features`,
  `labels`, `data`, `cli`, broker, live, paper, or order-routing paths.
- No data, raw/canonical/factor/label/cache values, provider responses, heavy
  artifacts, local DBs, logs, or caches were created.
- No autonomous agent was instantiated, no continuous runner was started, no
  runtime diagnostics ran, no dataset was resolved, no broker/paper/live/order
  action occurred, and no external provider was called.
- The README snapshot was applied compactly near the campaign-progress region.
- `ACTIVE_CAMPAIGN.md` was not touched.

## Caveats And Review Focus

- The P04 permission matrix in this checkout grants `hypothesis_scout` the tool
  ids `memory.lookup_rejected_ideas`, `library.summarize_prior_work`, and
  `alphaspec.draft`. The P05 tool-registry config in this checkout does not
  contain concrete contracts for those three ids. AGENT-P08 is forbidden from
  editing the shared tool registry, so the role references the P04 ids and
  treats unavailable summaries as `INPUTS_BLOCKED`. Ralph/reviewer should decide
  whether the tool-registry gap is an in-scope predecessor issue or an
  acceptable deferred integration point.
- The `AgentHandoff` dataclass is local to AGENT-P08 because the shared
  AGENT-P17 handoff-record module does not exist yet. It is value-free and can
  be replaced by the shared record when AGENT-P17 lands.
- This is a contract only. A drafted `AlphaSpec` ref is not implementation
  approval, not evidence, not a review verdict, not a promotion decision, and
  not an alpha, tradability, profitability, strategy, paper/live, broker,
  deployment, or production-readiness claim.

## Next Recommended Step

Ralph should perform the authoritative staging audit, stage the explicit file
list above if accepted, run its configured validation, then route the required
independent YELLOW review.
