# session_close_maintenance_flat LabelPack Scaleout Summary

Value-free session-close / maintenance-flat LabelPack summary. It contains no raw rows,
canonical values, label values, provider responses, SQLite content, Parquet payloads,
value content hashes, or roll-calendar data.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P18`
- Label pack: `session_close_maintenance_flat`
- Family / engine: `fixed_horizon` close-out labels on the reference label engine
- Label entrypoint: `alpha scaleout label-pack` -> `run_seed_label_pack`
- Value store: `parquet`
- Accepted states: `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`
- Excluded state: blocked `2018` DatasetVersions remain excluded
- Symbols: `ES`, `NQ`, `RTY`
- Years selected by accepted inventory: `2019` through `2026`
- Label ids: `session_close`, `maintenance_flat`
- Accepted full-window units: `48`
- Bounded-real year: `2024`
- Bounded-real executor result: `3` completed, `3` skipped from prior registry/checkpoint evidence, `0` failed after repair
- Full-window executor result: `42` completed, `6` skipped from bounded-real registry/checkpoint evidence, `0` failed
- Registry records checked for required fields: `48` / `48`
- Registry records with `label_available_ts` ranges: `48` / `48`

## Close-Out Semantics

- `session_close`: terminal is the same-contract RTH close-out bar for the CME trade date,
  selected by the explicit 08:30-15:00 America/Chicago RTH clock boundary. A source row
  at or after that terminal has no remaining same-session close-out horizon and is dropped.
- `maintenance_flat`: terminal is the same-contract last bar at or before the 16:00
  America/Chicago daily maintenance / trade-date break. A source row at or after that
  terminal has no remaining same-break horizon and is dropped.
- Both labels use `series_id+contract_id+event_ts` terminal lookup and
  `series_id+contract_id+close_out_boundary` terminal scope. No terminal is selected from
  a different contract or a different maintenance/trade-date scope.

## Guard Policy

- `label_available_ts` is required on every materialized label and is derived from the
  close-out terminal row availability.
- Roll-crossing windows use `roll_policy_id` `roll_cme_index_futures_quarterly`,
  `roll_guard_version` `roll_guard_v1`, and `roll_cross_policy` `drop`.
- Maintenance-crossing windows use `maintenance_policy_id`
  `cme_index_futures_daily_maintenance_break_v1`, `maintenance_guard_version`
  `maintenance_crossing_guard_v1`, and `maintenance_crossing_policy` `drop`.
- Guard counts below were computed with the shared fixed-horizon close-out terminal
  and guard helpers after exact contract-scoped terminal matching.

## Horizon Totals

| Horizon | Units | Input rows | Candidate terminals | Rows materialized | Boundary dropped | Maintenance dropped | Roll dropped | Roll flagged | Roll truncated | Effective samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `session_close` | 24 | 7683710 | 7369395 | 7248193 | 314315 | 0 | 121202 | 0 | 0 | 5598 |
| `maintenance_flat` | 24 | 7683710 | 7678019 | 7552054 | 5691 | 0 | 125965 | 0 | 0 | 5604 |

## Acceptance States

| State | Unit count |
| --- | ---: |
| `ACCEPTED` | 36 |
| `ACCEPTED_WITH_WARNINGS` | 12 |

## Per-Unit Coverage

Rows are materialized `LabelValueRecord` rows after close-out terminal availability,
roll-splice, maintenance-crossing, and gap semantics are applied. Effective samples
count distinct close-out terminal events per unit; rows are not represented as
independent samples.

| Year | Symbol | Horizon | DatasetVersion | State | Rows | Effective samples | Boundary dropped | Maintenance dropped | Roll dropped |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2019 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 343475 | 254 | 258 | 0 | 5799 |
| 2019 | `ES` | `session_close` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 332447 | 254 | 11466 | 0 | 5619 |
| 2019 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 343778 | 254 | 258 | 0 | 5809 |
| 2019 | `NQ` | `session_close` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 332753 | 254 | 11463 | 0 | 5629 |
| 2019 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 323130 | 254 | 258 | 0 | 5453 |
| 2019 | `RTY` | `session_close` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 312279 | 254 | 11286 | 0 | 5276 |
| 2020 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 343501 | 255 | 259 | 0 | 5848 |
| 2020 | `ES` | `session_close` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 332472 | 255 | 11468 | 0 | 5668 |
| 2020 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 342848 | 255 | 259 | 0 | 5822 |
| 2020 | `NQ` | `session_close` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 331823 | 255 | 11464 | 0 | 5642 |
| 2020 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 332157 | 255 | 259 | 0 | 5669 |
| 2020 | `RTY` | `session_close` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 321169 | 255 | 11427 | 0 | 5489 |
| 2021 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 347266 | 255 | 259 | 0 | 5838 |
| 2021 | `ES` | `session_close` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 333349 | 254 | 14386 | 0 | 5628 |
| 2021 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 347293 | 255 | 259 | 0 | 5841 |
| 2021 | `NQ` | `session_close` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 333351 | 254 | 14411 | 0 | 5631 |
| 2021 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 334055 | 255 | 259 | 0 | 5581 |
| 2021 | `RTY` | `session_close` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 320533 | 254 | 13989 | 0 | 5373 |
| 2022 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 347989 | 254 | 258 | 0 | 5872 |
| 2022 | `ES` | `session_close` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 333230 | 254 | 15257 | 0 | 5632 |
| 2022 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 347982 | 254 | 258 | 0 | 5872 |
| 2022 | `NQ` | `session_close` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 333222 | 254 | 15258 | 0 | 5632 |
| 2022 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 339233 | 254 | 258 | 0 | 5671 |
| 2022 | `RTY` | `session_close` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 324485 | 254 | 15246 | 0 | 5431 |
| 2023 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 347026 | 254 | 258 | 0 | 5869 |
| 2023 | `ES` | `session_close` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 331491 | 253 | 16033 | 0 | 5629 |
| 2023 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 347228 | 254 | 258 | 0 | 5872 |
| 2023 | `NQ` | `session_close` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 331676 | 253 | 16050 | 0 | 5632 |
| 2023 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 336491 | 254 | 258 | 0 | 5687 |
| 2023 | `RTY` | `session_close` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 321237 | 253 | 15751 | 0 | 5448 |
| 2024 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 340740 | 248 | 252 | 0 | 5866 |
| 2024 | `ES` | `session_close` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 326040 | 248 | 15192 | 0 | 5626 |
| 2024 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 340869 | 248 | 252 | 0 | 5871 |
| 2024 | `NQ` | `session_close` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 326169 | 248 | 15192 | 0 | 5631 |
| 2024 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 327671 | 248 | 252 | 0 | 5617 |
| 2024 | `RTY` | `session_close` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 313015 | 248 | 15147 | 0 | 5378 |
| 2025 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 338379 | 247 | 251 | 0 | 5931 |
| 2025 | `ES` | `session_close` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 323800 | 247 | 15070 | 0 | 5691 |
| 2025 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 338347 | 247 | 251 | 0 | 5931 |
| 2025 | `NQ` | `session_close` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 323769 | 247 | 15069 | 0 | 5691 |
| 2025 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 327551 | 247 | 251 | 0 | 5755 |
| 2025 | `RTY` | `session_close` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 313012 | 247 | 15030 | 0 | 5515 |
| 2026 | `ES` | `maintenance_flat` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 139039 | 101 | 102 | 0 | 1498 |
| 2026 | `ES` | `session_close` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 132979 | 101 | 6222 | 0 | 1438 |
| 2026 | `NQ` | `maintenance_flat` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 139010 | 101 | 102 | 0 | 1498 |
| 2026 | `NQ` | `session_close` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 132950 | 101 | 6222 | 0 | 1438 |
| 2026 | `RTY` | `maintenance_flat` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 136996 | 101 | 102 | 0 | 1495 |
| 2026 | `RTY` | `session_close` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 130942 | 101 | 6216 | 0 | 1435 |

## Expected Gaps

- `2018` remains `BLOCKED` in the accepted inventory and is excluded rather than forced
  into materialization.
- `2019` and `2026` are included as `ACCEPTED_WITH_WARNINGS`; `2026` uses the
  partial-year window ending `2026-06-01T00:00:00+00:00`.
- The committed inventory is year-level for `ohlcv_1m`; no 2018 symbol was selected.

## Overlap-Aware N_eff Metadata

- Metadata version: `horizon_overlap_metadata_v1`.
- Raw row count and effective sample count are distinct fields.
- Effective samples count distinct close-out terminal events, not per-row labels.
- Rows are not represented as independent samples; `N_eff` never exceeds raw rows.
- Runtime N_eff reporting remains owned by FUTSUB-P25; this phase records the
  per-pack metadata that feeds that reporting.

## Safety

This phase adds substrate label materialization only. It makes no profitability,
tradability, production, live, paper, broker, order-routing, or capital-allocation
claim. Local Parquet values, checkpoint ledgers, and the SQLite label registry remain
under `ALPHA_DATA_ROOT` and are not commit-eligible.
