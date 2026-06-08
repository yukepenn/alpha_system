# Feature Compute Fast Path Fixtures

These rows are tiny synthetic OHLCV inputs for fast-path parity tests. They are
not real market data, not canonical production data, and not alpha evidence.

The fixture intentionally includes one `no_trade` row so the reference-parity
harness exercises both `insufficient_window` and `input_gap` quality flags.

- `canonical_ohlcv_rows.json` is the four-row `FCFP-P01` materializer-core
  fixture.
- `base_ohlcv.py` generates the 32-row `FCFP-P02` Base OHLCV pack fixture. It
  includes enough rows to exercise `window=20` rolling gaps, no-trade gap
  propagation, and post-gap recovery without storing any real values.
- `session_calendar_roll.py` generates the dense-grid `FCFP-P03` Session /
  Calendar / Roll pack fixture. It covers RTH/ETH labels, pre-open and
  post-close RTH-clock edges, a contract-roll transition, a synthetic no-trade
  position-only row, and absent optional metadata flags.
- `vwap_session_auction.py` generates the `FCFP-P04` VWAP / session-auction
  fixture. It covers contiguous session resets, anchored VWAP activation,
  opening-window boundaries, ETH-to-RTH overnight carry, leading no-trade,
  zero-volume, before-anchor, and zero-VWAP gap cases. It includes one
  synthetic zero-price edge row solely to exercise the reference `zero_vwap`
  branch; it is not production canonical data or alpha evidence.
- `regime_vol_compression.py` generates the `FCFP-P05` regime / volatility /
  compression fixture. It covers two session segments, reset-on-session warm-up,
  a no-trade input gap, flat-close `zero_movement` trendiness gaps, ATR rolling
  mean parity, and exclusive prior-window range-contraction behavior.
- `bbo_tradability.py` generates the `FCFP-P08` BBO tradability / top-book
  fixture. It covers leading rolling warm-up, missing and quarantined BBO rows,
  wide-spread and low-depth flags, session-reset z-score behavior, and a
  missing spread-ticks gap without storing real market data or feature values.
- `cross_market.py` generates the `FCFP-P09` ES/NQ/RTY Cross-Market fixture. It
  covers strict same-event alignment, delayed instrument availability,
  exact-time missing BBO flags, a missing RTY event that must not be imputed,
  no-trade and session-reset return gaps, and rolling variance gap branches.
- `fixed_horizon_label.py` generates the `FCFP-P10` fixed-horizon label fixture.
  It covers every governed close and midprice fixed-horizon label, exact
  terminal-row exclusion, no-trade roll/maintenance quality flags, missing and
  quarantined BBO rows, and value-free N_eff / horizon-overlap metadata.
