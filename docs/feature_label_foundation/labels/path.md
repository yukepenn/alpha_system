# Path Label Family

FLF-P19 adds the path-dependent label family under
`alpha_system.labels.families.path`. The family produces in-memory
`LabelValueRecord` objects for:

- `mfe`
- `mae`
- `target_before_stop`
- `triple_barrier`

Every definition is built from a governed `LabelSpec` (`lspec_`) through the
FLF-P16 label contract surface. The family consumes `LabelHorizonSpec`,
`LabelPathSpec`, `BarrierSpec`, `target_stop_rules`, `path_rules`, and
`availability_time`; it does not duplicate those governance contracts.

## Inputs

The implementation reads canonical OHLCV input rows from accepted
DatasetVersion views. It does not read raw provider files or materialize label
values. Path evaluation is restricted to FLF-P04 trade-truth bars by using
`alpha_system.features.semantics.is_real_trade_bar`; dense-grid synthetic
no-trade rows are excluded from excursion and barrier calculations.

## Availability

`label_available_ts` is derived from the resolution row:

- MFE and MAE resolve at the terminal trade-truth bar for the governed horizon.
- Target/stop labels resolve at the first trade-truth bar where a target or stop
  barrier is known.
- Triple-barrier labels resolve at the first target/stop barrier or at the
  governed horizon when neither barrier is hit.

The emitted `label_available_ts` is
`max(resolution event time, resolution available_ts, LabelSpec.availability_time)`.
No label value is emitted without a `label_available_ts`.

## Boundaries

The family is strategy-agnostic: direction, horizon, target, stop, and same-bar
barrier policy are parameters in the `LabelSpec`, not a named strategy or
backtest wrapper. Forward path data is label-only and is rejected as a live
feature input by the governed label leakage checks. The implementation adds no
broker, live, paper, order-routing, portfolio, provider-call, or value-storage
surface and makes no alpha or trading-readiness claim.
