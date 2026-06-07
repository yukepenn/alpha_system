# AGENT-P24 Handoff - Workflow 2 DAG Integration and Parallel Plan

## Scope Completed

Implemented the documentation-only `ALPHA_AGENT_FACTORY_MVP/AGENT-P24` scope.

Added:

- `docs/agent_factory/WORKFLOW2_DAG.md`

Updated:

- `README.md`

The new durable DAG document records the `workflow2.scheduler` configuration
from `campaign.yaml`, the intended W0-W4 wave plan, the exact 18-wave
`frontier-plan` preview, parallel-safe disjointness rules, the serial merge
queue, coordinator-only `ACTIVE_CAMPAIGN.md` ownership, and the operator
verification commands. No code, tests, scheduler files, campaign files,
consumed primitives, review artifacts, verdict artifacts, run artifacts, PRs,
or merge actions were created by Codex.

## Executor Staging

Codex staged no files. The executor instructions explicitly forbade `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes were left
unstaged for Ralph/the driver.

Exact staged file list from Codex actions: none.

Expected explicit commit-eligible file list for Ralph staging:

```text
docs/agent_factory/WORKFLOW2_DAG.md
README.md
handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P24.md
```

No `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P24/**` files were created by Codex
because the executor prompt forbade calling Claude, running reviewer, creating
`review.md`, and creating `verdict.json`.

## Git Status Output

`git status --short` was not run. The executor prompt explicitly prohibits
Codex from running `git status`, so there is no `git status --short` output
from this executor turn. Ralph owns authoritative working-tree and staged-set
inspection after Codex finishes.

## Validation Results

Required validation:

| Command | Result |
| --- | --- |
| `git status --short` | SKIPPED; executor instructions explicitly prohibit Codex from running `git status`. |
| `python tools/verify.py --smoke` | PASS, exit 0. |
| `test -f docs/agent_factory/WORKFLOW2_DAG.md` | PASS, exit 0. |
| `git ls-files runs` | PASS, exit 0 with empty output. |

Supplemental consistency checks:

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP` | PASS, exit 0; STOP absent before execution. |
| `just frontier-plan ALPHA_AGENT_FACTORY_MVP` | PASS, exit 0; reported `dag_wave`, `max_parallel_phases: 3`, 18 waves, max width 3, parallel waves 7-9 and 13, and run-alone phases P00-P06, P16-P18, P22-P25. |
| `grep -q "dag_wave" docs/agent_factory/WORKFLOW2_DAG.md` | PASS, exit 0. |
| `grep -q "serial" docs/agent_factory/WORKFLOW2_DAG.md` | PASS, exit 0. |
| `grep -q "coordinator_only" docs/agent_factory/WORKFLOW2_DAG.md` | PASS, exit 0. |
| `just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3` | SKIPPED; this docs-only executor is not starting a live parallel run, and the phase validation section required documenting the command rather than running the mock driver. |

Context/source reads performed:

| Command | Result |
| --- | --- |
| `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md` | PASS, exit 0. |
| `sed -n '1,260p' AGENTS.md` | PASS, exit 0. |
| `sed -n '1,260p' frontier.yaml` | PASS, exit 0. |
| `rg --files -g 'campaign.yaml' -g 'PHASE_PLAN.md' -g 'ACCEPTANCE.md' -g 'README.md' -g 'AGENT-P24.md'` | PASS, exit 0. |
| `sed -n '1,320p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` | PASS, exit 0. |
| `sed -n '1,360p' campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md` | PASS, exit 0. |
| `sed -n '1,320p' campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md` | PASS, exit 0. |
| `sed -n '1,280p' README.md` | PASS, exit 0. |
| `rg --files handoffs/ALPHA_AGENT_FACTORY_MVP reviews/ALPHA_AGENT_FACTORY_MVP specs/ALPHA_AGENT_FACTORY_MVP runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P24` | Non-blocking context read; listed existing handoffs and reported missing optional reviews/specs/run phase directories. |
| `rg -n "workflow2:\|scheduler:\|AGENT-P0[7-9]\|AGENT-P1[0-9]\|AGENT-P2[0-5]\|parallel_safe\|must_run_alone\|allowed_paths\|merge_group\|update_active_campaign\|frontier-plan\|frontier-run-parallel-mock\|ACTIVE_CAMPAIGN" campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` | PASS, exit 0. |
| `rg -n "DAG\|Wave\|AGENT-P24\|frontier-plan\|parallel\|serial\|ACTIVE_CAMPAIGN\|coordinator" campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md README.md docs/agent_factory/README.md` | PASS, exit 0. |
| `sed -n '1,260p' handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P23.md` | PASS, exit 0. |
| `sed -n '1250,1625p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` | PASS, exit 0. |
| `sed -n '1760,1872p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` | PASS, exit 0. |
| `sed -n '1954,1990p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` | PASS, exit 0. |
| `sed -n '316,342p' campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md` | PASS, exit 0. |
| `sed -n '856,894p' campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md` | PASS, exit 0. |
| `rg -n "frontier-run-parallel-mock\|frontier-plan" justfile tools/frontier` | PASS, exit 0. |
| `sed -n '1,120p' docs/agent_factory/README.md` | PASS, exit 0. |
| `find docs/agent_factory -maxdepth 2 -type f | sort` | PASS, exit 0. |
| `find reviews/ALPHA_AGENT_FACTORY_MVP -maxdepth 2 -type f | sort` | Non-blocking context read; review directory is absent in this worktree. |
| `sed -n '70,110p' justfile` | PASS, exit 0. |
| `sed -n '1,260p' docs/agent_factory/WORKFLOW2_DAG.md` | PASS, exit 0. |
| `sed -n '1,60p' README.md` | PASS, exit 0. |

## Artifact Audit Confirmation

- `git ls-files runs` returned empty output.
- No file under `runs/**` was created or edited by this executor.
- No run-local handoff was written.
- No review artifact or verdict artifact was created.
- Codex staged nothing, so Codex introduced no staged `runs/**` path and no
  staged forbidden data, DB, cache, log, or heavy-artifact path.
- The expected Ralph staging list above contains no `runs/**`, data, DB,
  cache, log, heavy artifact, review, verdict, code, test, scheduler, or
  consumed-primitive path.
- Ralph must perform the authoritative staged-set audit after explicit staging
  because the executor prompt forbade `git status`, `git diff`, and
  `git diff --cached --name-only`.

## README Snapshot Confirmation

`README.md` now has a compact post-P24 snapshot: `ALPHA_AGENT_FACTORY_MVP`,
`AGENT-P24` of 26 complete, active/next `AGENT-P25` Acceptance Audit and
Closeout, the new durable `docs/agent_factory/WORKFLOW2_DAG.md` document, the
read-only `just frontier-plan ALPHA_AGENT_FACTORY_MVP` preview command, the
no-merge `just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3` command,
and unchanged safety boundaries. It does not include generated run details,
local artifact paths, broker/live/paper/order/account behavior, deployment
behavior, or duplicated phase-handoff content.

## Caveats

- `git status --short` was skipped due the explicit executor prohibition.
- `just frontier-run-parallel-mock ALPHA_AGENT_FACTORY_MVP 3` was not run
  because this phase did not start a live parallel run and the generated spec
  required documenting it as the pre-live verification path.
- `campaign.yaml`'s generated phase table for `AGENT-P24` still includes a
  local-only `runs/**` path in that phase's `allowed_paths`; the executor
  prompt explicitly overrides commit-eligible staging to exclude `runs/**`, and
  edits to `campaign.yaml` were forbidden by this phase.
- Fresh YELLOW-lane Claude review and `verdict.json` remain required before
  merge. Codex did not call Claude, run reviewer, create `review.md`, create
  `verdict.json`, create a PR, merge, mark the phase PASS, stage, commit, or
  push.
