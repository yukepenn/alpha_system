# Research Runtime Documentation

This directory is the durable documentation root for
`ALPHA_RESEARCH_RUNTIME_MVP`, the Workflow 2 campaign that builds the local
research-runtime layer over the completed Feature/Label substrate.

The campaign turns an approved `AlphaSpec` plus `StudySpec` into a bounded,
reproducible research run that can resolve accepted DatasetVersions and
registered Feature/Label packs, run diagnostics, apply cost stress, evaluate a
bounded probe, assemble descriptive evidence, and record rejection,
inconclusive, or blocked outcomes. It does this by orchestrating existing
governance, research, experiments, backtest, data, feature, and label
primitives. It does not re-implement those primitives.

## Campaign Map

The source-of-truth contract bundle is:

- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/GOAL.md`
- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md`
- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`
- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md`
- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RISK_REGISTER.md`
- `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RUNBOOK.md`

The repository-level `ACTIVE_CAMPAIGN.md` points at this campaign. In DAG-wave
parallel mode that pointer is coordinator-owned; phase branches read it but do
not update it. There is no campaign-local `ACTIVE_CAMPAIGN.md` under
`campaigns/ALPHA_RESEARCH_RUNTIME_MVP/`.

RT-P00 creates this documentation root. Later phases add the runtime entry
contract, package skeleton, input resolver, run contracts, diagnostics, cost
stress, bounded-grid guards, no-lookahead audit, evidence draft, reference
handoff, CLI/tool contracts, reports, workflow integration, and closeout docs.

## Current Root Files

- `README.md` explains what this documentation root is and how it maps to the
  campaign control surface.
- `OVERVIEW.md` summarizes the mission, tier model, runtime decision lifecycle,
  and load-bearing campaign boundaries.

## Boundaries

Research Runtime is not Agent Factory, alpha search, a FactorLibrary, Strategy
Reference Validation, a Portfolio AlphaBook, or paper/live/broker execution. A
diagnostic PASS is not alpha validation; a signal probe is not a strategy
candidate; a bounded grid is not promotion; an `EvidenceDraft` is not a
candidate; a `ReferenceCandidateHandoff` is not Reference validation; the fast
path is not Reference truth.

The runtime consumes accepted DatasetVersions only through the sanctioned
DatasetVersion boundary and the registered FeatureStore/LabelStore. It must not
read raw provider files, call Databento or IBKR, commit raw/canonical/feature/
label/runtime values, commit local DBs or heavy artifacts, or introduce broker,
live, paper, order, account, strategy, backtest, portfolio, alpha-search,
tradability, profitability, or production scope.
