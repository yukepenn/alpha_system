# Strategy Boundaries

Strategy code owns signal intent. It does not own accounting, execution, or
portfolio state.

## Allowed In StrategySpec

`StrategySpec` may declare:

- entry signal
- exit signal
- direction
- optional confidence score
- optional desired exposure
- required factor dependencies
- deterministic research-template parameters
- provenance metadata

Desired exposure is an intent field for later layers to interpret. It is not
position sizing, allocation, account equity logic, or order construction.

## Forbidden In StrategySpec

`StrategySpec` must not include:

- account equity
- position sizing
- fills
- order lifecycle
- slippage
- commission
- partial take-profit accounting
- portfolio aggregation

Management, portfolio, reference backtest, and execution layers own those
responsibilities in later phases.

## Input Boundary

Strategies may consume only factor value records for declared factor
dependencies. A factor dependency must name a factor id, factor version, and
strategy input name.

The validator rejects:

- labels as dependencies or input fields
- undeclared factor ids
- mismatched factor versions
- raw ad hoc columns outside the factor value schema

## Timing Boundary

A signal cannot be available before any factor value it depends on. Signal
validation checks the signal `available_ts` against all declared input factor
`available_ts` values.

## Artifact Boundary

Signal store outputs are local-only generated artifacts. They are not committed
and are not evidence of a profitable, tradable, robust, production-ready, or
live-ready strategy.
