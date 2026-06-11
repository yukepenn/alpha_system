# Roll Guard Audit Evidence Notes

Value-free FUTSUB-P21 backing notes. This file records registry metadata,
aggregate counts, policy ids, and timestamp-window demonstrations only. It
contains no prices, returns, per-row label values, provider payloads, SQLite
content, Parquet paths, or roll-calendar data.

## Inputs And Method

- Registry metadata was read through `alpha label list --json --alpha-data-root /home/yuke_zhang/alpha_data/alpha_system` and `LabelRegistry.from_alpha_data_root(...).read_label_records()`.
- Materialized value metadata was checked through registry `value_record_count`, value-store manifests, and bounded `alpha_system.core.value_store.load_parquet_values` samples.
- Missing dropped-window counts were recomputed read-only from already-canonical local OHLCV/BBO timestamp rows via `alpha_system.data.foundation.canonical_loader`; no raw provider path was read.
- Roll boundaries use the analytic approximate CME quarterly calendar documented in `docs/futures_substrate_scaleout/ROLL_GUARD.md`: third-Friday expiration, roll date eight calendar days before expiration, and a two-days-before / one-day-after roll-window split. This is not provider-exact splice truth.
- Drop counts for `extended_horizon`, `session_close_maintenance_flat`, and `path` are reused from their committed value-free materialization summaries/matrices and cross-checked against current local registry policy/version metadata.
- No registry write, value materialization, re-materialization, source-code edit, provider call, or raw provider read was performed.

## Registry Surface

| Family | Active unique label-version units | Emitted label rows | Producer provenance observed | Registry note |
| --- | ---: | ---: | --- | --- |
| `fixed_horizon` | 144 | 44,505,301 | `alpha_system.labels.fast.pack_materializer.v1`; `alpha_system.labels.reference_engine.v1` | 145 raw records; deprecated duplicate `ES_2024_fwd_ret_5m` ignored |
| `extended_horizon` | 72 | 20,126,303 | `alpha_system.labels.reference_engine.v1` | full 2019-2026 accepted grid |
| `session_close_maintenance_flat` | 48 | 14,800,247 | `alpha_system.labels.reference_engine.v1` | full 2019-2026 accepted grid |
| `cost_adjusted` | 432 | 134,264,936 | `alpha_system.labels.reference_engine.v1` | 216 horizon units across two emitted cost labels |
| `path` | 672 | 200,973,356 | `alpha_system.labels.fast.pack_materializer.v1` | four path variants across full accepted grid |

The current local registry has 2,325 total label records. The fixed-horizon
base family exposes 145 raw records and 144 active unique records because the
prior repair deprecated the duplicate `ES_2024_fwd_ret_5m` row. The older P16
coverage-summary prose in this worktree still describes a bounded 2024 run; the
audit treats that prose as stale and relies on registry/value metadata instead.

## Policy Provenance

All current local registry records in the audit surface agree on the same guard
policy tuple.

| Family | `roll_policy_id` | `roll_guard_version` | Roll policy | `maintenance_policy_id` | `maintenance_guard_version` | Maintenance policy |
| --- | --- | --- | --- | --- | --- | --- |
| `fixed_horizon` | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| `extended_horizon` | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| `session_close_maintenance_flat` | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| `cost_adjusted` | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |
| `path` | `roll_cme_index_futures_quarterly` | `roll_guard_v1` | `drop` | `cme_index_futures_daily_maintenance_break_v1` | `maintenance_crossing_guard_v1` | `drop` |

## Aggregate Guard Counts

