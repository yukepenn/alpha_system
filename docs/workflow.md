# Workflow

## Workflow 1

Human-gated phase loop:

```text
strategy -> spec -> human approval -> Codex execution -> handoff -> Claude review -> human merge or repair
```

## Workflow 2

Provider-wired campaign loop:

```text
campaign -> phase selection -> Claude spec -> Codex execution -> validation -> Claude review -> Codex repair loop -> semantic done-check -> commit/push -> PR -> CI wait -> merge gate -> lane auto-merge -> next phase -> campaign done-check -> RUN_SUMMARY
```

Supported commands:

```bash
just frontier-run-campaign <campaign>
just frontier-run-next <campaign>
just frontier-run-campaign-mock <campaign>
just frontier-run-next-mock <campaign>
just frontier-run-campaign-ledger <campaign>
just frontier-run-overnight <campaign>
just frontier-resume <run_id>
just frontier-tail <run_id>
just frontier-summary <run_id>
just frontier-stop <run_id>
just frontier-heartbeat <run_id>
just frontier-acceptance
```

## Modes

- Mock mode sets `FRONTIER_MOCK_PROVIDERS=1`; it writes deterministic artifacts and never calls Claude or Codex CLIs.
- Provider-wired local mode uses `claude -p` and `codex exec --sandbox workspace-write`.
- Worktree mode uses `FRONTIER_WORKTREE_MODE=1` or `--worktree-mode` to create `auto/<campaign>/<phase>-<slug>` branches in Frontier-owned worktrees.
- GitHub PR/CI mode uses `gh` for PR creation, CI polling, branch protection inspection, and merge.
- Real auto-merge is enabled only by `frontier.yaml` lane policy plus passing CI, verdicts, artifact policy, branch protection, and authenticated `gh`.

## Stop Conditions

- `STOP` file before a phase, provider call, done-check, PR, CI, or merge action.
- `BLOCKED` verdict or done-check.
- Repair attempts exhausted.
- CI failure or timeout when CI is required.
- Branch protection missing or mismatched for real merge.
- Merge gate block.
- Run, phase, or estimated-cost budget stop.

`just frontier-stop <run_id>` writes `runs/<run_id>/STOP`. Resume with `just frontier-resume <run_id>` after removing or resolving the STOP condition.
