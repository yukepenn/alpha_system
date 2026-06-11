# FUTSUB-P23 Session-Horizon Coverage Matrix

Value-free session x horizon rollup for the current label substrate. This
matrix records coverage and guard semantics by session segment; it does not
contain prices, label values, spreads, provider payloads, local paths, SQLite
content, Parquet payloads, or execution-quality claims.

## Inputs And Status Codes

- Session metadata requirement:
  `docs/futures_substrate_scaleout/DATASET_ACCEPTANCE.md` records
  `session_segment` as required DatasetVersion evidence.
- Session labels:
  `session_close` uses the same-contract RTH close terminal; `maintenance_flat`
  uses the same-contract last bar at or before the daily maintenance /
  trade-date break.
- Guard evidence:
  `research/futures_substrate_scaleout_v1/matrices/maintenance_crossing_invalidation.md`
  and `research/futures_substrate_scaleout_v1/matrices/roll_window_coverage.md`.

Status codes:

| Code | Meaning |
| --- | --- |
| `P` | Coverage present for 2020-2025 accepted DatasetVersions. |
| `W` | Coverage present with warning metadata for 2019 and partial-year 2026. |
| `EE` | 2018 expected exclusion because the DatasetVersion is `BLOCKED`. |
| `GD` | Guard-dropped or boundary-limited by policy; this is expected guard behavior, not a resolver gap. |
| `NA` | Not a defined label horizon for that session row. |

## Matrix

The `Years` column applies to every symbol ES/NQ/RTY. No session/horizon row has
an unexpected resolver gap.

| Session segment / guard row | Horizon coverage | Years | Status | Bound / evidence |
| --- | --- | --- | --- | --- |
| `RTH` source rows | `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 2019, 2026 | `W` | Input DatasetVersions preserve warning metadata; forward/path/cost labels resolve where the guarded terminal is valid. |
| `RTH` source rows | `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 2020-2025 | `P` | Active registry locks resolve; no silently measured roll or maintenance crossing in P21 matrices. |
| `RTH` source rows | `session_close` | 2019, 2026 | `W` | Same-contract RTH close terminal; warning metadata preserved. |
| `RTH` source rows | `session_close` | 2020-2025 | `P` | `close_out` registry cells resolve for all symbols and accepted clean years. |
| `ETH` source rows | `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 2019, 2026 | `W` | ETH rows are covered through the accepted canonical session grid when guarded terminals do not cross maintenance or roll boundaries. |
| `ETH` source rows | `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 2020-2025 | `P` | Active registry locks resolve; guard drops are explicit in P21 matrices. |
| `maintenance-adjacent windows` | forward/path/cost horizons ending across the daily break | 2019-2026 | `GD` | P21 records `9,247,533` maintenance-overlap windows dropped across forward/path/cost families and `0` silently measured crossings. |
| `maintenance-adjacent windows` | `maintenance_flat` | 2019, 2026 | `W` | Same-contract last bar at or before the daily break; warning metadata preserved. |
| `maintenance-adjacent windows` | `maintenance_flat` | 2020-2025 | `P` | `close_out` registry cells resolve; P21 records close-out boundary handling separately from forward drops. |
| `roll-window-adjacent windows` | all forward/path/cost/close-out governed horizons | 2019-2026 | `GD` | P21 records `4,197,410` roll-overlap windows dropped across the five families and `0` silently measured crossings. |
| `2018 blocked window` | all governed horizons and close-out labels | 2018 | `EE` | Campaign acceptance inventory blocks 2018; no session/horizon label cell is expected. |

## Guard Totals Consumed

| Family | Roll-overlap dropped | Maintenance-overlap dropped | Close-out boundary drops | Silently measured crossings |
| --- | ---: | ---: | ---: | ---: |
| `fixed_base` | 708172 | 353333 | 0 | 0 |
| `fixed_extended` | 334684 | 986770 | 0 | 0 |
| `close_out` | 247167 | 0 | 320006 | 0 |
| `cost_adjusted` | 2096436 | 5187270 | 0 | 0 |
| `path` | 810951 | 2720160 | 0 | 0 |
| **Total** | **4197410** | **9247533** | **320006** | **0** |

## Gap List

- Expected exclusions: all 2018 session/horizon cells.
- Guard-dropped windows: expected, explicit, and not counted as resolver gaps.
- Unexpected gaps: none.
