# Strategy-Agnostic Event Label Family

FLF-P20 adds the additive event label family under
`alpha_system.labels.families.event`. The family produces in-memory
`LabelValueRecord` objects for:

- `breakout_success`
- `return_to_vwap`
- `sweep_outcome`
- `liquidity_quality_future`

Every definition is built from a governed `LabelSpec` (`lspec_`) through the
FLF-P16 `LabelContractSpec.from_label_spec` contract surface. The family
consumes governed horizon, path rules, target/stop rules, cost-model metadata,
availability time, forbidden feature overlap, and leakage checks; it does not
duplicate those governance contracts.

## Inputs

Event anchors and OHLCV path outcomes consume canonical OHLCV input rows from
accepted DatasetVersion views. The implementation applies
`alpha_system.features.semantics.is_real_trade_bar` before event or outcome
evaluation, so dense-grid synthetic no-trade rows are not event anchors and are
not counted as future trade bars.

`liquidity_quality_future` also consumes canonical BBO input rows. Future BBO
rows must be exact timestamp rows. Rows carrying `missing_bbo` or
`bbo_quarantined`, invariant violations, or absent future BBO timestamps produce
gap labels with quality flags; the family does not forward-fill or interpolate
quotes.

## Label Semantics

`breakout_success` records whether a governed up/down event reaches the
specified success threshold before its failure threshold, or remains unresolved
through the governed horizon.

`return_to_vwap` records whether the future trade path returns to the governed
VWAP reference price within the configured tolerance before the horizon.

`sweep_outcome` records a neutral sweep result of `continuation`, `reversal`,
or `unresolved` based on governed continuation and reversal thresholds.

`liquidity_quality_future` records whether the future mean BBO spread is within
the governed spread threshold. Missing or abnormal BBO rows produce a null
value with explicit quality flags rather than a filled value.

## Availability

Each emitted record carries `label_available_ts`. For OHLCV event outcomes,
availability is derived from the row where the outcome is known:

`max(resolution event_ts, resolution available_ts, LabelSpec.availability_time)`.

For future liquidity quality labels, availability is derived from the governed
horizon and the future BBO rows used to assess the outcome:

`max(horizon_end_ts, future BBO available_ts values, LabelSpec.availability_time)`.

No label value is emitted without a `label_available_ts`, and no value is usable
before the outcome is known.

## Boundaries

The family is strategy-agnostic: horizon, direction, sweep side, VWAP
reference, continuation/reversal thresholds, and BBO spread thresholds are
parameters in the governed `LabelSpec`, not a named strategy, backtest, or
portfolio wrapper. Forward-looking data is label-only and is rejected as a live
feature input by the governed leakage checks.

The implementation adds no provider calls, raw data reads, value
materialization, feature exposure, broker/live/paper/order/account behavior, or
strategy/backtest/portfolio scope. It makes no alpha, profitability,
tradability, approval, production-readiness, paper-trading, live-trading, or
broker-readiness claim.
