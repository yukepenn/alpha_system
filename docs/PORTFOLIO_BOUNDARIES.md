# Portfolio Boundaries

The platform boundary remains:

- Signal is not strategy.
- Strategy is not portfolio.
- Portfolio is not execution.
- Backtest is not live trading.

## Responsibilities

Strategies produce signal intent: entry, exit, direction, optional confidence,
and optional desired exposure. They do not size positions or manage capital.

Management owns post-entry exits and adjustments such as stops, targets,
partials, trailing logic, cooldowns, and end-of-day exits. It does not allocate
capital across instruments.

Portfolio owns target sizing and exposure constraints. It may convert a signal
into a target notional or quantity, enforce capital availability, cap position
percent, cap gross exposure, cap net exposure, and represent multi-symbol
constraints.

The reference backtest engine owns fills, slippage, commission, trade journal
records, equity, and accounting. Portfolio code must not replace those
semantics.

## Prohibited Scope

This phase introduces no broker account sync, no live portfolio state, no paper
trading, no order routing, no production execution adapters, no optimizer, and
no alpha, profitability, tradability, or production-readiness claims.

Any portfolio integration with the reference engine must pass target quantities
or metadata into the reference path and let that engine remain the execution and
accounting authority.
