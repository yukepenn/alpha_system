# Known Limitations

## Validation Scope

- v0.1 validation is fixture-only correctness validation.
- No real market dataset, long historical backtest, market regime study,
  benchmark, scalability proof, or production operational test is included.
- Fixture results must not be interpreted as alpha, profitability, robustness,
  or tradability evidence.

## Research Boundaries

- Candidate promotion requires review metadata and remains separate from report
  recommendations.
- Draft factors are not materialized to long-term stores by default.
- ML is an MVP for factor-combination experiments with leakage controls; it is
  not a model-selection or deployment workflow.
- Grid and management-grid outputs are bounded research diagnostics, not
  approval artifacts.

## Execution Boundaries

- The Tier 1 reference 1-minute engine is the single canonical PnL truth.
- Fast path is acceleration-only and usable only where parity is proven for the
  selected feature set.
- Same-bar and bar-level execution ambiguity remains conservatively modeled;
  event-driven and L2 replay validation is future work.
- Costs and slippage are explicit research assumptions; they do not represent
  venue-specific execution guarantees.

## Artifact And Operations Boundaries

- SQLite registries are local-only and must not be committed.
- Raw data, canonical generated data, generated factors, labels, signals, review
  bundles, grid outputs, trade logs, equity curves, model artifacts, caches, and
  logs remain local-only.
- L2 work is schema/skeleton/design/fixture-only. There is no replay engine,
  queue model, passive-fill model, broker adapter, paper-trading adapter, live
  trading adapter, order router, or deployment path in v0.1.
- Ralph still owns formal validation recording, review routing, verdict
  parsing, semantic done-check, PR, CI, and merge gates.
