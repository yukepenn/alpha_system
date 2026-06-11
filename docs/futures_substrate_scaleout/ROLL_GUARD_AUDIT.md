# Roll Guard Audit

FUTSUB-P21 audited the roll-splice and daily maintenance / trade-date break
guards across the five materialized LabelPack families using value-free current
local registry metadata, value-store metadata, committed materialization
summaries, and read-only canonical timestamp enumeration. Executor audit
outcome: `READY_FOR_REVIEW_NO_SILENT_CROSSINGS_FOUND`.

## Scope And Inputs

- Families covered: fixed-horizon, extended intraday, session-close /
  maintenance-flat, cost-adjusted, and path labels for ES/NQ/RTY over accepted
  2019-2026 DatasetVersions. Blocked 2018 DatasetVersions remain excluded.
- Registry metadata was read through `alpha label list --json --alpha-data-root
  /home/yuke_zhang/alpha_data/alpha_system` and `LabelRegistry` read APIs.
- Materialized value metadata was checked through registry row counts,
  value-store manifests, and bounded `load_parquet_values` samples.
- Dropped-window counts that are not emitted as label rows were recomputed
  read-only from already-canonical local OHLCV/BBO timestamp rows via the
  project canonical loader. No raw provider path was read.
- No registry write, value materialization, re-materialization, provider access,
  producer-code edit, or `src/**` edit was performed.

## Boundary Policy

Roll boundaries use the documented analytic CME quarterly calendar:
third-Friday expiration, roll date eight calendar days before expiration, and a
roll-window split of two days before / one day after. This calendar is
approximate and is not provider-exact splice truth.

All audited families record the same policy tuple:

| Family | Roll policy | Roll guard | Cross-roll policy | Maintenance policy | Maintenance guard | Maintenance policy mode |
| --- | --- | --- | --- | --- | --- | --- |
| fixed_horizon | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| extended_horizon | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| session_close_maintenance_flat | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| cost_adjusted | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| path | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |

## Per-Family Audit Results

| Family | Active unique units | Emitted rows | Roll drops | Maintenance drops | Close-out boundary drops | Silently measured |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_horizon | 144 | 44,505,301 | 708,172 | 353,333 | 0 | 0 |
| extended_horizon | 72 | 20,126,303 | 334,684 | 986,770 | 0 | 0 |
| session_close_maintenance_flat | 48 | 14,800,247 | 247,167 | 0 | 320,006 | 0 |
| cost_adjusted | 432 | 134,264,936 | 2,096,436 | 5,187,270 | 0 | 0 |
| path | 672 | 200,973,356 | 810,951 | 2,720,160 | 0 | 0 |

Cost-adjusted counts are reported on the emitted label-version surface across
`cost_adjusted_fwd_ret` and `spread_adjusted_fwd_ret`. Session-close /
maintenance-flat uses close-out boundary semantics; it does not measure forward
returns across the daily break.

## Demonstrations

Known roll-week demonstration: the chosen approximate boundary is the 2024 June
CME equity-index analytic roll date, `2024-06-13`. In the ES 2024 local
canonical timestamp drill, the `2024-06-12T23:30:00+00:00` to
`2024-06-13T00:00:00+00:00` slice produced 64 fixed-horizon roll-crossing
windows and 308 cost-adjusted label-surface roll-crossing windows; adjacent
fixed-horizon non-crossing windows were not over-dropped.

Known maintenance-break demonstration: the chosen ordinary break is January 2,
2024 at 16:00 America/Chicago (`2024-01-02T22:00:00+00:00`). In the ES 2024
local canonical timestamp drill, the `2024-01-02T21:30:00+00:00` to
`2024-01-02T22:00:00+00:00` slice produced 58 fixed-horizon maintenance
crossings and 296 cost-adjusted label-surface maintenance crossings; adjacent
fixed-horizon non-crossing windows were not over-dropped.

## Findings

- Blocking findings from this executor audit: none.
- Non-blocking finding: the committed P16 fixed-horizon coverage-summary prose
  in this worktree is stale relative to current local registry truth. The audit
  did not rely on that prose.
- No family has a missing or inconsistent guard policy/version id in current
  local registry metadata.
- No silently measured roll-splice or maintenance-crossing window was found in
  the matrix evidence, demonstration slices, or value-store samples.

## Non-Claims

This audit does not claim provider-exact roll splice truth, roll execution
semantics, contract routing, alpha quality, profitability, tradability,
execution quality, production readiness, or broker/order behavior. It verifies
only that the materialized label surfaces do not silently measure across the
analytic approximate roll boundaries or the daily maintenance / trade-date
break under the recorded guard policies.
