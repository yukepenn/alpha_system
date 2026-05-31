# Campaigns

Campaigns group related work into reviewable goals.

Create one directory per campaign:

```text
campaigns/<CAMPAIGN_ID>/
```

Each campaign must include:

- `GOAL.md`
- `PHASE_PLAN.md`
- `campaign.yaml`
- `ACCEPTANCE.md`
- `RISK_REGISTER.md`
- `RUNBOOK.md`

Do not put campaign plans in the repository root. Use `ACTIVE_CAMPAIGN.md` to point to the current campaign.

`G005_WORKFLOW2_TOY` is included as a deterministic local Workflow 2 readiness campaign. It creates local docs and run artifacts only; it does not call providers, GitHub, browser, network, merge, deployment, live trading, or paper trading systems.
