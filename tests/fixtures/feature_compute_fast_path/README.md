# Feature Compute Fast Path Fixtures

These rows are tiny synthetic OHLCV inputs for `FCFP-P01` parity tests. They are
not real market data, not canonical production data, and not alpha evidence.

The fixture intentionally includes one `no_trade` row so the reference-parity
harness exercises both `insufficient_window` and `input_gap` quality flags.
