# LCFP-P04 Parity Coverage

This is value-free evidence for the LCFP-P04 synthetic parity suite. It contains
no per-row label values, raw data, canonical data, registry output, Parquet,
SQLite, logs, or run-local artifacts.

## Families

- `session_close`
- `maintenance_flat`
- `cost_adjusted_fwd_ret`
- `spread_adjusted_fwd_ret`

## Fixture Cases

- Normal close-out rows.
- Post-session rows without a retained session-close terminal.
- Roll-crossing close-out rows dropped by the shared roll guard.
- Normal cost/spread-adjusted BBO rows.
- Cost/spread-adjusted windows crossing the daily maintenance break.
- Terminal BBO missingness rows.
- Entry BBO missingness rows.

## Assertions

- Label value parity against the reference families.
- Exact `label_available_ts` parity.
- Exact `label_spec_id` and `label_version_id` parity.
- Exact quality flag parity, including ordered cost-adjusted gap flags.
- Exact retained/missing event sets for close-out guard cases.

## Tolerance

Close-out labels use exact value comparison. Cost-adjusted labels use
`abs=1e-12, rel=1e-12` because the reference path computes from `Decimal`
input-view rows and the fast path consumes a Polars float panel before applying
the sanctioned `alpha_system.backtest.costs` primitives. Timestamp, identity,
event-set, and flag checks remain exact.
