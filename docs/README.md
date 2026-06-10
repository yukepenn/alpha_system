# Documentation Index

Durable documentation for `alpha_system`. **New here? Start with
[`AGENT_CONTEXT_MAP.md`](AGENT_CONTEXT_MAP.md)** — it orients you in a few minutes
and tells you which of the docs below you actually need. Do not read everything.

Docs are grouped by purpose below. Subdirectories: [`data_foundation/`](data_foundation/)
(incl. [`databento/`](data_foundation/databento/)), [`governance/`](governance/),
and [`_historical/`](_historical/) (superseded docs, kept for audit).

## Start here / guides
- [AGENT_CONTEXT_MAP.md](AGENT_CONTEXT_MAP.md) — single orientation page (read first).
- [SYSTEM_MAP.md](SYSTEM_MAP.md) — **generated** structure map (anchors, packages, commands); `just system-map` regenerates, CI fails on drift.
- [ONBOARDING.md](ONBOARDING.md) — local-first quickstart.
- [RESEARCHER_GUIDE.md](RESEARCHER_GUIDE.md) — human research workflow.
- [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) — Workflow-2 AI agent guide.
- [CLI_REFERENCE.md](CLI_REFERENCE.md) — current CLI surface (incl. a "Planned / Target CLI Surface" section).
- [EXAMPLE_WORKFLOWS.md](EXAMPLE_WORKFLOWS.md) · [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Feature/Label Foundation (next campaign)
- [FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md](FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md) — inputs, allowed canonical records, gates, and boundaries for `ALPHA_FEATURE_LABEL_FOUNDATION_V1`.

## Architecture & contracts
- [ARCHITECTURE.md](ARCHITECTURE.md) · [CONTRACTS.md](CONTRACTS.md) · [LOCAL_FIRST_STACK.md](LOCAL_FIRST_STACK.md)
- [DOMAIN_BOUNDARIES.md](DOMAIN_BOUNDARIES.md) · [INSTRUMENT_MASTER.md](INSTRUMENT_MASTER.md) · [METADATA_REGISTRY.md](METADATA_REGISTRY.md) · [SOURCE_MAPS.md](SOURCE_MAPS.md)

## Harness & process (Workflow 1 / Workflow 2)
- Workflow-2 driver contract: see [`../AGENTS.md`](../AGENTS.md) and [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) (state machine, roles, lanes, run artifacts).
- [GIT_AND_ARTIFACT_DISCIPLINE.md](GIT_AND_ARTIFACT_DISCIPLINE.md) · [ARTIFACT_POLICY.md](ARTIFACT_POLICY.md) · [STOP_AND_RESUME.md](STOP_AND_RESUME.md)
- Research workflow governance order: see [RESEARCHER_GUIDE.md](RESEARCHER_GUIDE.md) · [MANAGEMENT_GRID_WORKFLOW.md](MANAGEMENT_GRID_WORKFLOW.md)
- [automation_lanes.md](automation_lanes.md) · [campaign_authoring.md](campaign_authoring.md) · [model_routing.md](model_routing.md) · [operations.md](operations.md) · [validation.md](validation.md) · [workflow.md](workflow.md)
- See also [`harness/HARNESS_NOTES.md`](harness/HARNESS_NOTES.md) — harness maintainability backlog, and [`STRUCTURAL_BACKLOG.md`](STRUCTURAL_BACKLOG.md) — deferred data-layer / provider-boundary refactors.

## Domain layers
- [DATA_LAYER.md](DATA_LAYER.md)
- [FACTOR_CARDS.md](FACTOR_CARDS.md) · [FACTOR_COMPUTE.md](FACTOR_COMPUTE.md) · [FACTOR_DIAGNOSTICS.md](FACTOR_DIAGNOSTICS.md) · [FACTOR_REGISTRY.md](FACTOR_REGISTRY.md)
- [LABEL_STORE.md](LABEL_STORE.md) · [SIGNALS_AND_STRATEGIES.md](SIGNALS_AND_STRATEGIES.md) · [ML_LAYER.md](ML_LAYER.md) · [PORTFOLIO_LAYER.md](PORTFOLIO_LAYER.md)
- [EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md) · [GRID_ENGINE.md](GRID_ENGINE.md)

## Backtest & reference truth
- [REFERENCE_BACKTEST.md](REFERENCE_BACKTEST.md) · [BACKTEST_TIERS.md](BACKTEST_TIERS.md) · [BACKTEST_TRUTH_POLICY.md](BACKTEST_TRUTH_POLICY.md)
- [FAST_PATH_PARITY.md](FAST_PATH_PARITY.md) · [FAST_PATH_LIMITATIONS.md](FAST_PATH_LIMITATIONS.md)
- [COST_AND_SLIPPAGE.md](COST_AND_SLIPPAGE.md) · [CONSERVATIVE_EXECUTION_SEMANTICS.md](CONSERVATIVE_EXECUTION_SEMANTICS.md) · [POSITION_MANAGEMENT.md](POSITION_MANAGEMENT.md)

## Policies & guardrails
- [NO_LOOKAHEAD_POLICY.md](NO_LOOKAHEAD_POLICY.md) · [ML_LEAKAGE_POLICY.md](ML_LEAKAGE_POLICY.md)
- [GRID_OVERFIT_POLICY.md](GRID_OVERFIT_POLICY.md) · [MANAGEMENT_OVERFIT_POLICY.md](MANAGEMENT_OVERFIT_POLICY.md)
- [RESEARCH_INTERPRETATION_POLICY.md](RESEARCH_INTERPRETATION_POLICY.md) · [REPORT_LANGUAGE_POLICY.md](REPORT_LANGUAGE_POLICY.md)
- [FIXTURE_POLICY.md](FIXTURE_POLICY.md) · [SURVIVOR_POLICY.md](SURVIVOR_POLICY.md)
- [PORTFOLIO_BOUNDARIES.md](PORTFOLIO_BOUNDARIES.md) · [STRATEGY_BOUNDARIES.md](STRATEGY_BOUNDARIES.md)

## Calendar & universe
- [CALENDAR_AND_SESSIONS.md](CALENDAR_AND_SESSIONS.md) · [UNIVERSES_AND_MULTI_ASSET.md](UNIVERSES_AND_MULTI_ASSET.md)

## Reproducibility, audit & reports
- [REPRODUCIBILITY_PRINCIPLES.md](REPRODUCIBILITY_PRINCIPLES.md) · [REPRODUCIBILITY_AUDIT.md](REPRODUCIBILITY_AUDIT.md)
- [AUDIT_REPORTS.md](AUDIT_REPORTS.md) · [REVIEW_BUNDLES.md](REVIEW_BUNDLES.md) · [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)

## Planning & status
- [PLAN.md](PLAN.md) · [NEXT_CAMPAIGN_CANDIDATES.md](NEXT_CAMPAIGN_CANDIDATES.md) (historical candidate menu; decided next campaign is in `PROJECT_STATUS.md`).

## L2 (design-only — future, not implemented)
- [L2_READINESS.md](L2_READINESS.md) · [L2_DERIVED_FEATURES.md](L2_DERIVED_FEATURES.md) · [L2_FEATURE_SCOPE_POLICY.md](L2_FEATURE_SCOPE_POLICY.md) · [L2_SCOPE_BOUNDARIES.md](L2_SCOPE_BOUNDARIES.md) · [FUTURE_L2_REPLAY.md](FUTURE_L2_REPLAY.md)

## Release history
- [V0_1_RELEASE_NOTES.md](V0_1_RELEASE_NOTES.md) · [V0_1_VALIDATION.md](V0_1_VALIDATION.md) · [DATA_VALIDATION_CLI.md](DATA_VALIDATION_CLI.md)