| Family | Roll-overlap windows dropped | Maintenance-overlap windows dropped | Close-out boundary drops | Truncated | Flagged | Invalid | Silently measured |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_horizon` | 708,172 | 353,333 | 0 | 0 | 0 | 0 | 0 |
| `extended_horizon` | 334,684 | 986,770 | 0 | 0 | 0 | 0 | 0 |
| `session_close_maintenance_flat` | 247,167 | 0 | 320,006 | 0 | 0 | 0 | 0 |
| `cost_adjusted` | 2,096,436 | 5,187,270 | 0 | 0 | 0 | 0 | 0 |
| `path` | 810,951 | 2,720,160 | 0 | 0 | 0 | 0 | 0 |

Cost-adjusted counts are reported on the emitted label-version surface: each
shared guarded BBO horizon unit feeds `cost_adjusted_fwd_ret` and
`spread_adjusted_fwd_ret`.

## Known 2024 Roll-Week Demonstration

The chosen approximate roll boundary is the 2024 June CME equity-index analytic
roll date, `2024-06-13`. The calendar is approximate and not provider-exact.
The local read-only drill used `ES` / 2024 canonical timestamps around the UTC
date boundary into the approximate roll date.

| Evidence slice | Source timestamps selected | Guarded crossing windows | Adjacent non-crossing windows | Observed disposition |
| --- | ---: | ---: | ---: | --- |
| `fixed_horizon` ES 2024, `2024-06-12T23:30:00+00:00` to `2024-06-13T00:00:00+00:00`, horizons 1/3/5/10/15/30m | 30 | 64 | 180 | crossing windows counted as `drop`; adjacent non-crossing windows not over-dropped |
| `cost_adjusted` ES 2024, same slice, horizons 1/3/5/10/15/30/60/120/240m, two emitted labels | 30 | 308 | not recomputed for this drill | crossing windows counted as `drop` on the emitted label-version surface |

The full 2024 all-symbol matrix rows record 97,966 fixed-horizon roll drops,
46,153 extended roll drops, 33,989 close-out roll drops, 289,370 cost-adjusted
roll drops, and 112,061 path roll drops, all with zero silently measured
crossings.

## Known Maintenance-Break Demonstration

The chosen ordinary daily maintenance / trade-date break is the January 2,
2024 CME break starting at 16:00 America/Chicago (`2024-01-02T22:00:00+00:00`).
The local read-only drill used `ES` / 2024 canonical timestamps immediately
before that break.

| Evidence slice | Source timestamps selected | Guarded crossing windows | Adjacent non-crossing windows | Observed disposition |
| --- | ---: | ---: | ---: | --- |
| `fixed_horizon` ES 2024, `2024-01-02T21:30:00+00:00` to `2024-01-02T22:00:00+00:00`, horizons 1/3/5/10/15/30m | 30 | 58 | 180 | crossing windows invalidated before measurement; adjacent non-crossing windows not over-dropped |
| `cost_adjusted` ES 2024, same slice, horizons 1/3/5/10/15/30/60/120/240m, two emitted labels | 30 | 296 | not recomputed for this drill | crossing windows counted as `drop` on the emitted label-version surface |

The full 2024 all-symbol matrix rows record 47,731 fixed-horizon maintenance
invalidations, 137,016 extended maintenance drops, 46,287 close-out boundary
stops, 722,942 cost-adjusted maintenance drops, and 361,440 path maintenance
drops, all with zero silently measured crossings.

## Value-Store Sample Reads

Bounded read-only samples through `alpha_system.core.value_store` confirmed
manifest/readability consistency and zero emitted roll/maintenance guard flags.
Dropped windows are not emitted rows, so these samples complement rather than
replace the matrix drop-count enumeration.

| Family | Sample label / partition | Registry rows | Manifest rows | Loaded rows | Emitted roll/maintenance guard-flag rows |
| --- | --- | ---: | ---: | ---: | ---: |
| `fixed_horizon` | `fwd_ret_30m` / `ES_2024_fwd_ret_30m` | 333,575 | 333,575 | 333,575 | 0 |
| `extended_horizon` | `fwd_ret_240m` / `ES_2024_fwd_ret_240m` | 281,318 | 281,318 | 281,318 | 0 |
| `session_close_maintenance_flat` | `maintenance_flat` / `ES_2024_maintenance_flat` | 340,740 | 340,740 | 340,740 | 0 |
| `cost_adjusted` | `cost_adjusted_fwd_ret` / `ES_2024_240m` | 306,903 | 613,806 | 613,806 | 0 |
| `path` | `path_mfe` / `ES_2024_240m` | 281,468 | 1,125,872 | 1,125,872 | 0 |

## Findings

- Blocking findings: none from this executor audit.
- Non-blocking finding: the committed P16 fixed-horizon coverage summary prose
  is stale relative to current local registry truth. The audit did not rely on
  that prose and used registry/value metadata plus read-only timestamp
  enumeration instead.
- No family has a missing or inconsistent `roll_policy_id`,
  `roll_guard_version`, `maintenance_policy_id`, or
  `maintenance_guard_version` in current local registry metadata.
- No silently measured roll-splice or maintenance-crossing window was found in
  the matrix evidence, demonstration slices, or value-store samples.
