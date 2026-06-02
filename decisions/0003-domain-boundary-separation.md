# ADR-0003: Domain Boundary Separation

## Status

Accepted for v1 design baseline.

## Context

Research workflows can become ambiguous when data, factors, signals,
strategies, portfolios, and execution are blended together. Ambiguous domain
ownership makes point-in-time validation and reproducibility difficult.

## Decision

The following domain statements are invariants:

- Data is not factor.
- Factor is not signal.
- Signal is not strategy.
- Strategy is not portfolio.
- Portfolio is not execution.
- Backtest is not live trading.
- Fast research simulation is not execution truth.
- Draft factor values are not automatically long-term stored.
- Only validated and reviewed factors may be materialized into the long-term
  factor store.

Every result must be reproducible through git commit, code hash, config hash,
data version, factor version, label version, engine version, and run manifest.

## Consequences

Later implementation must preserve explicit transitions between domains.
Reviewers can reject changes that merge domains or materialize drafts without
validation and review.
