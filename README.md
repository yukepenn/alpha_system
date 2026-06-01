# alpha_system

This repository uses Frontier Harness `0.3.0-rc1` with profile `trading_research`.

## Start

```bash
python tools/verify.py --smoke
python tools/frontier/bootstrap.py doctor
just frontier-run-next-mock G005_WORKFLOW2_TOY
```

## Workflow2 Commands

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

Mock one-phase:

```bash
FRONTIER_MOCK_PROVIDERS=1 FRONTIER_MAX_PHASES=1 just frontier-run-campaign G005_WORKFLOW2_TOY
```

Provider-wired one-phase:

```bash
FRONTIER_MAX_PHASES=1 just frontier-run-campaign G005_WORKFLOW2_TOY
```

Overnight:

```bash
just frontier-run-overnight G005_WORKFLOW2_TOY
```

## Modes

- Mock mode sets `FRONTIER_MOCK_PROVIDERS=1` and never calls Claude or Codex CLIs.
- Provider-wired local mode uses `claude -p` and `codex exec --sandbox workspace-write`.
- Worktree mode uses `FRONTIER_WORKTREE_MODE=1` or `--worktree-mode` to execute phase branches in Frontier-owned worktrees.
- GitHub PR/CI mode uses authenticated `gh` for PR creation, CI polling, branch protection inspection, and merge.
- Real auto-merge is controlled by `frontier.yaml` lane policy and requires CI success, passing verdicts, artifact policy success, branch protection validation, and `gh` auth. Red lane also requires `FRONTIER_RED_AUTHORIZED=1`.

## Required Local Auth

```bash
gh auth status
claude -p "ping"
codex exec --sandbox workspace-write "ping"
```

## Safety Defaults

- STOP files stop before expensive/provider/merge actions and before the next phase.
- BLOCKED, repair exhaustion, and CI failure stop the campaign unless policy explicitly allows the condition.
- No live trading, paper trading, broker operations, production deployment, destructive cleanup, or secrets handling is included.

Project work should stay in campaigns, specs, handoffs, reviews, decisions, source, configs, and tests. Generic harness behavior belongs under the generated harness files; project-specific behavior belongs in `frontier.yaml`, campaign files, project skill files, profile config, source, configs, and project tests.
