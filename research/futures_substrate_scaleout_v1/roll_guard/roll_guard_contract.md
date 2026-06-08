# Roll Guard Contract Summary

This value-free summary records the `FUTSUB-P03` roll-splice guard contract. It
contains no market rows, prices, volumes, feature values, label values,
provider responses, SQLite content, or persisted roll-calendar data.

## Identifiers

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P03`
- Roll policy id: `roll_cme_index_futures_quarterly`
- Roll guard version: `roll_guard_v1`
- Default cross-roll policy: `drop`
- Missing or ambiguous calendar policy: `drop`

## Calendar Contract

The approximate calendar is computed for `ES`, `NQ`, and `RTY` using:

- quarterly cycle months: March, June, September, December;
- expiration rule: third Friday;
- roll offset: 8 calendar days before expiration;
- method: `calendar_days_before_expiration`;
- validation status: `unvalidated`.

The calendar is analytic and approximate. It is not reconciled to provider
splice metadata and is not provider-exact splice truth. Persisted
`RollCalendarRecord` data remains local-only under `$ALPHA_DATA_ROOT` or
`runs/**`.

## Guard Contract

`alpha_system.labels.roll_guard.evaluate_roll_guard` evaluates a forward label
window `[entry_ts, label_horizon_ts]` and returns a deterministic verdict:

- `drop`: remove a cross-roll window;
- `truncate`: shorten the effective horizon to the roll boundary when possible;
- `flag`: retain the original horizon with an explicit cross-roll flag;
- `invalid`: mark the window invalid.

Missing or ambiguous calendar coverage fails closed to `drop`, even if the
caller requested `flag` or another retaining mode.

## Roll-Window Split

`classify_roll_window`, `is_roll_window`, and `roll_window_label` expose the
roll-window split. Defaults are 2 days before the roll date and 1 day after the
roll date. Labels are `roll_window`, `non_roll_window`, or
`roll_window_unknown`.

## Downstream Use

The guard is ready for the label materialization phases `FUTSUB-P16` through
`FUTSUB-P20` and for the `FUTSUB-P21` guard audit. Those phases must record the
policy id, guard version, applied policy, and verdict metadata with guarded
label packs.
