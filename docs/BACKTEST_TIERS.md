# Backtest Tiers

## Truth Model

There must never be two conflicting PnL truths. For v1, Tier 1 is the single
canonical PnL truth. Other tiers either support research diagnostics,
acceleration, or future design-readiness.

## Tier 0 - Factor Research Engine

Tier 0 supports factor diagnostics, labels, studies, and exploratory research.
It does not run full trade simulation and makes no tradability claims.

## Tier 1 - Reference 1-Minute Bar Execution Truth

Tier 1 is the Reference 1-minute bar execution truth. It is conservative,
deterministic, point-in-time, and canonical for v1 PnL.

The Reference engine owns accounting semantics, fill assumptions, cost
handling, exit ordering, and same-bar ambiguity defaults for v1. It must use
completed bars only after `bar_end_ts` plus configured latency. Signals on bar
`t` do not execute inside bar `t` by default.

## Tier 2 - Fast Path Parity

Tier 2 is the Fast path. It may use NumPy and Numba for speed, but it is
acceleration only. It must match the Tier 1 Reference engine on deterministic
fixtures before use.

Tier 2 is never a second PnL truth. If parity fails, the Reference engine wins.

## Tier 3 - Event-Driven Execution Truth Engine

Tier 3 is future design-readiness only. It is not implemented in v1. It must
not be described as complete execution validation for this campaign.

## Tier 4 - Future L2/L3 Replay Engine

Tier 4 is future L2/L3 replay design only. V1 does not implement L2 replay,
queue modeling, passive fills, or real L2 ingestion.

## Grid Usage

Grids may use acceleration only after parity. Finalist validation must return
to the Reference truth model. Grid results must remain bounded, versioned, and
reported with limitations.
