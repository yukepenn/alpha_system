# Label Coverage And Horizon Quality

`FUTSUB-P23` records the value-free label coverage matrices and horizon-quality
context for the `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` campaign.

This document contains registry statuses, counts, coverage fractions, guard
counts, and overlap provenance only. It contains no per-row label values,
prices, returns, spreads, provider payloads, local SQLite content, Parquet
payloads, local data paths, profitability claim, execution-quality claim,
paper/live/broker/order behavior, or production claim.

## Matrix Summary

The committed matrices are:

- `research/futures_substrate_scaleout_v1/matrices/label_family_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/symbol_horizon_coverage.md`
- `research/futures_substrate_scaleout_v1/matrices/session_horizon_coverage.md`

P23 read the local label registry through
`LabelRegistry.from_alpha_data_root(...).read_label_records()` and counted only
active `REGISTERED` records as coverage. The current surface has `1368` active
locks across the five governed surfaces. The P22 resolver evidence records
`1368` / `1368` current preview locks resolved and `0` current preview gaps.

| Status | Family-symbol-horizon-year cells |
| --- | ---: |
| Present clean (`P`) | 486 |
| Present with warning metadata (`W`) | 162 |
| Expected-excluded (`EE`) | 81 |
| Unexpected gap (`UG`) | 0 |

Coverage is not asserted by subset. The matrix renders 2018 explicitly as an
expected exclusion, renders 2019 and 2026 as warned-but-present, and records no
unexpected accepted-window gap.

## Horizon Quality Report

Coverage fraction is active locks divided by expected active locks for the
2019-2026 accepted or accepted-with-warnings grid. All rows below are
summary metadata only.

| Surface | Horizon | Active / expected locks | Coverage fraction | Warned locks | Registry/report rows | Effective / N_eff context | Overlap rows/context | Provenance |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `fixed_base` | `1m` | 24 / 24 | 1.000 | 6 | 7488622 | 7488622 | 0 | report-level P22 registry-row context |
| `fixed_base` | `3m` | 24 / 24 | 1.000 | 6 | 7470979 | 2490318 | 4980661 | report-level P22 registry-row context |
| `fixed_base` | `5m` | 24 / 24 | 1.000 | 6 | 7455294 | 1491049 | 5964245 | report-level P22 registry-row context |
| `fixed_base` | `10m` | 24 / 24 | 1.000 | 6 | 7416879 | 741677 | 6675202 | report-level P22 registry-row context |
| `fixed_base` | `15m` | 24 / 24 | 1.000 | 6 | 7379178 | 491934 | 6887244 | report-level P22 registry-row context |
| `fixed_base` | `30m` | 24 / 24 | 1.000 | 6 | 7294349 | 243133 | 7051216 | report-level P22 registry-row context |
| `fixed_extended` | `60m` | 24 / 24 | 1.000 | 6 | 7153505 | 119212 | 7034293 | registry-level `horizon_overlap_metadata` plus P17 report |
| `fixed_extended` | `120m` | 24 / 24 | 1.000 | 6 | 6819369 | 56816 | 6762553 | registry-level `horizon_overlap_metadata` plus P17 report |
| `fixed_extended` | `240m` | 24 / 24 | 1.000 | 6 | 6153429 | 25625 | 6127804 | registry-level `horizon_overlap_metadata` plus P17 report |
| `close_out` | `session_close` | 24 / 24 | 1.000 | 6 | 7248193 | terminal-event context | no fixed forward-horizon overlap claim | report-level P18/P21 close-out context |
| `close_out` | `maintenance_flat` | 24 / 24 | 1.000 | 6 | 7552054 | terminal-event context | no fixed forward-horizon overlap claim | report-level P18/P21 close-out context |
| `cost_adjusted` | `1m` | 48 / 48 | 1.000 | 12 | 15133646 | 15133646 | 0 | report-level P19 overlap context |
| `cost_adjusted` | `3m` | 48 / 48 | 1.000 | 12 | 15133808 | 5044596 | 10089212 | report-level P19 overlap context |
| `cost_adjusted` | `5m` | 48 / 48 | 1.000 | 12 | 15134042 | 3026800 | 12107242 | report-level P19 overlap context |
| `cost_adjusted` | `10m` | 48 / 48 | 1.000 | 12 | 15134434 | 1513434 | 13621000 | report-level P19 overlap context |
| `cost_adjusted` | `15m` | 48 / 48 | 1.000 | 12 | 15134752 | 1008970 | 14125782 | report-level P19 overlap context |
| `cost_adjusted` | `30m` | 48 / 48 | 1.000 | 12 | 15134902 | 504483 | 14630419 | report-level P19 overlap context |
| `cost_adjusted` | `60m` | 48 / 48 | 1.000 | 12 | 15134266 | 252226 | 14882040 | report-level P19 overlap context |
| `cost_adjusted` | `120m` | 48 / 48 | 1.000 | 12 | 14667698 | 122221 | 14545477 | report-level P19 overlap context |
| `cost_adjusted` | `240m` | 48 / 48 | 1.000 | 12 | 13657388 | 56892 | 13600496 | report-level P19 overlap context |
| `path` | `5m` | 96 / 96 | 1.000 | 24 | 30148832 | 6029724 | 24119108 | report-level P20 overlap context |
| `path` | `10m` | 96 / 96 | 1.000 | 24 | 30035012 | 3003456 | 27031556 | report-level P20 overlap context |
| `path` | `15m` | 96 / 96 | 1.000 | 24 | 29921192 | 1994696 | 27926496 | report-level P20 overlap context |
| `path` | `30m` | 96 / 96 | 1.000 | 24 | 29579732 | 985936 | 28593796 | report-level P20 overlap context |
| `path` | `60m` | 96 / 96 | 1.000 | 24 | 28897084 | 481564 | 28415520 | report-level P20 overlap context |
| `path` | `120m` | 96 / 96 | 1.000 | 24 | 27540712 | 229460 | 27311252 | report-level P20 overlap context |
| `path` | `240m` | 96 / 96 | 1.000 | 24 | 24850792 | 103500 | 24747292 | report-level P20 overlap context |

