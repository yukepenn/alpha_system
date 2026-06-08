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
