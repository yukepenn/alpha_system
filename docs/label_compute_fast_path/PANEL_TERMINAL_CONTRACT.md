# Shared Label Panel / Terminal Contract

LCFP-P02 adds the shared value-free contract surface in
`alpha_system.labels.fast`. Downstream label-pack phases consume this contract
before computing family-specific values.

## Public Surface

- `build_shared_label_panel(...)` constructs one immutable
  `SharedLabelPanel` per symbol-year from OHLCV rows plus optional BBO rows.
- `SharedLabelPanel` / `SharedLabelPanelRow` expose wide rows with trade
  price, high/low, BBO proxy columns, BBO presence flags, spread/cost inputs,
  session segment ids, ex-ante roll calendar records, and maintenance windows.
- `TerminalRequest`, `TerminalKind`, `resolve_terminal_indices(...)`, and
  `TerminalIndexModel` compute once-per-panel terminal indices for
  fixed-horizon, session-close, maintenance-flat, and roll-truncation modes.
- `TerminalResolution` records source index, terminal index, requested and
  effective terminal timestamps, guard disposition, guard reason, roll policy,
  and value-free quality flags.
- `derive_label_available_ts(...)` implements the per-family availability
  contract from `LabelAvailabilityPolicy`.
- `quality_metadata_for_resolution(...)` derives gap/missingness metadata from
  a terminal resolution without computing label values.

## Panel Contract

The panel is immutable to consumers and has one wide row per
`series_id + contract_id + event_ts` OHLCV row. BBO columns are aligned by the
same key when available. BBO is a proxy input only: every row carries
`bbo_present`, `bbo_missing`, `bbo_quarantined`, and
`bbo_invariant_violation` fields so downstream packs can fail closed or flag
missingness explicitly.

Panel metadata carries:

- `roll_policy_id = roll_cme_index_futures_quarterly`;
- `roll_guard_version = roll_guard_v1`;
- `maintenance_policy_id = cme_index_futures_daily_maintenance_break_v1`;
- `maintenance_guard_version = maintenance_crossing_guard_v1`.

The default roll calendar is the existing ex-ante analytic CME equity-index
quarterly calendar for supported roots. Missing or ambiguous roll coverage
continues to fail closed through `evaluate_roll_guard(...)`.

## Terminal Contract

Terminal lookup is exact by construction:

- fixed horizons use `series_id + contract_id + event_ts + horizon`;
- session close uses the last same-contract RTH row at or before 15:00
  America/Chicago for the CME trade date;
- maintenance flat uses the last same-contract row at or before 16:00
  America/Chicago for the CME trade date;
- roll truncation uses the existing roll guard effective horizon and requires
  an exact same-contract terminal row at that timestamp.

Maintenance crossing is evaluated before roll crossing, matching the reference
fixed-horizon family. Roll actions map directly to terminal dispositions:
`drop`, `truncate`, `flag`, and `invalid`. Truncate and flag retain value-free
roll-splice flags; drop and invalid retain no terminal index.

## Availability And Quality

`derive_label_available_ts(...)` mirrors
`LabelAvailabilityPolicy.from_label_spec(...)` by family:

- fixed horizon: max terminal row availability and governed availability floor;
- cost adjusted: max horizon end, governed floor, and terminal BBO availability
  when present;
- path: max resolution event time, resolution availability, and governed floor;
- event: max horizon/resolution time, relevant future availability candidates,
  and governed floor.

Gap and quality metadata vocabulary is value-free and standardized for later
packs: `insufficient_window`, `input_gap`, `session_reset`,
`maintenance_crossing`, and BBO gap/missingness flags. This contract does not
derive or mutate `label_version_id`; identities stay content-addressed from the
governed `LabelContractSpec`.
