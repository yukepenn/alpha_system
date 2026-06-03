# Changelog

All notable changes to `alpha_system` are recorded here.

## 0.1.0 — ALPHA_SYSTEM_V1 foundation closeout

Status: executor-complete with warnings on deterministic fixtures.

### Added

- Local-first research harness with repository-native campaign, spec, review, handoff, and run
  contracts.
- Core contracts and timestamp semantics for point-in-time research workflows.
- Canonical 1-minute data contracts and deterministic fixture validation.
- Factor specification, registry, compute, diagnostics, and report surfaces.
- Label generation with explicit availability semantics.
- Signal and strategy contracts that keep research layers separated from execution simulation.
- Tier 1 reference 1-minute backtest truth with conservative timing and accounting semantics.
- Explicit cost and slippage semantics for reference-engine fixture validation.
- Management, portfolio sizing, bounded grids, ML MVP, and multi-symbol fixture coverage.
- Design-only L2 readiness schema.
- Review bundle and closeout artifacts for the ALPHA_SYSTEM_V1 foundation.

### Validation

- Fixture-only end-to-end validation through ASV1-P29.
- Executor recommendation: `COMPLETE_WITH_WARNINGS`.
- No market data validation was performed.
- No alpha, profitability, robustness, tradability, paper/live, broker, or deployment claim is
  made.

### Known warnings

- Formal validation, Claude review, semantic done-check, PR, CI, and merge gates remain separate
  from the executor recommendation.
- CLI/package smoke requires a clean local environment and package importability.
- Generated artifacts, local DBs, raw/canonical data, factor/label materializations, logs,
  caches, and run-local files remain local-only.

## Unreleased

- Post-closeout release hygiene: `ASV1_RELEASE_HYGIENE`.
- Next intended macro-campaign: `ALPHA_RESEARCH_GOVERNANCE_MVP`.
