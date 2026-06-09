# fixed_horizon LabelPack Scaleout Summary

Value-free fixed-horizon LabelPack summary. It contains no raw rows, canonical
values, label values, provider responses, SQLite content, Parquet payloads, or
roll-calendar data.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P16`
- Family: `fixed_horizon`
- Engine: `reference`
- Label entrypoint: `run_seed_label_pack`
- Value store: `parquet`
- Accepted states: `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`
- Excluded state: blocked 2018 DatasetVersions remain excluded
- Symbols: `ES`, `NQ`, `RTY`
- Years selected by accepted inventory: `2019` through `2026`
- Label ids: `fwd_ret_1m`, `fwd_ret_3m`, `fwd_ret_5m`, `fwd_ret_10m`,
  `fwd_ret_15m`, `fwd_ret_30m`
- Expected full-window units: `144`
- Bounded-real year: `2024`
- Bounded-real units: `18`
- Bounded-real executor result: `18` selected, `16` completed, `2` skipped from
  current registry truth, `0` failed
- Full-window executor result: not run in this executor turn; the full accepted
  grid remains `144` units and is restart-safe from the bounded-real checkpoint
  and registry evidence

## Guard Policy

- `label_available_ts` is required on every materialized label and is derived
  from the forward terminal row availability.
- Forward terminal lookup is contract-scoped:
  `series_id+contract_id+event_ts`.
- Roll-crossing windows use `roll_policy_id`
  `roll_cme_index_futures_quarterly`, `roll_guard_version`
  `roll_guard_v1`, `roll_cross_policy` `drop`, and a roll-window split of two
  days before / one day after the approximate quarterly roll date.
- Maintenance-crossing windows use `maintenance_policy_id`
  `cme_index_futures_daily_maintenance_break_v1`,
  `maintenance_guard_version` `maintenance_crossing_guard_v1`, and
  `maintenance_crossing_policy` `drop`.

## Coverage Metadata

- Row counts are materialized LabelValue rows after terminal availability,
  roll-splice, maintenance-crossing, and gap semantics are applied.
- `N_eff` is a distinct analysis concept from materialized row count. For
  fixed-horizon labels, downstream integration must account for overlapping
  forward horizons rather than treating every row as an independent effective
  sample.
- Actual row counts, content hashes, registry rows, checkpoint ledgers, and
  Parquet label values are local-only under `ALPHA_DATA_ROOT` and are not
  recorded in this summary.

## Safety

This phase adds substrate materialization plumbing only. It makes no
profitability, tradability, production, live, paper, broker, order-routing, or
capital-allocation claim.
