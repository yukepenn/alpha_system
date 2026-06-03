# Position Management

Position management is the reviewed post-entry rule layer for the reference
1-minute backtest path. Strategies declare entry and exit intent. Management
evaluates how an already-open position is protected or closed after entry.

The module supports fixed stops, ATR stops, volatility stops, R-multiple
targets, laddered partial take profit, breakeven updates, trailing updates,
time exits, end-of-day exits, max trades per day, cooldown, scale-in and
scale-out contract representation, max holding bars, risk per trade, and max
position percent fields.

## Rule Order

Rules are deterministic and ordered:

1. Session reset.
2. Entry trade limit.
3. Entry cooldown.
4. Active stop.
5. Full R-multiple target.
6. Laddered partials.
7. Max holding bars.
8. Time exit.
9. End-of-day exit.
10. Breakeven update for the next bar.
11. Trailing update for the next bar.

The active stop is evaluated before favorable exits. If a stop and target or
partial threshold are both touched within the same 1-minute bar, the adverse
stop exit wins. Breakeven and trailing updates are applied after exit
evaluation so the moved stop affects the next bar.

## Partial Exits

Laddered partial exits are emitted as visible trade-journal records with
`partial_take_profit:<label>` exit reasons. Entry cost is allocated
proportionally to each closed quantity, and remaining position quantity and
entry cost are updated deterministically before later exits.

## Boundaries

Management does not own account equity, strategy logic, portfolio allocation,
broker order state, paper trading, live trading, order routing, or production
execution behavior. It reuses the reference fill, cost, accounting, equity, and
trade-journal containers. The reference 1-minute engine path remains the PnL
truth for this repository.

No management config, report, or CLI output should be treated as evidence of
tradability or candidate approval.
