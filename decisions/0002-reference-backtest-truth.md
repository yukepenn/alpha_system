# ADR-0002: Reference Backtest Truth

## Status

Accepted for v1 design baseline.

## Context

The platform must avoid execution truth ambiguity. Multiple engines that each
claim PnL truth would invalidate comparisons, grids, reports, and review.

## Decision

Tier 1, the Reference 1-minute bar execution truth, is the single canonical PnL
truth for v1. It must be conservative, deterministic, and point-in-time.

Tier 0 supports factor research and does not make full trade simulation or
tradability claims. Tier 2 Fast path work is acceleration only and must match
the Reference engine on deterministic fixtures. Tier 3 event-driven execution
truth and Tier 4 L2/L3 replay are future design-readiness only during this
campaign.

There must never be two conflicting PnL truths.

## Consequences

Reference behavior wins when any accelerated or future design path disagrees.
Fast path work cannot weaken Reference semantics. Event-driven and L2 design
cannot be treated as complete execution validation for v1.
