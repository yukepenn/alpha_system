# FUTSUB-P23 Label-Family Coverage Matrix

Value-free coverage matrix for
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` / `FUTSUB-P23`.

This report contains registry statuses, lock counts, row-count metadata, and
coverage classifications only. It contains no label values, prices, returns,
spreads, provider payloads, local SQLite content, Parquet payloads, local data
paths, profitability language, execution-quality claim, paper/live/broker/order
behavior, or production claim.

## Inputs

- Label registry read path:
  `LabelRegistry.from_alpha_data_root(...).read_label_records()`, filtered to
  lifecycle state `REGISTERED`.
- Resolver evidence:
  `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`.
- Registry integration evidence:
  `research/futures_substrate_scaleout_v1/label_packs/registry_integration_audit.md`.
- Guard evidence:
  `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`,
  `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`,
  and `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_audit.md`.
- Expected 2018 exclusion evidence:
  `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.

Current P23 registry read returned `1368` active `REGISTERED` locks in the
current label surface. Historical deprecated rows are not counted as coverage.
The current active surface matches the P22 current preview total: `1368` locks
resolved, `0` resolver gaps.

## Legend

| Code | Meaning | Gap class |
| --- | --- | --- |
| `P` | Present: every required active, non-deprecated label version for the family / symbol / horizon / year cell is registered and covered by the P22 resolver evidence. | none |
| `W` | Present with warning metadata: same as `P`, but the cell belongs to 2019 or partial-year 2026, both surfaced as `ACCEPTED_WITH_WARNINGS`. | none |
| `EE` | Expected-excluded: 2018 is excluded because the required DatasetVersion is `BLOCKED`; this includes RTY-2018 and the campaign-level 2018 fallback for ES/NQ. | expected |
| `UG` | Unexpected gap: an accepted or warned cell lacks one or more required active locks. | unexpected |

`cost_adjusted` cells require both `cost_adjusted_fwd_ret` and
`spread_adjusted_fwd_ret`. `path` cells require `path_mfe`, `path_mae`,
`path_target_before_stop`, and `path_triple_barrier`.

## Cell Counts

Scope is five governed surfaces rendered as 729
family x symbol x horizon x year cells, including explicit 2018 expected
exclusions. Present and warned cells together cover all 2019-2026 accepted or
accepted-with-warnings cells.

| Status | Cells |
| --- | ---: |
| `P` | 486 |
| `W` | 162 |
| `EE` | 81 |
| `UG` | 0 |

## Surface Counts

| Surface | Matrix cells | `P` cells | `W` cells | `EE` cells | `UG` cells | Active locks counted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_base` | 162 | 108 | 36 | 18 | 0 | 144 |
| `fixed_extended` | 81 | 54 | 18 | 9 | 0 | 72 |
| `close_out` | 54 | 36 | 12 | 6 | 0 | 48 |
| `cost_adjusted` | 243 | 162 | 54 | 27 | 0 | 432 |
| `path` | 189 | 126 | 42 | 21 | 0 | 672 |
| **Total** | **729** | **486** | **162** | **81** | **0** | **1368** |

## Status Matrix

| Surface | Required labels/cell | Symbol | Horizon | Active locks 2019-2026 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fixed_base` | 1 | `ES` | `1m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `NQ` | `1m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `RTY` | `1m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `ES` | `3m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `NQ` | `3m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `RTY` | `3m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `ES` | `5m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `NQ` | `5m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `RTY` | `5m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `ES` | `10m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `NQ` | `10m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `RTY` | `10m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `ES` | `15m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `NQ` | `15m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `RTY` | `15m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `ES` | `30m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `NQ` | `30m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_base` | 1 | `RTY` | `30m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `ES` | `60m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `NQ` | `60m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `RTY` | `60m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `ES` | `120m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `NQ` | `120m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `RTY` | `120m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `ES` | `240m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `NQ` | `240m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `fixed_extended` | 1 | `RTY` | `240m` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `close_out` | 1 | `ES` | `session_close` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `close_out` | 1 | `NQ` | `session_close` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `close_out` | 1 | `RTY` | `session_close` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `close_out` | 1 | `ES` | `maintenance_flat` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `close_out` | 1 | `NQ` | `maintenance_flat` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `close_out` | 1 | `RTY` | `maintenance_flat` | 8 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `1m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `1m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `1m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `3m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `3m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `3m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `5m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `5m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `5m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `10m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `10m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `10m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `15m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `15m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `15m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `30m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `30m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `30m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `60m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `60m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `60m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `120m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `120m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `120m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `ES` | `240m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `NQ` | `240m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `cost_adjusted` | 2 | `RTY` | `240m` | 16 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `5m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `5m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `5m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `10m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `10m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `10m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `15m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `15m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `15m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `30m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `30m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `30m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `60m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `60m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `60m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `120m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `120m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `120m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `ES` | `240m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `NQ` | `240m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |
| `path` | 4 | `RTY` | `240m` | 32 | `EE` | `W` | `P` | `P` | `P` | `P` | `P` | `P` | `W` |

## Explicit Gap List

### Expected Exclusions

- All 2018 label-family cells are `EE`: five surfaces, ES/NQ/RTY, and every
  governed horizon or close-out label. Count: `81` cells.
- The 2018 exclusion is expected because the campaign acceptance inventory marks
  the required 2018 DatasetVersion as `BLOCKED`; RTY-2018 is the binding sparse
  history issue, and the campaign applies dataset-level fallback rather than
  fabricating per-symbol acceptance.
- 2019 and 2026 are not gaps. They resolve as `W` because their DatasetVersions
  carry warning metadata; 2026 is partial-year.
- P20 path feasibility expected exclusions: none in the current registry
  surface. P20 recorded `0` flagged infeasible units and all four path variants
  resolved for every 2019-2026 symbol/horizon cell.

### Unexpected Gaps

None. Every accepted or accepted-with-warnings family / symbol / horizon / year
cell resolves to the required active label-version count through the P22
resolver evidence.

## Downstream Use

- `FUTSUB-P24` and `FUTSUB-P25` should treat `W` cells as usable only with the
  warning context preserved.
- `FUTSUB-P25` owns overlap-aware N_eff computation. This matrix records the
  coverage surface and points to the horizon-quality report for the current
  overlap provenance.
- A registered cell is not a statement that rows are independent samples.