Rows are not independent samples for overlapping horizons. The effective/N_eff
entries above are provenance records from P17/P19/P20/P22 reports or
registry-level metadata; P23 does not introduce a new N_eff engine. The
overlap-aware runtime reporting work remains owned by `FUTSUB-P25`.

## Guard Context

P21 remains the semantic guard audit. P23 consumes its summary counts rather
than recomputing guard arithmetic.

| Surface | Roll-overlap dropped | Maintenance-overlap dropped | Close-out boundary drops | Truncated | Flagged | Invalid | Silently measured |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixed_base` | 708172 | 353333 | 0 | 0 | 0 | 0 | 0 |
| `fixed_extended` | 334684 | 986770 | 0 | 0 | 0 | 0 | 0 |
| `close_out` | 247167 | 0 | 320006 | 0 | 0 | 0 | 0 |
| `cost_adjusted` | 2096436 | 5187270 | 0 | 0 | 0 | 0 | 0 |
| `path` | 810951 | 2720160 | 0 | 0 | 0 | 0 | 0 |

The P21 matrices record zero silently measured roll-splice or daily
maintenance / trade-date break crossings. Guard-dropped windows are expected
exclusions from emitted rows, not resolver gaps.

## Overlap Provenance

| Surface | Overlap / N_eff provenance |
| --- | --- |
| `fixed_base` | Report-level context from P22 using registry row counts; registry-level `horizon_overlap_metadata` is absent by family design for base horizons. |
| `fixed_extended` | Registry-level `contract_metadata.horizon_overlap_metadata` exists for extended fixed-horizon records, with P17 report-level rows and effective-count context. |
| `close_out` | Report-level terminal-event context from P18/P21; no fixed forward-horizon overlap claim is made. |
| `cost_adjusted` | Report-level horizon rows, effective N, and overlap rows from P19. |
| `path` | Report-level horizon rows, effective N, overlap rows, and feasibility/budget context from P20 and `coverage_matrix.json`. |

Neither provenance source is promoted beyond what it records. Extended fixed
horizons cite registry-level metadata; the other families cite committed
report-level evidence.

## Explicit Gap List

Expected exclusions:

- All 2018 label-family cells are expected exclusions because the DatasetVersion
  is `BLOCKED`.
- RTY-2018 is the binding sparse-history coverage issue; ES/NQ 2018 are also
  excluded under the campaign dataset-level fallback.
- 2026 is partial-year and resolved with warning metadata, not treated as a
  clean full-year cell.
- P20 recorded `0` path infeasible units, so there are no path feasibility
  exclusions in the current surface.

Unexpected gaps:

- None. The P23 matrix found `0` unexpected accepted-window family / horizon /
  instrument / year gaps.

## Downstream Consumption

- `FUTSUB-P24` opens walk-forward wiring with the coverage map above as the
  label substrate availability surface.
- `FUTSUB-P25` owns overlap-aware N_eff reporting and must preserve the
  rows-versus-effective-samples distinction.
- `FUTSUB-P27` through `FUTSUB-P29` must not accept the substrate as complete by
  subset. Any future missing active lock is a gap to route to the owning
  materialization or integration phase, not something to fill in P23.
