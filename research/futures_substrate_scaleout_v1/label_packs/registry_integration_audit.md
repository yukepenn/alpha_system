# LabelPack Registry Integration Audit

Value-free registry integration audit for `FUTSUB-P22`. This report records
counts, statuses, and metadata presence only. It does not embed label values,
prices, returns, spreads, Parquet payloads, SQLite contents, provider
responses, local file paths, or content hashes.

- Generated: `2026-06-11`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P22`
- Executor status: `READY_FOR_REVIEW_NO_CURRENT_GAPS_FOUND`
- Registry read path: `LabelRegistry.from_alpha_data_root(...).read_label_records()`
- Resolver path: `FeatureLabelPackResolver.resolve_label_packs`
- Current lock source: write-free `alpha scaleout label-pack --dry-run` identity preview
- Current preview locks audited: `1368`
- Current preview locks resolved: `1368`
- Current preview gaps: `0`

## Current Preview Surface

| Surface | Labels / horizons | Expected locks | Active registered locks | Resolver gaps | Dataset states |
| --- | --- | ---: | ---: | ---: | --- |
| `fixed_base` | `1m`, `3m`, `5m`, `10m`, `15m`, `30m` | 144 | 144 | 0 | `ACCEPTED`, `ACCEPTED_WITH_WARNINGS` |
| `fixed_extended` | `60m`, `120m`, `240m` | 72 | 72 | 0 | `ACCEPTED`, `ACCEPTED_WITH_WARNINGS` |
| `close_out` | `session_close`, `maintenance_flat` | 48 | 48 | 0 | `ACCEPTED`, `ACCEPTED_WITH_WARNINGS` |
| `cost_adjusted` | `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 432 | 432 | 0 | `ACCEPTED`, `ACCEPTED_WITH_WARNINGS` |
| `path` | `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | 672 | 672 | 0 | `ACCEPTED`, `ACCEPTED_WITH_WARNINGS` |
| **Total** | all current label locks | **1368** | **1368** | **0** | `ACCEPTED`, `ACCEPTED_WITH_WARNINGS` |

The accepted materialization window is ES/NQ/RTY for 2019 through 2026. Year
2018 remains excluded because its DatasetVersion is `BLOCKED`; 2019 and 2026
are included with warning metadata surfaced.

## Required Registry Fields

All `1368` current preview locks had the required fields populated:

- `value_store_format`
- `parquet_path`
- `value_content_hash`
- `value_schema_version`
- `dataset_version_id`
- `label_version_id`

All current locks had `value_store_format=parquet`, an existing Parquet file,
and a sidecar manifest whose content hash matched the registry
`value_content_hash`. Shared value files are expected for multi-label packs, so
manifest value counts can exceed a single label-version record count; the
content-hash check is the keystone value-store check used here.

DatasetVersion binding matched the dry-run preview for every current lock:
`1368` / `1368` records had the expected `dataset_version_id` and
`partition_id`. The DatasetVersion acceptance states were:

| Surface | `ACCEPTED` locks | `ACCEPTED_WITH_WARNINGS` locks |
| --- | ---: | ---: |
| `fixed_base` | 108 | 36 |
| `fixed_extended` | 54 | 18 |
| `close_out` | 36 | 12 |
| `cost_adjusted` | 324 | 108 |
| `path` | 504 | 168 |

## Availability And Guards

All current preview locks had `first_label_available_ts` and
`last_label_available_ts`; no availability bound preceded the corresponding
event timestamp bound.

All current preview locks carried the expected guard provenance:

- `roll_policy_id=roll_cme_index_futures_quarterly`
- `roll_guard_version=roll_guard_v1`
- `roll_cross_policy=drop`
- `maintenance_policy_id=cme_index_futures_daily_maintenance_break_v1`
- `maintenance_guard_version=maintenance_crossing_guard_v1`
- `maintenance_crossing_policy=drop`

P21 remains the semantic guard audit for roll-splice and maintenance-crossing
window arithmetic; P22 verifies registry-field presence and resolver safety.

## Identity And Producer Provenance

No duplicate current `label_version_id` was observed. Producer engine and value
schema were metadata only and did not enter the current lock matching rule.

| Surface | Producer provenance on current locks | Value schema provenance |
| --- | --- | --- |
| `fixed_base` | 126 V1 fast rows, 18 reference rows | 126 fast value-schema rows, 18 reference value-schema rows |
| `fixed_extended` | 72 reference rows | 72 reference value-schema rows |
| `close_out` | 48 reference rows | 48 reference value-schema rows |
| `cost_adjusted` | 432 reference rows | 432 reference value-schema rows |
| `path` | 672 V1 fast rows | 672 fast value-schema rows |

The mixed fixed-base provenance is expected engine-invariance evidence: 2024
bounded-reference rows and full-grid V1 rows resolve under governed identities
without producer engine entering `label_version_id`.

## Deprecated Rows

The local registry contains `2373` total records: `2324` `REGISTERED` and `49`
`DEPRECATED`.

| Deprecated family | Deprecated records | Current preview ids among deprecated rows |
| --- | ---: | ---: |
| `fixed_horizon` | 1 | 0 |
| `session_close_maintenance_flat` | 48 | 0 |

The `48` repaired close-out stale rows are deprecated and absent from the
current dry-run lock surface. The current close-out preview locks are
`48` / `48` active `REGISTERED` rows and resolve by exact id. Deprecated rows
remain readable through the historical registry API for audit, but they are not
counted as active locks and are not counted as current-surface coverage gaps.
A deprecated exact `label_version_id` supplied directly to the official runtime
resolver fails closed with `label_pack_deprecated`.

Historical inventory note: `956` active cost-adjusted records are outside the
current dry-run preview surface and are bound to BBO DatasetVersion ids from
earlier FUTSUB-P19 runs. They are not duplicate current ids and are not used as
P22 current locks. The current cost-adjusted surface is the `432` OHLCV-bound
dry-run ids above, all of which resolve exactly.

## N_eff / Overlap Evidence Provenance

The coordinator-clarified contract is applied per family:

| Surface | Registry-level `horizon_overlap_metadata` | Report-level evidence used by P22 | Provenance result |
| --- | ---: | --- | --- |
| `fixed_base` | 0 / 144 by design | P22-computed conservative effective counts from current registry row counts; P16 coverage and P21 guard matrices carry row and overlap-window context | report-level |
| `fixed_extended` | 72 / 72 | P17 coverage summary also records extended overlap context | registry-level |
| `close_out` | 0 / 48 by design | P18 coverage summary records effective samples as distinct close-out terminal events | report-level |
| `cost_adjusted` | 0 / 432 by design | P19 coverage summary records horizon rows, effective N, and overlap rows | report-level |
| `path` | 0 / 672 by design | P20 coverage summary and `coverage_matrix.json` record horizon rows, effective N, and overlap rows | report-level |

The fixed-base report-level effective-sample context below is P22-computed. It
uses the same conservative one-minute-grid convention used by the other
coverage reports: `effective = sum(floor(row_count / horizon_minutes))`. It is
value-free and uses registry row counts only.

| Fixed-base horizon | Label versions | Registry rows | Conservative effective count | Overlap rows |
| --- | ---: | ---: | ---: | ---: |
| `1m` | 24 | 7,488,622 | 7,488,622 | 0 |
| `3m` | 24 | 7,470,979 | 2,490,318 | 4,980,661 |
| `5m` | 24 | 7,455,294 | 1,491,049 | 5,964,245 |
| `10m` | 24 | 7,416,879 | 741,677 | 6,675,202 |
| `15m` | 24 | 7,379,178 | 491,934 | 6,887,244 |
| `30m` | 24 | 7,294,349 | 243,133 | 7,051,216 |

Recorded follow-up carried forward, not fixed in P22: the V1 fast
`register_pack` registry-metadata path would not propagate
`horizon_overlap_metadata` if extended horizons ever registered through V1.
That is latent only today because extended horizons register through the
reference engine.

## Explicit Gap List

Unexpected current-surface coverage gaps: none.

Unexpected resolver lifecycle gaps: none found in this executor audit.

Expected exclusions:

- `2018` is excluded because the DatasetVersion is `BLOCKED`.
- `2019` and `2026` are included as `ACCEPTED_WITH_WARNINGS` and surfaced in
  the counts above.
- P21 guard-invalidated roll and maintenance windows remain excluded from
  emitted rows and were not recomputed here.
- P20 path materialization recorded no infeasible units in the current registry
  surface.

## Outcome

The current dry-run identity preview equals the active registry surface for all
representative LabelPack locks audited by P22, and all current locks resolve
through the official resolver to Parquet-backed value-store records with
matching content-hash sidecars. Deprecated rows are excluded from that current
surface and deprecated exact-id probes fail closed. Ralph and the reviewer own
the phase verdict; the executor did not issue one.
