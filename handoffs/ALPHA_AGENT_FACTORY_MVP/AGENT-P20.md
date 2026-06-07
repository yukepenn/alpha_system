# AGENT-P20 Handoff

## Scope

Phase: `AGENT-P20` - Agent Factory Docs and Operator Guide.

Implemented documentation-only scope:

- `docs/agent_factory/GUIDE.md`
- `docs/agent_factory/OPERATOR.md`
- `docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P20.md`

No `agent_factory` code, tests, runtime bridge code, templates, sibling Wave-3
docs, consumed primitive packages, `ACTIVE_CAMPAIGN.md`, review artifact, or
verdict artifact was created or modified by Codex.

## Explicit Staging

Executor-staged file list: none.

The executor prompt explicitly forbade `git add`, `git commit`, `git push`,
`git status`, and `git diff`, and required all changes to remain unstaged for
Ralph. Ralph should explicitly stage only these commit-eligible paths if the
phase passes driver validation:

```text
docs/agent_factory/GUIDE.md
docs/agent_factory/OPERATOR.md
docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md
README.md
handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P20.md
```

No review files are listed because Codex was instructed not to call Claude, not
to run reviewer, not to create `review.md`, and not to create `verdict.json`.

## Validation Results

Working directory for commands:
`/home/yuke_zhang/projects/alpha_system-alpha_agent_factory_mvp-agent-p20`.

Required validation:

| Command | Result |
| --- | --- |
| `git status --short` | Skipped. The executor prompt explicitly forbids `git status`. |
| `python tools/verify.py --smoke` | PASS, exit 0, no stdout. |
| `test -f docs/agent_factory/GUIDE.md` | PASS, exit 0. |
| `test -f docs/agent_factory/OPERATOR.md` | PASS, exit 0. |
| `test -f docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md` | PASS, exit 0. |
| `test -f README.md` | PASS, exit 0. |
| `git ls-files runs` | PASS, exit 0, output empty. |

Supplementary checks:

| Command | Result |
| --- | --- |
| `git status --short -- src templates/agent_factory/prompts docs/agent_factory/RUNTIME_BRIDGE.md` | Skipped. The executor prompt explicitly forbids `git status`. |
| `grep -REn "profitab\|tradab\|alpha is\|live trading\|paper trading\|broker\|deploy" docs/agent_factory/GUIDE.md docs/agent_factory/OPERATOR.md docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md \|\| echo "no obvious claim/scope language found (still review wording)"` | PASS, exit 0. Hits were manually reviewed and are explicit prohibition/no-claims boundary language only: `OPERATOR.md:6-7`, `OPERATOR.md:107`, `NEXT_CORE_ALPHA_PILOT_READINESS.md:8-9`, `NEXT_CORE_ALPHA_PILOT_READINESS.md:45-46`. |

Additional local checks run by Codex:

| Command | Result |
| --- | --- |
| `if test -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP; then printf 'STOP present\n'; else printf 'STOP absent\n'; fi` | PASS, exit 0, output `STOP absent`. |
| `test -f docs/agent_factory/GUIDE.md && test -f docs/agent_factory/OPERATOR.md && test -f docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md && test -f README.md` | PASS, exit 0. |

Final post-handoff validation pass:

| Command | Result |
| --- | --- |
| `python tools/verify.py --smoke` | PASS, exit 0, no stdout. |
| `test -f docs/agent_factory/GUIDE.md && test -f docs/agent_factory/OPERATOR.md && test -f docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md && test -f README.md && test -f handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P20.md` | PASS, exit 0. |
| `git ls-files runs` | PASS, exit 0, output empty. |
| `grep -REn "profitab\|tradab\|alpha is\|live trading\|paper trading\|broker\|deploy" docs/agent_factory/GUIDE.md docs/agent_factory/OPERATOR.md docs/agent_factory/NEXT_CORE_ALPHA_PILOT_READINESS.md \|\| echo "no obvious claim/scope language found (still review wording)"` | PASS, exit 0. Hits remained the same explicit prohibition/no-claims boundary language only: `OPERATOR.md:6-7`, `OPERATOR.md:107`, `NEXT_CORE_ALPHA_PILOT_READINESS.md:8-9`, `NEXT_CORE_ALPHA_PILOT_READINESS.md:45-46`. |

Read-only context commands run before editing, all exit 0:

