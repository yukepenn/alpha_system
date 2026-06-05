# Transform / Window / Normalization Primitives

`alpha_system.features.primitives` is the shared deterministic primitive layer
for later feature and label families. It computes no alpha, materializes no
feature or label values, persists no registry rows, reads no raw provider files,
and makes no tradability, profitability, broker, paper, live, or production
claim.

## Live-Safe Surface

The package root exports only causal live-safe primitives. Inputs are
`PrimitivePoint` or `OHLCVPrimitiveBar` records with explicit timezone-aware
`available_ts`. Primitive outputs are `PrimitiveResult` records that retain the
output `available_ts`, the source availability timestamps, input count, session
label, and quality flags.

The live primitive dispatcher is selected by FLF-P06 contract objects:

- `TransformSpec` selects transforms such as identity, rolling mean, rolling
  standard deviation / volatility, rolling min / max / range, simple returns,
  and log returns.
- `WindowSpec` supplies the causal window shape and length. Live primitives
  require `anchor == "available_ts"`, `causality == "causal"`, and
  `offline_only == False`.
- `NormalizationSpec` selects identity, causal z-score, causal demeaning, or
  causal min-max scaling.

`build_live_primitive(...)`, `describe_live_primitive(...)`, and
`apply_live_primitive(...)` fail closed if a centered, future, offline-only, or
non-`available_ts` window is supplied.

## Causality Guarantees

All causal primitives order inputs by `available_ts`, with input order used only
as a deterministic tie-breaker for equal availability timestamps. A result at
timestamp `t` uses only source rows whose `available_ts <= t`.

Supported causal primitives include:

- trailing rolling mean, standard deviation / volatility, min, max, and range;
- trailing simple returns and log returns;
- causal true range and ATR-style trailing true-range aggregation;
- causal z-score, demeaning, and min-max scaling;
- session reset grouping and optional per-primitive reset behavior that prevents
  trailing windows from crossing RTH/ETH-style session boundaries.

Insufficient history produces an explicit gap result instead of borrowing later
rows. Undefined calculations, such as zero-denominator returns, non-positive
log returns, zero-variance z-scores, or zero-range min-max scaling, also surface
gap results with quality flags.

## Dense Grid And BBO Semantics

Primitive row adapters consume FLF-P04 semantics instead of redefining them.
Synthetic no-trade rows are not treated as trade bars. Missing or quarantined
BBO rows are not forward-filled, interpolated, or converted into replacement
quotes.

Where a row is flagged as `no_trade`, `missing_bbo`, or `bbo_quarantined`, the
adapter emits a primitive gap at that row's own `available_ts`. Downstream
rolling and normalization primitives propagate the gap rather than silently
skipping or imputing the value.

## Offline-Only Windows

Centered and future-looking helpers live only in
`alpha_system.features.primitives.offline`. They require FLF-P06 `WindowSpec`
objects that are explicitly marked `offline_only=True` and whose causality is
`centered` or `future`.

Those helpers may use source rows with availability timestamps later than the
output timestamp, so they are valid only for offline label and diagnostic work.
They are not exported from the package-root live surface and cannot be bound by
`build_live_primitive(...)` or live `FeatureSpec` contracts.

## Shared Usage

Later feature families and label families should call this package as the
single implementation layer for basic transforms, windows, and normalizations.
Feature code must use the package-root live-safe surface. Label or diagnostic
code that intentionally needs future data must use the explicit offline module
and must keep those values out of live feature contracts.
