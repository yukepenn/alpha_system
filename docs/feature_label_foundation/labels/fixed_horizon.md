# Fixed-Horizon Forward Labels

`alpha_system.labels.families.fixed_horizon` defines the FLF-P17 fixed-horizon
label family. It is substrate code for governed label definitions and
in-memory fixture calculations only. It does not materialize label values, read
raw provider files, call external providers, persist registries, expose labels
as live features, or make alpha, profitability, broker, paper, live, or
production claims.

## Inputs And Contracts

Each definition is built with `build_fixed_horizon_label_definition(...)` from a
validated governance `LabelSpec` with an `lspec_` id. The family consumes the
FLF-P16 `LabelContractSpec`, `LabelInputSpec`, future offline `WindowSpec`,
`LabelVersion`, and `LabelValueRecord` contracts. Missing, malformed,
horizon-mismatched, or family-mismatched `LabelSpec` inputs fail closed before
a label version is derived.

Trade-price labels consume canonical OHLCV input-view rows and use the
canonical close field. Midprice labels consume canonical BBO input-view rows
and use the canonical `mid` field, whose upstream invariant is
`mid == (bid + ask) / 2`.

## Label Coverage

The family covers these trade-close forward-return labels:

- `fwd_ret_1m`
- `fwd_ret_3m`
- `fwd_ret_5m`
- `fwd_ret_10m`
- `fwd_ret_30m`

It also covers these midprice forward-return labels:

- `mid_fwd_ret_1m`
- `mid_fwd_ret_3m`
- `mid_fwd_ret_5m`
- `mid_fwd_ret_10m`
- `mid_fwd_ret_30m`

The calculation uses the exact terminal row at `source.event_ts + horizon`.
Rows without an exact terminal row are excluded rather than assigned fabricated
availability metadata.

## Availability

Every emitted `LabelValueRecord` carries:

- `event_ts` from the source row;
- `horizon_end_ts` from the terminal row;
- `label_available_ts` as the later of terminal-row `available_ts` and the
  governed `LabelSpec.availability_time`.

This keeps the label availability timestamp no earlier than the point at which
the outcome is known.

## No-Trade And BBO Missingness

Trade-close labels use FLF-P04 trade-bar semantics. Rows carrying the canonical
`no_trade` flag are gaps for trade-price forward returns. They are not treated
as source or terminal trade bars.

Midprice labels use FLF-P04 BBO semantics. Rows carrying `missing_bbo` or
`bbo_quarantined`, or rows whose BBO arithmetic invariants do not hold, are
reported as gap label rows with quality flags. They are not forward-filled,
interpolated, or replaced with neighboring quotes.

## Label-Only Boundary

The family records future windows as offline, labels-only windows. A label
definition delegates live-feature exclusion to the governance leakage guard via
`LabelContractSpec.validate_live_feature_references(...)`. A matching label id,
alias, transform, or lookahead availability reference is blocking.

`configs/labels/families/fixed_horizon/` contains only declarative family
metadata. It contains no provider data, materialized label rows, registry data,
or local artifacts.
