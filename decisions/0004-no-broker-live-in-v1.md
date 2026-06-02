# ADR-0004: No Broker Or Live Trading In V1

## Status

Accepted for v1 design baseline.

## Context

The campaign is a research-only local platform foundation. Broker operations,
paper trading, live trading, and order routing would move the project into a
different risk lane and require additional authorization and controls.

## Decision

No broker integration, paper trading adapter, live trading path, real-time
order routing, production deployment, or execution operation is in v1 scope.

Backtest is not live trading. Research reports must not imply live readiness.

## Consequences

Any broker, paper, live, or order-routing file is scope creep for v1 unless a
future reviewed campaign explicitly authorizes it. The v1 architecture can
document research boundaries without implementing execution operations.
