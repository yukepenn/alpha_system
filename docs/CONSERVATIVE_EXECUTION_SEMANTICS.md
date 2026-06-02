# Conservative Execution Semantics

This repository models offline research execution only. It does not perform
live trading, paper trading, broker calls, order routing, deployment, or
production execution.

## Defaults

The non-test defaults are:

- `execution_timing: next_bar_conservative`;
- `same_bar_policy: adverse_first`;
- non-zero cost and non-zero slippage;
- explicit missing bid/ask behavior;
- volume participation controls available for conservative fill-model checks.

A signal generated from bar `t` cannot fill inside bar `t` by default. The
reference engine selects the first later eligible bar whose start time is not
before the signal was available.

## Same-Bar Stop And Target Ambiguity

When a stop and target are both reachable inside the same 1-minute OHLC bar,
the outcome resolves against the open position. Long and short positions both
choose the stop before the target when ordering cannot be known from the bar.
This prevents optimistic same-bar fills.

## Spread-Aware Fills

When bid/ask fields are present:

- long entries buy at ask;
- long exits sell at bid;
- short entries sell at bid;
- short exits buy at ask.

When bid/ask is missing, the explicit default policy is
`fallback_to_ohlc_with_warning`: use the configured OHLC fallback field and
surface a warning/provenance flag. This is documented fallback behavior, not a
silent quote assumption.

## Zero-Cost Fixture Policy

Zero cost and no slippage are allowed only for explicit synthetic fixture or
test configurations. Non-test defaults must never silently be zero-cost or
same-bar optimistic.

## Single Truth Boundary

The Tier 1 reference 1-minute engine remains the single PnL truth. These modules
add configurable cost, slippage, liquidity, fill-model, and metadata semantics;
they do not introduce a second accounting engine or fast path. Fast-path parity,
L2 replay, queue modeling, paper trading, live trading, and broker adapters are
out of scope.
