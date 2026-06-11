# Futures Research Substrate Scaleout Docs

`docs/futures_substrate_scaleout/` is the durable documentation root for
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

This tree indexes the substrate scaleout operator and research contracts as they
are added by Workflow 2 phases. The campaign bundle remains the source of truth
for phase order, scope, lane policy, artifact policy, and acceptance criteria:

- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/GOAL.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/PHASE_PLAN.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/campaign.yaml`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/ACCEPTANCE.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RISK_REGISTER.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RUNBOOK.md`

## Current Docs

- `README.md` - this index for the substrate scaleout docs tree.
- `OVERVIEW.md` - compact overview of mission, phase-map source, boundaries,
  and source-of-truth pointers.
- `WALK_FORWARD_WIRING.md` - P24 runtime wiring for purged / embargoed
  walk-forward diagnostics metadata and protocol hooks.

## Expected Additions

Later phases are expected to add focused docs for the reality lock, dataset
acceptance, roll guards, keystone identity, materialization planning, feature
and label integration, coverage matrices, N_eff reporting, BBO and cross-market
matrices, Core Pilot rerun evidence, downstream handoffs, artifact audit, and
closeout.

Each document in this tree should stay value-free, cite campaign or research
evidence artifacts by path when needed, and avoid broker, live, paper, order,
deployment, profitability, or tradability claims.
