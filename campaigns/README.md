# Campaigns

Campaigns group related work into reviewable goals. Each is a directory
`campaigns/<CAMPAIGN_ID>/` containing `GOAL.md`, `PHASE_PLAN.md`, `campaign.yaml`,
`ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md` (and a `CLOSEOUT.md` once done).

## Index

| Campaign | Status | Notes |
| --- | --- | --- |
| `ALPHA_SYSTEM_V1` | Complete (`COMPLETE_WITH_WARNINGS`) | Fixture-only foundation; phases ASV1-P00…P29. |
| `ALPHA_RESEARCH_GOVERNANCE_MVP` | Complete (`COMPLETE_WITH_WARNINGS`) | Spec/gate/ledger governance; phases ARGOV-P00…P19. |
| `ALPHA_DATA_FOUNDATION_V1` | Complete (`COMPLETE_WITH_WARNINGS`, 25/25) | Read-only quality-gated data foundation; phases DATA-P00…P24. Post-closeout: IBKR + Databento providers (see `PROJECT_STATUS.md`). |
| `G005_WORKFLOW2_TOY` | Local readiness fixture | Deterministic Workflow-2 test; local docs/runs only. |
| `000-template` | Template | Starter campaign bundle. |

`ASV1_RELEASE_HYGIENE` was a post-closeout cleanup pass with no campaign
directory (see `handoffs/ASV1-HYGIENE.md`). The **decided next campaign** is
`ALPHA_FEATURE_LABEL_FOUNDATION_V1` (not yet authored).

Use `ACTIVE_CAMPAIGN.md` to point to the current campaign; do not put campaign
plans in the repository root.

`G005_WORKFLOW2_TOY` is a deterministic local Workflow 2 readiness campaign. It
creates local docs and run artifacts only; it does not call providers, GitHub,
browser, network, merge, deployment, live trading, or paper trading systems.
