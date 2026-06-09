# extended_horizon LabelPack Scaleout Summary

Value-free extended-horizon LabelPack summary. It contains no raw rows,
canonical values, label values, provider responses, SQLite content, Parquet
payloads, value content hashes, or roll-calendar data.

- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P17`
- Label pack: `extended_horizon`
- Family / engine: `fixed_horizon` on the reference label engine
- Label entrypoint: `run_seed_label_pack`
- Value store: `parquet`
- Accepted states: `ACCEPTED`, `ACCEPTED_WITH_WARNINGS`
- Excluded state: blocked `2018` `ohlcv_1m` DatasetVersion remains excluded
- Symbols: `ES`, `NQ`, `RTY`
- Years selected by accepted inventory: `2019` through `2026`
- Label ids: `fwd_ret_60m`, `fwd_ret_120m`, `fwd_ret_240m`
- Expected full-window units: `72`
- Bounded-real year: `2024`
- Bounded-real executor result: `9` completed, `0` failed
- Full-window executor result: `63` completed, `9` skipped from current
  bounded-real registry/checkpoint evidence, `0` failed
- Registry records checked for required fields: `72` / `72`
- Registry records with `label_available_ts` ranges: `72` / `72`

## Guard Policy

- `label_available_ts` is required on every materialized label and is derived
  from the forward terminal row availability.
- Forward terminal lookup is contract-scoped:
  `series_id+contract_id+event_ts`.
- Roll-crossing windows use `roll_policy_id`
  `roll_cme_index_futures_quarterly`, `roll_guard_version`
  `roll_guard_v1`, and `roll_cross_policy` `drop`.
- Maintenance-crossing windows use `maintenance_policy_id`
  `cme_index_futures_daily_maintenance_break_v1`,
  `maintenance_guard_version` `maintenance_crossing_guard_v1`, and
  `maintenance_crossing_policy` `drop`.
- Guard counts below were computed with the shared fixed-horizon guard
  helpers after exact contract-scoped terminal matching.

## Horizon Totals

| Horizon | Units | Candidate terminals | Rows materialized | Roll dropped | Maintenance dropped | Roll flagged | Roll truncated | Effective samples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fwd_ret_60m` | 24 | 7270082 | 7153505 | 116577 | 0 | 0 | 0 | 119212 |
| `fwd_ret_120m` | 24 | 7169230 | 6819369 | 114320 | 235541 | 0 | 0 | 56816 |
| `fwd_ret_240m` | 24 | 7008445 | 6153429 | 103787 | 751229 | 0 | 0 | 25625 |

## Acceptance States

| State | Unit count |
| --- | ---: |
| `ACCEPTED` | 54 |
| `ACCEPTED_WITH_WARNINGS` | 18 |

## Per-Unit Coverage

Rows are materialized LabelValue rows after terminal availability,
roll-splice, maintenance-crossing, and gap semantics are applied.
Effective samples use the conservative metadata rule
`floor(row_count / horizon_minutes)` for the 1-minute overlapping grid.

