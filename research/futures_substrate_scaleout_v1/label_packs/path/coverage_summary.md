# FUTSUB-P20 path LabelPack Coverage Summary

Value-free evidence only. This report contains no per-row label values, prices,
returns, provider responses, local Parquet paths, content hashes, SQLite
content, checkpoint payloads, or roll-calendar data.

- Generated: `2026-06-11`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P20`
- Family: `path`
- Status: `materialized_registered`
- Engine: `v1` (`alpha_system.labels.fast.pack_materializer.v1`)
- Worker configuration: requested `8`, effective `8` for the full accepted grid,
  effective `7` for the bounded `ES`/`2024` pilot, threads per worker `2`
- Thread caps used: `ALPHA_LABEL_CPU_WORKERS=8`, `POLARS_MAX_THREADS=2`,
  `OMP_NUM_THREADS=2`, `RAYON_NUM_THREADS=2`, `NUMBA_NUM_THREADS=2`
- Registry writes: parent-only serial through the official `LabelRegistry` path
- Reference oracle: existing governed `alpha_system.labels.families.path`
  family definitions; no new variants, no parameter sweep, no tuning

## Resume Accounting

The current executor first validated the bounded real `ES` / `2024` batch, then
expanded through the full accepted grid with checkpoint + registry truth. The
full-grid run skipped the seven bounded `ES`/`2024` units and completed the
remaining units.

| Run | Completed | Skipped | Failed | Notes |
| --- | ---: | ---: | ---: | --- |
| bounded real `ES`/`2024`, workers requested 8 | 7 | 0 | 0 | effective workers reduced to 7 runnable units |
| full accepted grid, workers=8 | 161 | 7 | 0 | skipped bounded units from checkpoint + registry truth |
| current registry/ledger truth | 168 | 0 remaining | 0 | 672 label versions resolve with required metadata |

## Materialization Window

- Included years: `2019` through `2026`.
- Excluded year: `2018`, because the DatasetVersion is `BLOCKED`; see
  `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.