- `sed -n '1,220p' /home/yuke_zhang/projects/alpha_system-alpha_agent_factory_mvp-agent-p20/.codex/skills/frontier-execute/SKILL.md`
- `rg --files docs/agent_factory docs decisions campaigns specs handoffs README.md frontier.yaml ACTIVE_CAMPAIGN.md | sort`
- `sed -n '1,240p' frontier.yaml`
- `sed -n '1,200p' ACTIVE_CAMPAIGN.md`
- `sed -n '1,260p' campaigns/ALPHA_AGENT_FACTORY_MVP/GOAL.md`
- `sed -n '1,280p' campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md`
- `sed -n '1,260p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml`
- `sed -n '1,240p' docs/agent_factory/PREFLIGHT_GATES.md`
- `sed -n '1,260p' docs/agent_factory/ROLES.md`
- `sed -n '1,280p' docs/agent_factory/PERMISSIONS.md`
- `sed -n '1,280p' docs/agent_factory/TOOLS.md`
- `sed -n '1,280p' docs/agent_factory/RESEARCH_QUEUE.md`
- `sed -n '1,300p' docs/agent_factory/SEPARATION_OF_DUTIES.md`
- `sed -n '1,280p' docs/agent_factory/HANDOFFS.md`
- `sed -n '1,320p' docs/agent_factory/REJECTION_MEMORY.md`
- `sed -n '1,260p' README.md`
- `sed -n '1,240p' docs/agent_factory/README.md`
- `sed -n '1,260p' docs/agent_factory/OVERVIEW.md`
- `sed -n '1,260p' docs/RESEARCH_INTERPRETATION_POLICY.md`
- `sed -n '1,260p' decisions/0006-feature-label-value-storage.md`
- `rg -n "FEATURE_LABEL_PARQUET_SINK|SESSION_LABEL_GUARD|report-rehydration|rehydration|dataset-registry" docs/STRUCTURAL_BACKLOG.md docs/**/*.md decisions/0006-feature-label-value-storage.md campaigns/ALPHA_AGENT_FACTORY_MVP -g '*.md' -g '*.yaml'`
- `sed -n '1,260p' docs/STRUCTURAL_BACKLOG.md`
- `rg -n "runtime|agent_factory|dry-run|dry run|frontier|verify|target|TARGET" docs/CLI_REFERENCE.md docs/CLI_COMMANDS_TARGET.md docs/AI_AGENT_GUIDE.md docs/RESEARCHER_GUIDE.md docs/agent_factory/*.md docs/research_runtime/CLI.md docs/research_runtime/E2E_DRY_RUN.md`
- `sed -n '240,285p' campaigns/ALPHA_AGENT_FACTORY_MVP/GOAL.md`
- `sed -n '300,360p' campaigns/ALPHA_AGENT_FACTORY_MVP/RUNBOOK.md`
- `sed -n '815,835p' campaigns/ALPHA_AGENT_FACTORY_MVP/RUNBOOK.md`
- `sed -n '1,150p' docs/research_runtime/CLI.md`
- `rg -n "class ResearchTaskStatus|RESEARCH_TASK_QUEUED|REFERENCE_HANDOFF_RECORDED|LIBRARIAN_MEMORY_RECORDED|ALPHASPEC|STATISTICAL_REVIEW" src/alpha_system/agent_factory docs/agent_factory campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml`
- `rg --files src/alpha_system/agent_factory tests/unit/agent_factory templates/agent_factory | sort`
- `find docs/agent_factory -maxdepth 1 -type f -printf '%f\n' | sort`
- `sed -n '45,75p' src/alpha_system/agent_factory/queue/models.py`
- `sed -n '255,305p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml`
- `sed -n '1,220p' docs/agent_factory/roles/diagnostics_runner.md`
- `sed -n '1,220p' docs/agent_factory/roles/statistical_reviewer.md`

## Artifact Audit

- `git ls-files runs` returned empty.
- Codex staged nothing.
- The intended explicit-stage list above contains no `runs/` path and no
  raw/canonical/feature/label/runtime/agent value path, data path, DB path,
  cache path, log path, or heavy artifact suffix.
- No generated local-only artifact under `runs/**` was staged or committed.
- The run-local `handoff.md` under
  `runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P20/` was not
  staged; Codex did not create it.

Ralph must perform the authoritative staged-set audit after staging because the
executor prompt forbade `git status` and `git diff --cached --name-only`.

## Scope Confirmations

- Docs-only changes were made.
- No `.py` file under `src/**` or `tests/**` was edited.
- No consumed primitive package was edited.
- No sibling Wave-3 path was edited:
  `templates/agent_factory/prompts/**` was not edited, and
  `docs/agent_factory/RUNTIME_BRIDGE.md` was not created or edited.
- `ACTIVE_CAMPAIGN.md` was not edited.
- No broker, live, paper, order, account, provider, deployment, PR, merge, or
  reviewer operation was performed.
- The new docs use no-claims language and frame seed/synthetic dry-run output,
  `EvidenceDraft`, `ReferenceCandidateHandoff`, and runtime diagnostic `PASS`
  as non-promotional, non-candidate, non-validation artifacts.

## Caveats

- `git status --short` output is unavailable because the prompt explicitly
  forbade running `git status`.
- No review artifact or verdict was created by Codex. YELLOW review remains
  Ralph/reviewer-owned.
- No phase PASS is asserted by this handoff.
