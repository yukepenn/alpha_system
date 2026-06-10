# LCFP-P05 Parity Coverage

This is value-free evidence for the LCFP-P05 synthetic path-label suite. It
contains no per-row label values, raw data, canonical data, registry output,
Parquet, SQLite, logs, or run-local artifacts.

## Families

- `mfe`
- `mae`
- `target_before_stop`
- `triple_barrier`

## Fixture Cases

- Target touched before stop.
- Stop touched before target.
- Same-bar target/stop ambiguity.
- Same-bar `target_first` and `stop_first` policy variants.
- Barrier-never-touched timeout.
- No-trade session-gap source row.
- Roll-crossing source row dropped by the P02 terminal guard.
- Maintenance-crossing source row dropped by the P02 terminal guard.

## Assertions

- Label value parity against the reference path family for kernelized scan
  cases.
- Exact `label_available_ts` parity.
- Exact `label_spec_id` and `label_version_id` parity.
- Exact event-set parity for reference-vs-fast path scan rows.
- Exact same-bar ambiguity and horizon-timeout quality flags.
- Exact P02 guard disposition for roll and maintenance crossing rows before
  value emission.

## Tolerance

Path value assertions use `abs=1e-12, rel=1e-12` because the reference path
family computes from `Decimal` input-view rows and the fast path consumes a
float shared panel. Timestamp, identity, event-set, same-bar quality flag,
horizon-timeout quality flag, and guard-disposition checks remain exact.
