# Data Fixtures

Fixtures in this directory are tiny, synthetic, deterministic correctness
fixtures. They are not raw market data, are not evidence about any venue or
instrument, and must not be used for performance, tradability, or robustness
claims.

`synthetic_1min_bars.csv` contains three canonical 1-minute bars for one
fabricated instrument/session. The prices, volume, timestamps, versions, and
quality flags were hand-authored for schema, validation, DuckDB, and Polars
tests only.

`synthetic_session_calendar.json` contains one synthetic session template and
four synthetic dated calendar records covering a normal session, a DST offset
transition, an early close, and a holiday. It is not an exchange-official
calendar, not a holiday-complete source, and not market data.

`synthetic_ibkr_raw_bars.csv` contains two provider-shaped synthetic raw bar rows
for parser correctness tests. The provider timestamp, contract reference, WAP,
and bar-count fields are hand-authored fixture values only; the file is not a
provider response and is not canonical market data.
