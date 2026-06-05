# Dense Grid and BBO Semantics

`alpha_system.features.semantics` defines input-layer predicates for dense
1-minute research grids, synthetic no-trade rows, and BBO missingness. It is a
policy and selector layer only. It does not compute features, labels, alpha
evidence, materialized values, tradability, profitability, or production
readiness.

## Input Boundary

Semantics consume canonical objects that have already passed the sanctioned
Feature/Label entry path:

- sparse OHLCV rows exposed by `alpha_system.features.input_views.OHLCVInputRow`;
- BBO rows exposed by `alpha_system.features.input_views.BBOInputRow`;
- dense-grid rows reconstructed as `DenseGridBarRecord` through the FLF-P01
  consumption adapter.

The module does not accept raw-provider shaped mappings as a loading path, does
not open provider files, and does not introduce an alternate DatasetVersion
resolver. Unsupported row shapes fail closed with `DataFoundationValidationError`.

## Sparse OHLCV Truth vs. Dense Grid

Sparse OHLCV records are provider trade-truth. A missing minute in the sparse
truth means there was no provider trade bar for that minute.

Dense-grid rows may preserve a 1-minute research index, but no-trade rows are
synthetic placeholders. The canonical no-trade signature is:

- `has_trade == False`;
- `synthetic == True`;
- `fill_method == "previous_close"`;
- `volume == 0`;
- `quality_flags` contains `no_trade`;
- `provider_bar_ref is None`.

Rows with that signature are flagged by `is_synthetic_no_trade_bar(...)` and
returned by `select_synthetic_no_trade_bars(...)`. They are excluded by
`is_real_trade_bar(...)` and `select_real_trade_bars(...)`.

Real dense-grid trade rows must carry `has_trade == True`, `synthetic == False`,
no fill method, a `provider_bar_ref`, and no `no_trade` quality flag. Sparse
`OHLCVInputRow` values are treated as real trade bars unless they carry the
`no_trade` quality token.

## BBO Missingness and Quarantine

BBO missingness uses only these canonical quality-flag tokens:

- `missing_bbo`: missing or bad quote row;
- `bbo_quarantined`: crossed or abnormal quote row, non-blocking but surfaced.

The semantics module surfaces those flags through `has_missing_bbo(...)`,
`is_bbo_quarantined(...)`, `has_missing_or_abnormal_bbo(...)`, and
`select_missing_or_abnormal_bbo_rows(...)`.

Missing or quarantined rows are not silently forward-filled, interpolated, or
converted into replacement quotes. `select_valid_bbo_quotes(...)` returns only
unflagged rows whose stored quote invariants hold. It returns existing rows; it
does not synthesize bid, ask, mid, spread, or microprice values.

## BBO Invariants

Downstream callers can use `bbo_invariants_hold(...)` and
`is_valid_bbo_quote(...)` to check the row as stored. The checks preserve the
canonical BBO requirements:

- `mid == (bid + ask) / 2`;
- `spread == ask - bid`;
- `ask >= bid`;
- `available_ts >= bar_end_ts`;
- when `microprice` is present, bid and ask sizes must both be positive and
  `bid <= microprice <= ask`.

These checks do not repair rows. A missing row can still carry explicit zero
quote values for audit, but it remains flagged and is excluded from valid quote
selectors.

## Safety Boundary

This phase adds no raw provider access, external provider calls, broker, live,
paper, order-routing, account, strategy, backtest, portfolio, feature
materialization, label materialization, alpha search, or alpha/tradability/
profitability claim. Feature and label values remain local-only.
