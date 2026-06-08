# FCFP-P03 Session / Calendar / Roll Parity

This value-free note records the synthetic parity coverage for the V1
`session_calendar_roll` fast pack. It contains no per-row feature values and no
real market data.

## Fixture Coverage

- Exact parity expected for all ten governed `SESSION_CALENDAR_ROLL` features.
- Covered cases: RTH and ETH labels, an RTH-to-ETH boundary, pre-open and
  post-close RTH-clock clamping, one contract-roll transition, absent later roll
  transitions, one synthetic no-trade position-only row, and absent optional
  expiration/status metadata.
- Compared fields: value, `entity_id`, `event_ts`, `available_ts`,
  `quality_flags`, gap rows, and `feature_version_id`.

## Tolerance

All P03 parity comparisons are exact. No floating-point tolerance is used.

## Metadata Deferral

The fast frame does not yet project present expiration/status metadata maps as
columns. `minutes_to_expiration` and `halt_status_flag` therefore cover the
reference absent-metadata path only: `None` values plus
`expiration_metadata_absent` or `status_metadata_absent` flags. Present-metadata
values remain with the reference oracle until a governed metadata projection is
introduced.
