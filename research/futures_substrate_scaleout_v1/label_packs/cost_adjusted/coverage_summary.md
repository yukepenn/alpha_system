# FUTSUB-P19 cost_adjusted LabelPack Coverage Summary

Value-free evidence only. This report contains no per-row label values, prices,
returns, provider responses, local Parquet paths, content hashes, SQLite
content, or checkpoint payloads.

- Generated: `2026-06-11`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P19`
- Family: `cost_adjusted`
- Status: `materialized_registered`
- Engine: `reference`
- Worker configuration: requested `8`, effective `8`, threads per worker `2`
- Thread caps used: `ALPHA_LABEL_CPU_WORKERS=8`, `POLARS_MAX_THREADS=2`,
  `OMP_NUM_THREADS=2`, `RAYON_NUM_THREADS=2`, `NUMBA_NUM_THREADS=2`
- Registry writes: parent-only serial
- Force recompute: `false`

## Resume Accounting

The current run first validated `ES` / `2024` with the reference engine at
`workers=1`, then resumed the full accepted grid with `--engine reference
--workers 8`.

| Run | Completed | Skipped | Failed | Notes |
| --- | ---: | ---: | ---: | --- |
| bounded serial `ES`/`2024` | 9 | 0 | 0 | current partition-scoped identity validation |
| full accepted grid, workers=8 | 207 | 9 | 0 | skipped the bounded serial units from checkpoint + registry truth |
| current registry/ledger truth | 216 | 0 remaining | 0 | 432 label versions resolve with required metadata |

The prior unscoped P19 checkpoint progress was superseded because
cost-adjusted label-version identity was not partition-scoped. Current
completed units are keyed by symbol/year/horizon materialization scope and were
validated against current dry-run preview label-version ids.

## Materialization Window

- Included years: `2019` through `2026`.
- Excluded year: `2018`, because the DatasetVersion is `BLOCKED`; see
  `research/futures_substrate_scaleout_v1/dataset_acceptance/2018_BLOCKED_DIAGNOSIS.md`.
- Eligible states: `ACCEPTED` and `ACCEPTED_WITH_WARNINGS`.
- Accepted unit states: `162` `ACCEPTED`, `54` `ACCEPTED_WITH_WARNINGS`.
- 2019 warning metadata and 2026 partial-year warning metadata are preserved
  through the DatasetVersion state.

## Cost And Proxy Assumptions

- Label cost model version: `cost_adjusted_reference_v1`.
- `cost_adjusted_fwd_ret`: existing governed `spread_plus_bps` model,
  `fixed_cost_bps=0.25`, `spread_adjustment=half_spread_round_trip`.
- `spread_adjusted_fwd_ret`: existing governed `spread_adjusted` model,
  `fixed_cost_bps=0`, `spread_adjustment=half_spread_round_trip`.
- Mid-to-mid is the internal BBO gross forward-return terminal used before
  subtracting governed cost components; it is not emitted as a separate P19
  label id.
- Slippage-stress-adjusted output is not supported by the current sanctioned
  `cost_adjusted` label contract and was not fabricated.
- Sanctioned cost context is recorded in
  `configs/labels/scaleout/cost_adjusted.json`: `default_conservative` and
  `spread_sensitive_conservative`, both `engine_version=reference_1min_v1`.

BBO-1m spreads are a time-sampled, forward-filled tradability proxy only, not
execution truth. Missing, bad-quote, wide-spread, duplicate-key, entry-gap, and
terminal-gap conditions are surfaced as label gap metadata and are never
silently substituted.

## Aggregate Coverage

| Metric | Count |
| --- | ---: |
| Current completed units | 216 |
| Current label versions | 432 |
| Label rows scanned for metadata | 134264936 |
| `label_available_ts` null rows | 0 |
| Gap rows (`label_gap`) | 5045570 |
| Missing terminal BBO rows | 5001728 |
| Entry BBO gap rows | 22322 |
| Terminal BBO gap rows | 21520 |
| Missing BBO rows surfaced in gap flags | 43842 |
| Guard-flagged emitted rows | 0 |

The roll-splice and maintenance-crossing policies are `drop`; dropped guard
windows are not emitted as label rows. The focused synthetic test covers both
drop paths, and the materialized outputs contain no emitted guard-flag rows.
The dedicated FUTSUB-P21 guard audit owns the full guard matrix.

## Per Symbol-Year Coverage

| Symbol | Year | Units | Rows | Gap rows | `label_available_ts` nulls | Guard-flag rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `ES` | 2019 | 9 | 6113172 | 200134 | 0 | 0 |
| `ES` | 2020 | 9 | 6113008 | 217754 | 0 | 0 |
| `ES` | 2021 | 9 | 6172906 | 173806 | 0 | 0 |
| `ES` | 2022 | 9 | 6180746 | 154598 | 0 | 0 |
| `ES` | 2023 | 9 | 6164198 | 162772 | 0 | 0 |
| `ES` | 2024 | 9 | 6052280 | 154202 | 0 | 0 |
| `ES` | 2025 | 9 | 6010920 | 151734 | 0 | 0 |
| `ES` | 2026 | 9 | 2468508 | 60388 | 0 | 0 |
| `NQ` | 2019 | 9 | 6118422 | 194694 | 0 | 0 |
| `NQ` | 2020 | 9 | 6101606 | 215114 | 0 | 0 |
| `NQ` | 2021 | 9 | 6173400 | 173304 | 0 | 0 |
| `NQ` | 2022 | 9 | 6180624 | 154714 | 0 | 0 |
| `NQ` | 2023 | 9 | 6167660 | 159262 | 0 | 0 |
| `NQ` | 2024 | 9 | 6054474 | 151896 | 0 | 0 |
| `NQ` | 2025 | 9 | 6010358 | 152376 | 0 | 0 |
| `NQ` | 2026 | 9 | 2468030 | 60822 | 0 | 0 |
| `RTY` | 2019 | 9 | 5761290 | 473410 | 0 | 0 |
| `RTY` | 2020 | 9 | 5914814 | 344232 | 0 | 0 |
| `RTY` | 2021 | 9 | 5943880 | 363096 | 0 | 0 |
| `RTY` | 2022 | 9 | 6029306 | 286440 | 0 | 0 |
| `RTY` | 2023 | 9 | 5983456 | 312256 | 0 | 0 |
| `RTY` | 2024 | 9 | 5826178 | 333322 | 0 | 0 |
| `RTY` | 2025 | 9 | 5822506 | 304228 | 0 | 0 |
| `RTY` | 2026 | 9 | 2433194 | 91016 | 0 | 0 |

## Horizon Coverage And Overlap Metadata

Effective N is the conservative overlap-aware count
`floor(row_count / horizon_minutes)` at one-minute sampling; rows are not
claimed to be independent.

| Horizon | Units | Rows | Gap rows | Effective N | Overlap rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| `1m` | 24 | 15133646 | 161658 | 15133646 | 0 |
| `3m` | 24 | 15133808 | 196880 | 5044596 | 10089212 |
| `5m` | 24 | 15134042 | 228480 | 3026800 | 12107242 |
| `10m` | 24 | 15134434 | 305632 | 1513434 | 13621000 |
| `15m` | 24 | 15134752 | 381342 | 1008970 | 14125782 |
| `30m` | 24 | 15134902 | 551114 | 504483 | 14630419 |
| `60m` | 24 | 15134266 | 832110 | 252226 | 14882040 |
| `120m` | 24 | 14667698 | 1033582 | 122221 | 14545477 |
| `240m` | 24 | 13657388 | 1354772 | 56892 | 13600496 |

## Registry And Identity Checks

- Required registry fields populated for all current label versions:
  `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `dataset_version_id`, `label_version_id`.
- `value_store_format`: `parquet` for all 432 current label versions.
- Producer provenance: `alpha_system.labels.reference_engine.v1` for all 432
  current label versions.
- Label-version identity is partition-scoped by materialization scope
  (`symbol`, `partition_id`, `dataset_version_id`, window, and horizon) and
  does not encode producer provenance.
- The full workers=8 run used checkpoint + registry truth to skip the 9
  bounded serial `ES`/`2024` units.
