# Feature/Label Synthetic Fixtures

Tiny deterministic fixtures for FLF-P25 no-lookahead and fail-closed tests.

These rows are fabricated examples only. They are not real market data, are not
provider responses, and are not evidence about alpha, tradability, profitability,
or production readiness.

The fixture set includes:

- canonical OHLCV rows with explicit `available_ts`;
- canonical BBO rows with valid, `missing_bbo`, and `bbo_quarantined` cases;
- dense-grid OHLCV rows with one real trade row and one synthetic `no_trade`
  previous-close row;
- minimal locked-partition governance metadata used only to exercise
  fail-closed partition checks.

