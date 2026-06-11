# LabelPack Integration

`FUTSUB-P22` audits the integrated label registry and resolver-smoke contract
for the futures substrate scaleout LabelPacks. This document is value-free: it
records registry and resolver evidence only and does not embed label values,
Parquet payloads, SQLite contents, provider responses, local run artifacts, or
content hashes.

## Integrated Surfaces

The audited current label surfaces are:

- fixed-horizon diagnostic and primary labels: `1m`, `3m`, `5m`, `10m`,
  `15m`, and `30m`;
- extended fixed-horizon labels: `60m`, `120m`, and `240m`;
- close-out labels: `session_close` and `maintenance_flat`;
- cost-adjusted labels: `cost_adjusted_fwd_ret` and
  `spread_adjusted_fwd_ret`;
- path labels: `mfe`, `mae`, `target_before_stop`, and `triple_barrier`.

The accepted window spans ES/NQ/RTY for 2019 through 2026. Year 2018 is
excluded because its DatasetVersion is `BLOCKED`; 2019 and 2026 are included
with `ACCEPTED_WITH_WARNINGS` metadata surfaced.

## Resolver Contract

Runtime label locks resolve by exact `lver_...` id through
`FeatureLabelPackResolver.resolve_label_packs`. The resolver-smoke uses the
write-free scaleout dry-run preview as the current lock source, then requires
each preview lock to:

- resolve by exact `label_version_id`;
- match the expected DatasetVersion and partition;
- carry required value-store metadata;
- point to a current Parquet sidecar with matching content hash;
- preserve `label_available_ts` ordering;
- carry roll and maintenance guard provenance.

The fail-closed fixture probes cover absent exact ids, mutated exact ids, fuzzy
label names, and deprecated exact ids. No fuzzy fallback, unit-id fallback,
substitution, deprecated lifecycle fallback, or fabricated value is accepted.

## Current Evidence

The current P22 executor evidence is:

- `1368` / `1368` current dry-run preview locks resolve.
- Required registry fields are populated for every current lock.
- `label_available_ts` bounds and guard provenance are present for every
  current lock.
- DatasetVersion ids match the current dry-run units and point to accepted or
  accepted-with-warnings DatasetVersions.
- No current `label_version_id` collision is present.
- `49` deprecated registry rows are excluded from the current lock surface:
  `48` repaired close-out stale rows and `1` fixed-horizon duplicate.
- Unexpected current-surface coverage gaps: none.
- Deprecated exact-id refs fail closed with `label_pack_deprecated`.
- Unexpected resolver lifecycle gaps: none found in this executor audit.

Ralph and the reviewer own the phase verdict; this executor snapshot does not
create a review, verdict, PR, merge, or phase-pass decision.

Detailed evidence is recorded in:

- `research/futures_substrate_scaleout_v1/label_packs/registry_integration_audit.md`
- `research/futures_substrate_scaleout_v1/label_packs/label_resolver_smoke.md`
- `tests/unit/futures_substrate_scaleout/labels/test_label_resolver_smoke.py`

## N_eff / Overlap Contract

The coordinator-clarified P22 contract is per-family:

- extended fixed-horizon records carry registry-level
  `contract_metadata.horizon_overlap_metadata`;
- fixed-base, close-out, cost-adjusted, and path labels carry overlap or
  effective-sample context in committed value-free reports rather than in
  registry-level metadata.

P22 records the provenance explicitly and does not require registry-level
metadata where the family design places evidence in reports. The latent
follow-up remains unchanged: before any V1 extended-horizon registration, the
V1 `register_pack` registry-metadata path must propagate
`horizon_overlap_metadata`.

## Boundaries

This phase did not materialize new values, write registry rows, re-run
diagnostics, change label-family code, create StudySpecs, issue alpha claims,
or touch broker/live/paper/order/deployment behavior. Values, manifests,
registries, checkpoints, roll-calendar data, and heavy artifacts remain
local-only under `ALPHA_DATA_ROOT`.