- Eligible states: `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.
- Accepted unit states: `126` `ACCEPTED`,
  `42` `ACCEPTED_WITH_WARNINGS`.
- 2019 warning metadata and 2026 partial-year warning metadata are preserved
  through the DatasetVersion state.

## Path Definitions

- Variants: `mfe`, `mae`, `target_before_stop`, `triple_barrier`.
- Horizons: `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m`.
- Governed path parameters: `price_field=close`, `direction=long`,
  `target_return=0.02`, `stop_return=-0.02`,
  `same_bar_policy=ambiguous`.
- `mfe` / `mae` `label_available_ts`: guarded full-window end.
- `target_before_stop` / `triple_barrier` `label_available_ts`: first barrier
  touch when touched, otherwise guarded window end.
- Full path windows are contract-scoped on `series_id+contract_id+event_ts` and
  guarded before excursion or barrier measurement.

## Feasibility Accounting

| Metric | Count |
| --- | ---: |
| Expected units | 168 |
| Materialized units | 168 |
| Flagged infeasible units | 0 |
| Label versions | 672 |
| Unique Parquet value files under `ALPHA_DATA_ROOT` | 168 |
| Metadata-column rows scanned across all four variants | 200,973,356 |
| Max rows in one label version | 347,309 |
| Per-label row budget | 550,000 |
| Aggregate per-label-surface row budget | 103,950,000 |
| Aggregate all-variant path-evaluation budget | 415,800,000 |

No variant / horizon / symbol / year unit was flagged infeasible. The recorded
R-021 bound is the configured per-label row and path-evaluation budget in
`configs/labels/scaleout/path.json`; the observed max registered row count per
label version remained below the per-label row budget, and the all-variant
metadata row count remained below the aggregate path-evaluation budget.

## Aggregate Coverage

| Metric | Count |
| --- | ---: |
| Registered label versions | 672 |
| Registered value rows | 200,973,356 |
| `label_available_ts` null rows | 0 |
| Guard-flagged emitted rows | 0 |

Rows by variant:

| Variant | Rows |
| --- | ---: |
| `mfe` | 50,243,339 |
| `mae` | 50,243,339 |
| `target_before_stop` | 50,243,339 |
| `triple_barrier` | 50,243,339 |

## Horizon Coverage And Overlap Metadata

Effective N is the conservative overlap-aware count
`floor(row_count / horizon_steps)` at one-minute sampling; rows are not claimed
to be independent.

| Horizon | Units | Label versions | Rows | Effective N | Overlap rows | Roll/contract dropped windows | Maintenance dropped windows | Guard-flag rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `5m` | 24 | 96 | 30,148,832 | 6,029,724 | 24,119,108 | 118,047 | 28,335 | 0 |
| `10m` | 24 | 96 | 30,035,012 | 3,003,456 | 27,031,556 | 118,047 | 56,670 | 0 |
| `15m` | 24 | 96 | 29,921,192 | 1,994,696 | 27,926,496 | 118,047 | 85,005 | 0 |
| `30m` | 24 | 96 | 29,579,732 | 985,936 | 28,593,796 | 118,047 | 170,010 | 0 |
| `60m` | 24 | 96 | 28,897,084 | 481,564 | 28,415,520 | 117,979 | 340,020 | 0 |
| `120m` | 24 | 96 | 27,540,712 | 229,460 | 27,311,252 | 115,612 | 680,040 | 0 |
| `240m` | 24 | 96 | 24,850,792 | 103,500 | 24,747,292 | 105,172 | 1,360,080 | 0 |

## Per Symbol-Year Coverage And Guard Counts

Roll-splice and maintenance-crossing policies are `drop`; dropped guard windows
are not emitted as label rows. The drop counts below are value-free window
counts per governed full-window variant surface, summed across horizons for each
symbol-year. `Guard-flag rows` are emitted rows whose quality flags mention a
roll or maintenance guard; the drop policy produced none.

| Symbol | Year | Units | Label versions | Rows | Roll/contract dropped windows | Maintenance dropped windows | Guard-flag rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ES` | 2019 | 7 | 28 | 9,141,940 | 37,399 | 123,360 | 0 |
| `ES` | 2020 | 7 | 28 | 9,141,972 | 37,443 | 123,840 | 0 |
| `ES` | 2021 | 7 | 28 | 9,246,196 | 37,672 | 123,840 | 0 |
| `ES` | 2022 | 7 | 28 | 9,268,332 | 37,910 | 123,360 | 0 |
| `ES` | 2023 | 7 | 28 | 9,241,348 | 37,894 | 123,360 | 0 |
| `ES` | 2024 | 7 | 28 | 9,076,692 | 37,873 | 120,480 | 0 |
| `ES` | 2025 | 7 | 28 | 9,013,692 | 38,024 | 120,000 | 0 |
| `ES` | 2026 | 7 | 28 | 3,703,900 | 9,538 | 48,480 | 0 |
| `NQ` | 2019 | 7 | 28 | 9,150,424 | 37,469 | 123,360 | 0 |
| `NQ` | 2020 | 7 | 28 | 9,123,688 | 37,261 | 123,840 | 0 |
| `NQ` | 2021 | 7 | 28 | 9,246,952 | 37,693 | 123,840 | 0 |
| `NQ` | 2022 | 7 | 28 | 9,268,136 | 37,910 | 123,360 | 0 |
| `NQ` | 2023 | 7 | 28 | 9,247,024 | 37,910 | 123,360 | 0 |
| `NQ` | 2024 | 7 | 28 | 9,080,324 | 37,903 | 120,480 | 0 |
| `NQ` | 2025 | 7 | 28 | 9,012,776 | 38,029 | 120,000 | 0 |
| `NQ` | 2026 | 7 | 28 | 3,703,088 | 9,538 | 48,480 | 0 |
| `RTY` | 2019 | 7 | 28 | 8,571,228 | 35,240 | 123,360 | 0 |
| `RTY` | 2020 | 7 | 28 | 8,824,212 | 36,222 | 123,840 | 0 |
| `RTY` | 2021 | 7 | 28 | 8,875,900 | 35,970 | 123,840 | 0 |
| `RTY` | 2022 | 7 | 28 | 9,022,412 | 36,691 | 123,360 | 0 |
| `RTY` | 2023 | 7 | 28 | 8,946,208 | 36,660 | 123,360 | 0 |
| `RTY` | 2024 | 7 | 28 | 8,710,140 | 36,285 | 120,480 | 0 |
| `RTY` | 2025 | 7 | 28 | 8,710,076 | 36,900 | 120,000 | 0 |
| `RTY` | 2026 | 7 | 28 | 3,646,696 | 9,517 | 48,480 | 0 |

## Registry And Identity Checks

- Required registry fields populated for all current label versions:
  `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, `label_version_id`.
- `value_store_format`: `parquet` for all 672 current
  label versions.
- Producer provenance: `alpha_system.labels.fast.pack_materializer.v1` for all
  672 current label versions.
- Value schema version: `alpha_system.labels.fast.values.v1` for all current
  label versions.
- Label-version identity is partition-scoped by materialization scope
  (`symbol`, `partition_id`, `dataset_version_id`, window, and horizon) and
  does not encode producer provenance.
- The full workers=8 run used checkpoint + registry truth to skip the seven
  bounded real `ES`/`2024` units.
- Machine-reviewable per symbol x year x variant x horizon coverage and per-unit
  guard counts are in `coverage_matrix.json` in this directory.

## Guard Policy

- Roll policy: `roll_cme_index_futures_quarterly`, guard version
  `roll_guard_v1`, policy `drop`, roll window two days before / one day after
  the approximate quarterly roll date.
- Maintenance policy: `cme_index_futures_daily_maintenance_break_v1`, guard
  version `maintenance_crossing_guard_v1`, policy `drop`.
- The fast path reuses the shared guard wiring from fixed-horizon terminal
  resolution; it does not fork roll or maintenance policy code.

## Safety

This phase adds substrate materialization only. It makes no profitability,
tradability, production, live, paper, broker, order-routing, or
capital-allocation claim. Label values, registries, manifests, checkpoints, and
SQLite files remain local-only under `ALPHA_DATA_ROOT`.
