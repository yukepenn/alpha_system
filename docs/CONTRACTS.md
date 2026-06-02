# Core Contracts

ASV1-P04 defines schema primitives only. These contracts do not implement
persistence, registry writes, data ingestion, factor computation, label
generation, signal generation, strategy execution, backtest execution, order
routing, broker integration, paper trading, or live trading.

## Shared Timestamp Semantics

The platform separates source and availability timestamps:

- `event_ts`: source event time for a record.
- `bar_start_ts`: start time of a 1-minute bar.
- `bar_end_ts`: end time of a completed 1-minute bar.
- `receive_ts`: receipt time for future L2 records.
- `available_ts`: first time a data, factor, signal, or L2 record may be used.
- `label_available_ts`: first time a future-looking label may be used after its
  horizon has completed.

1-minute bars must retain `bar_start_ts`, `bar_end_ts`, `event_ts`, and
`available_ts` as distinct primitives. A completed bar may be consumed only at
or after `bar_end_ts` plus configured data latency. The default signal timing
contract is next-bar conservative, so a signal based on bar `t` does not execute
inside bar `t` by default.

## Data Contracts

`InstrumentMaster` uses `instrument_id` as the stable internal identity. Raw
`symbol` is descriptive metadata and is not the sole identity. Instrument fields
also include asset class, exchange, currency, timezone, tick and lot details,
multiplier, active dates, corporate-action policy, and metadata.

`TradingSession` records calendar and session identity, trading date, open and
close timestamps, holiday and half-day flags, session type, timezone, and
quality flags. Contracts do not assume one global timezone or session for all
instruments.

`OneMinuteBar` records instrument/session identity, bar index, bar start and end
timestamps, event and availability timestamps, OHLCV, VWAP, trade count, bid,
ask, spread, source version, data version, and quality flags.

`QuoteTradeReadiness` is a design-level readiness primitive for quote data,
trade prints, bid/ask spread, future executable labels, and future cost
modeling. It does not process quotes or trades.

## Factor And Label Contracts

`FactorSpec` defines versioned factor metadata, owner, declared input fields,
parameters, frequency, warmup bars, session reset behavior, availability lag,
factor type, evaluation type, code/config hashes, lifecycle status, creation
time, and validation artifact reference.

Factor lifecycle values are exactly:

```text
draft
candidate
validated
approved
deprecated
```

Draft factors do not default to long-term materialization. Factor input domains
exclude labels at the contract level; later phases may add enforcement logic.

`FactorValue` carries factor and factor-version identity, instrument identity,
event and availability timestamps, session and bar identity, raw and normalized
values, quality flags, data version, and compute version.

`LabelSchema` represents future-looking research labels. It includes label and
instrument identity, event timestamp, horizon, label type, value, path metadata,
data version, and `label_available_ts`. Labels are separate from factor inputs,
signals, strategies, portfolio decisions, and execution.

## Signal And Strategy Boundaries

`SignalRecord` carries timestamped signal outputs with factor-version
references. It includes entry and exit booleans, direction, optional confidence
score, optional desired exposure, data version, and quality flags.

`StrategySpec` may declare entry signal, exit signal, direction, optional
confidence score, optional desired exposure, parameters, metadata, and required
factor dependencies.

`StrategySpec` does not own account equity, position sizing, fills, order
lifecycle, slippage, commission, partial take-profit accounting, or portfolio
aggregation.

## Management And Portfolio Boundaries

`ManagementSpec` owns position-management support fields: fixed stop, ATR stop,
volatility stop, target R multiple, laddered partial take profit, breakeven
stop, trailing stop, time exit, EOD exit, max trades per day, cooldown,
scale-in, scale-out, max holding bars, risk per trade, and max position percent.

`PortfolioSpec` owns portfolio target representation, position sizing, capital
allocation, risk limits, multi-symbol constraints, max gross exposure, max net
exposure, future sector/asset constraints, future correlation-aware allocation,
and signal-to-target conversion.

## Backtest And Experiment Contracts

`BacktestSpec` and `ExperimentSpec` are reproducibility primitives only. They
carry run identifiers, code/config hashes, data version, factor versions, label
versions, engine version, parameters, artifact paths, decision status, and
creation timestamp. They do not execute runs and do not persist registry state.

## Level-2 Design Contracts

The L2 module is design-only in this phase. `BookLevel`, `L2Snapshot`, and
`L2EventDelta` represent book level, side, price, size, optional order count,
`event_ts`, `receive_ts`, `available_ts`, data version, and quality flags.

The phase introduces no L2 replay engine, queue model, passive-fill logic, or
real L2 ingestion.