| Year | Symbol | Horizon | DatasetVersion | State | Rows | Effective samples | Roll dropped | Maintenance dropped |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2019 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 328127 | 5468 | 5435 | 0 |
| 2019 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 312785 | 2606 | 5316 | 8850 |
| 2019 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 282387 | 1176 | 4830 | 32361 |
| 2019 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 328733 | 5478 | 5453 | 0 |
| 2019 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 313366 | 2611 | 5332 | 8848 |
| 2019 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 282945 | 1178 | 4852 | 32380 |
| 2019 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 293611 | 4893 | 4893 | 0 |
| 2019 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 279566 | 2329 | 4761 | 7453 |
| 2019 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_a483cc0cc282474b` | `ACCEPTED_WITH_WARNINGS` | 250682 | 1044 | 4235 | 28227 |
| 2020 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 328035 | 5467 | 5412 | 0 |
| 2020 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 312520 | 2604 | 5348 | 9003 |
| 2020 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 281844 | 1174 | 4868 | 33002 |
| 2020 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 327356 | 5455 | 5367 | 0 |
| 2020 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 311781 | 2598 | 5296 | 8993 |
| 2020 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 281050 | 1171 | 4816 | 32989 |
| 2020 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 309212 | 5153 | 5095 | 0 |
| 2020 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 294092 | 2450 | 5013 | 8578 |
| 2020 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_bac95e92f1bb1850` | `ACCEPTED` | 263989 | 1099 | 4526 | 31504 |
| 2021 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 332244 | 5537 | 5481 | 0 |
| 2021 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 316837 | 2640 | 5359 | 10596 |
| 2021 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 286254 | 1192 | 4878 | 34706 |
| 2021 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 332310 | 5538 | 5486 | 0 |
| 2021 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 316911 | 2640 | 5364 | 10587 |
| 2021 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 286318 | 1192 | 4882 | 34688 |
| 2021 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 308896 | 5148 | 5027 | 0 |
| 2021 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 294197 | 2451 | 4921 | 9937 |
| 2021 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_8aeb50fb409fc691` | `ACCEPTED` | 264572 | 1102 | 4407 | 32610 |
| 2022 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 333109 | 5551 | 5518 | 0 |
| 2022 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 317756 | 2647 | 5396 | 11937 |
| 2022 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 287276 | 1196 | 4916 | 35811 |
| 2022 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 333097 | 5551 | 5518 | 0 |
| 2022 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 317742 | 2647 | 5396 | 11934 |
| 2022 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 287263 | 1196 | 4916 | 35812 |
| 2022 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 317314 | 5288 | 5192 | 0 |
| 2022 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 302359 | 2519 | 5051 | 11336 |
| 2022 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_dc7c86c813fe0dfe` | `ACCEPTED` | 272495 | 1135 | 4570 | 34354 |
| 2023 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 331930 | 5532 | 5514 | 0 |
| 2023 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 316633 | 2638 | 5392 | 11829 |
| 2023 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 286167 | 1192 | 4908 | 35539 |
| 2023 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 332306 | 5538 | 5518 | 0 |
| 2023 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 316976 | 2641 | 5396 | 11856 |
| 2023 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 286496 | 1193 | 4916 | 35586 |
| 2023 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 313417 | 5223 | 5185 | 0 |
| 2023 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 298996 | 2491 | 5044 | 10986 |
| 2023 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_ec144f9a02a64774` | `ACCEPTED` | 269678 | 1123 | 4570 | 33229 |
| 2024 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 326038 | 5433 | 5507 | 0 |
| 2024 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 311065 | 2592 | 5386 | 11673 |
| 2024 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 281318 | 1172 | 4907 | 35048 |
| 2024 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 326278 | 5437 | 5516 | 0 |
| 2024 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 311292 | 2594 | 5394 | 11687 |
| 2024 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 281539 | 1173 | 4914 | 35072 |
| 2024 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 303296 | 5054 | 5087 | 0 |
| 2024 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 289124 | 2409 | 4957 | 10907 |
| 2024 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_05404069799decb0` | `ACCEPTED` | 260537 | 1085 | 4485 | 32629 |
| 2025 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 323882 | 5398 | 5517 | 0 |
| 2025 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 308836 | 2573 | 5454 | 11633 |
| 2025 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 279092 | 1162 | 4974 | 34903 |
| 2025 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 323829 | 5397 | 5518 | 0 |
| 2025 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 308783 | 2573 | 5455 | 11624 |
| 2025 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 279040 | 1162 | 4975 | 34895 |
| 2025 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 304805 | 5080 | 5203 | 0 |
| 2025 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 290188 | 2418 | 5157 | 11082 |
| 2025 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_35ffead770498acd` | `ACCEPTED` | 261148 | 1088 | 4675 | 33224 |
| 2026 | `ES` | `fwd_ret_60m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 133138 | 2218 | 1380 | 0 |
| 2026 | `ES` | `fwd_ret_120m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 127020 | 1058 | 1379 | 4800 |
| 2026 | `ES` | `fwd_ret_240m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 114900 | 478 | 1259 | 14399 |
| 2026 | `NQ` | `fwd_ret_60m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 133084 | 2218 | 1380 | 0 |
| 2026 | `NQ` | `fwd_ret_120m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 126980 | 1058 | 1379 | 4796 |
| 2026 | `NQ` | `fwd_ret_240m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 114861 | 478 | 1259 | 14381 |
| 2026 | `RTY` | `fwd_ret_60m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 129458 | 2157 | 1375 | 0 |
| 2026 | `RTY` | `fwd_ret_120m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 123564 | 1029 | 1374 | 4616 |
| 2026 | `RTY` | `fwd_ret_240m` | `dsv_databento_ohlcv_a0342ee6a412622b` | `ACCEPTED_WITH_WARNINGS` | 111578 | 464 | 1249 | 13880 |

## Expected Gaps

- `2018` `ohlcv_1m` remains `BLOCKED` in the accepted inventory and is
  excluded rather than forced into materialization.
- `2019` and `2026` are included as `ACCEPTED_WITH_WARNINGS`; `2026` uses
  the partial-year window ending `2026-06-01T00:00:00+00:00`.
- The committed inventory is year-level for `ohlcv_1m`; it does not expose a
  separate ES/NQ-2018 eligibility surface, so no 2018 symbol was selected.

## Overlap-Aware N_eff Metadata

- Metadata version: `horizon_overlap_metadata_v1`.
- Raw row count and effective sample count are distinct fields.
- Rows are not represented as independent samples.
- Effective samples are below raw rows for every extended-horizon unit.
- Runtime N_eff reporting remains owned by FUTSUB-P25; this phase records
  the per-pack overlap metadata that feeds it.

## Safety

This phase adds substrate label materialization only. It makes no
profitability, tradability, production, live, paper, broker, order-routing,
or capital-allocation claim. Local Parquet values, checkpoint ledgers, and
the SQLite label registry remain under `ALPHA_DATA_ROOT` and are not
commit-eligible.
