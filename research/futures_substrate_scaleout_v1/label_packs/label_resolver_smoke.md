# Label Resolver Smoke

Value-free resolver smoke for `FUTSUB-P22`. It records current dry-run lock
resolution through the official runtime resolver and closed-failure probes. It
does not embed label values, prices, returns, spreads, Parquet payloads, SQLite
contents, provider responses, local paths, or content hashes.

- Generated: `2026-06-11`
- Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
- Phase: `FUTSUB-P22`
- Resolver: `alpha_system.runtime.input_resolver.FeatureLabelPackResolver.resolve_label_packs`
- Current lock source: write-free scaleout dry-run identity preview
- Current preview locks audited: `1368`
- Current preview locks resolved: `1368`
- Current preview gaps: `0`
- Current preview ids with state `REGISTERED`: `1368`
- Deprecated registry ids in the current preview surface: `0`

## Horizon / Label Matrix

| Surface | Horizon / label | Expected locks | Resolved | Gap |
| --- | --- | ---: | ---: | ---: |
| `fixed_base` | `1m` | 24 | 24 | 0 |
| `fixed_base` | `3m` | 24 | 24 | 0 |
| `fixed_base` | `5m` | 24 | 24 | 0 |
| `fixed_base` | `10m` | 24 | 24 | 0 |
| `fixed_base` | `15m` | 24 | 24 | 0 |
| `fixed_base` | `30m` | 24 | 24 | 0 |
| `fixed_extended` | `60m` | 24 | 24 | 0 |
| `fixed_extended` | `120m` | 24 | 24 | 0 |
| `fixed_extended` | `240m` | 24 | 24 | 0 |
| `close_out` | `maintenance_flat` | 24 | 24 | 0 |
| `close_out` | `session_close` | 24 | 24 | 0 |
| `cost_adjusted` | `1m` | 48 | 48 | 0 |
| `cost_adjusted` | `3m` | 48 | 48 | 0 |
| `cost_adjusted` | `5m` | 48 | 48 | 0 |
| `cost_adjusted` | `10m` | 48 | 48 | 0 |
| `cost_adjusted` | `15m` | 48 | 48 | 0 |
| `cost_adjusted` | `30m` | 48 | 48 | 0 |
| `cost_adjusted` | `60m` | 48 | 48 | 0 |
| `cost_adjusted` | `120m` | 48 | 48 | 0 |
| `cost_adjusted` | `240m` | 48 | 48 | 0 |
| `path` | `5m` | 96 | 96 | 0 |
| `path` | `10m` | 96 | 96 | 0 |
| `path` | `15m` | 96 | 96 | 0 |
| `path` | `30m` | 96 | 96 | 0 |
| `path` | `60m` | 96 | 96 | 0 |
| `path` | `120m` | 96 | 96 | 0 |
| `path` | `240m` | 96 | 96 | 0 |

## Symbol / Year Coverage

Each row below covers the accepted years `2019,2020,2021,2022,2023,2024,2025,2026`.
Warned-year locks are from `2019` and `2026`; they resolve and keep their
warning state visible.

| Surface | Symbol | Expected locks | Resolved | Gap | Warned-year locks |
| --- | --- | ---: | ---: | ---: | ---: |
| `fixed_base` | `ES` | 48 | 48 | 0 | 12 |
| `fixed_base` | `NQ` | 48 | 48 | 0 | 12 |
| `fixed_base` | `RTY` | 48 | 48 | 0 | 12 |
| `fixed_extended` | `ES` | 24 | 24 | 0 | 6 |
| `fixed_extended` | `NQ` | 24 | 24 | 0 | 6 |
| `fixed_extended` | `RTY` | 24 | 24 | 0 | 6 |
| `close_out` | `ES` | 16 | 16 | 0 | 4 |
| `close_out` | `NQ` | 16 | 16 | 0 | 4 |
| `close_out` | `RTY` | 16 | 16 | 0 | 4 |
| `cost_adjusted` | `ES` | 144 | 144 | 0 | 36 |
| `cost_adjusted` | `NQ` | 144 | 144 | 0 | 36 |
| `cost_adjusted` | `RTY` | 144 | 144 | 0 | 36 |
| `path` | `ES` | 224 | 224 | 0 | 56 |
| `path` | `NQ` | 224 | 224 | 0 | 56 |
| `path` | `RTY` | 224 | 224 | 0 | 56 |

## Keystone Chain Checks

For every current dry-run lock:

- exact `label_version_id` resolved through `FeatureLabelPackResolver`;
- resolved `dataset_version_id` matched the dry-run unit DatasetVersion;
- resolved `partition_id` matched the dry-run unit partition;
- resolved label spec id matched the expected governed label spec id;
- the registry row had required value-store metadata;
- the Parquet file existed and its sidecar content hash matched the registry
  `value_content_hash`;
- `label_available_ts` bounds were populated and did not precede event bounds;
- registry lifecycle state was `REGISTERED`.

No current lock used unit-id fallback, label-name fallback, fuzzy matching,
substitution, or fabricated values.

## Negative-Probe Result

The absent, mutated, fuzzy-name, and deprecated exact-id probes were simulated
without mutating the real registry. The deprecated probe uses a synthetic
registry that returns a `DEPRECATED` record to the production runtime resolver.

| Probe | Method | Result |
| --- | --- | --- |
| Absent exact id | synthetic empty registry | `label_pack_not_found` |
| Mutated exact id | synthetic registry containing only the valid id | `label_pack_not_found` |
| Fuzzy label name | synthetic registry containing only the valid id | `invalid_label_pack_ref` |
| Deprecated exact id | synthetic registry returns a `DEPRECATED` record | `label_pack_deprecated` |

The real registry contains `49` deprecated rows (`48` close-out stale rows from
the repair and `1` fixed-horizon duplicate). None are present in the current
preview lock source. Supplying a deprecated exact id directly to the official
resolver fails closed with `label_pack_deprecated`.

## Explicit Gap List

Unexpected current-surface coverage gaps: none.

Unexpected resolver lifecycle gaps: none found in this executor audit.

Expected exclusions:

- `2018` is excluded because its DatasetVersion is `BLOCKED`.
- `2019` and `2026` are included with `ACCEPTED_WITH_WARNINGS` metadata.
- P21 guard-invalidated roll-splice and maintenance-crossing windows remain
  omitted from emitted rows and were not recomputed here.
- No P20 path unit is classified as infeasible in the current registry surface.

## Outcome

All required current label locks spanning fixed-base, extended fixed-horizon,
close-out, cost-adjusted, and path LabelPacks across ES/NQ/RTY and accepted
years resolve by exact id through the official runtime resolver. Absent,
mutated, fuzzy-name, and deprecated exact-id refs fail closed in the current
resolver-smoke probe. Ralph and the reviewer own the phase verdict; the
executor did not create a review, verdict, PR, merge, or phase-pass decision.
