# Fast Path Limitations

ASV1-P19 fast path support is deliberately scoped. It accelerates only a small
bar-level subset and otherwise fails closed or routes to the reference engine.

## Unsupported Or Fallback Matrix

| Feature | ASV1-P19 behavior | Grid fast-path use |
| --- | --- | --- |
| slippage model with non-zero slippage | reference fallback | blocked |
| liquidity policy semantics | reference fallback | blocked |
| laddered partial exits | reference fallback | blocked |
| cooldown | reference fallback | blocked |
| max holding bars | reference fallback | blocked |
| management fixed stop or target R multiple | reference fallback | blocked |
| management EOD exit | reference fallback | blocked |
| ATR stop | reference fallback | blocked |
| volatility stop | reference fallback | blocked |
| breakeven stop | reference fallback | blocked |
| trailing stop | reference fallback | blocked |
| time exit | reference fallback | blocked |
| scale-in or scale-out | reference fallback | blocked |
| max trades per day | reference fallback | blocked |
| risk per trade or max position percent in management | reference fallback | blocked |
| signal desired exposure or portfolio target semantics | reference fallback | blocked |
| multi-instrument or multi-session runs | reference fallback | blocked |
| unknown future feature labels | fail closed | blocked |

Reference fallback is explicit. It is not an approximation and it is not an
accelerated certification.

## Optional Array Dependencies

`fast_arrays.py` uses NumPy and Numba when they are installed. The current
repository dependency contract does not require them and ASV1-P19 is not allowed
to edit dependency metadata, so the module also has a deterministic pure-Python
array fallback. The fallback exists only to keep local parity tests runnable in
the current environment.

## Same-Bar Ambiguity

Same-bar stop/target ambiguity follows the reference adverse-first rule. If a
stop and target are both touched in the same 1-minute bar, the stop is selected.
The fast path must not choose a favorable target to improve PnL.

## Artifact Policy

The fast path and parity checker do not write:

- benchmark logs,
- `.npy` or `.npz` arrays,
- Parquet, Arrow, or Feather files,
- SQLite or DB files,
- full trade logs or equity logs,
- raw data,
- grid outputs,
- model binaries,
- repository-local caches or local-only run artifacts.

`runs/**` remains local-only and must never be staged or committed.

## Scope Boundaries

The fast path is research simulation acceleration only. It is not a broker
adapter, paper-trading adapter, order router, live-trading system, production
execution system, or a second PnL truth. No alpha, profitability, robustness, or
tradability claim is introduced by the parity fixtures.
