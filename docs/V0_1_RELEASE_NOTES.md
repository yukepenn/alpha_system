# v0.1 Release Notes

## Scope

`ALPHA_SYSTEM_V1` closes a local-first v0.1 foundation for an Alpha Research
Platform. The foundation is research-only and fixture-validated. It is not a
broker, paper-trading, live-trading, order-routing, deployment, or production
execution system.

## Included Foundation

- Frontier Workflow 2 campaign and artifact discipline.
- Core contracts, timestamp semantics, and no-lookahead policy.
- SQLite metadata registry with temp/local test coverage.
- Canonical 1-minute bar contracts, validation, build-bars CLI, calendar, and
  session assignment.
- Factor specification, lifecycle, validation, compute, diagnostics, factor
  card/report generation, and promotion boundaries.
- Label generation and alignment with `label_available_ts`.
- Signal and strategy contracts separated from portfolio, management, and
  execution truth.
- Tier 1 reference 1-minute backtest truth with conservative timing,
  same-bar ambiguity handling, and explicit costs/slippage.
- Management rules, portfolio target/sizing, fast-path parity, bounded grids,
  management grids, experiment registry hardening, ML MVP, multi-symbol fixture
  support, design-only L2 readiness, review bundles, source maps, audit reports,
  and onboarding docs.

## Added By ASV1-P29

- End-to-end fixture validation test:
  `tests/integration/test_end_to_end_v0_1.py`.
- Closeout documentation:
  `docs/V0_1_VALIDATION.md`, `docs/V0_1_RELEASE_NOTES.md`,
  `docs/KNOWN_LIMITATIONS.md`, `docs/NEXT_CAMPAIGN_CANDIDATES.md`, and
  `campaigns/ALPHA_SYSTEM_V1/CLOSEOUT.md`.
- Curated validation summaries under `evals/v0_1/`.
- Commit-eligible executor handoff: `handoffs/ALPHA_SYSTEM_V1/ASV1-P29.md`.

## Interpretation

The v0.1 validation uses deterministic fixtures to check platform correctness,
domain boundaries, reproducibility hooks, and artifact discipline. It does not
validate any real dataset, strategy edge, market behavior, alpha, profitability,
robustness, tradability, live readiness, paper-trading readiness, or deployment
readiness.
