# Workflow

Document how work moves from campaign planning through implementation, review, and handoff.

## Workflow 1

Human-gated phase loop:

```text
strategy -> spec -> human approval -> Codex execution -> handoff -> Claude review -> human merge or repair
```

## Workflow 2

Ralph strict autonomous campaign loop scaffold:

```text
campaign -> phase spec -> execute -> checks -> handoff -> review -> repair or merge gate -> done-check -> next phase
```

The generic Workflow 2 MVP includes:

- `just frontier-run-campaign <campaign_id>` for provider-wired campaign-loop mode.
- `FRONTIER_MAX_PHASES=1 just frontier-run-campaign <campaign_id>` or `just frontier-run-next <campaign_id>` for one-phase smoke/debug mode.
- `just frontier-run-campaign-mock <campaign_id>` and `just frontier-run-next-mock <campaign_id>` for deterministic mock-provider runs.
- `just frontier-run-campaign-ledger <campaign_id>` for ledger-only state and artifacts with no phase execution.

The conductor never performs GitHub operations, PR creation, auto-merge, deployment, live trading, paper trading, or broker actions. Provider calls are only attempted outside mock mode, and mock mode remains the recommended bootstrap validation path.
