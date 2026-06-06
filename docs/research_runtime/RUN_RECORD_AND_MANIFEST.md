# Study Run Records and Manifests

RT-P05 adds three immutable runtime contract objects under
`alpha_system.runtime.contracts`. They describe what a bounded run produced and
how to reproduce the run's reference state. They do not execute diagnostics,
resolve registries, materialize features or labels, or write runtime data.

## StudyRunRecord

`StudyRunRecord` is the durable outcome record for one bounded run. It stores:

- `run_id`;
- a `StudyRunSpec` reference by id and content hash;
- a legal runtime result state;
- visible rejection reasons for terminal `REJECTED`, `INCONCLUSIVE`, and
  `BLOCKED` outcomes;
- artifact references by id, location, and content hash;
- a `StudyRunManifest` reference by id and hash.

The record does not copy the `StudyRunSpec`, `RuntimePlan`, feature pack, label
pack, or artifact values. It is descriptive evidence only. Terminal failed or
inconclusive outcomes must carry at least one reason, so failed runs are not
hidden as empty records.

The result-state type admits the runtime lifecycle states used by this campaign:
request, input resolution, validated plan, diagnostics, signal probe, cost
stress, evidence draft, reference handoff, and the terminal failure states. It
does not contain promotion, broker, paper, live, deployment, or readiness states.

## StudyRunManifest

`StudyRunManifest` is reproducibility evidence for a run. It binds the run to
reference fields only:

- DatasetVersion id, content hash, lineage reference, and admissibility state
  metadata.
- Feature-pack ids, hashes, lineage references, and `available_ts` metadata
  references.
- Label-pack ids, hashes, lineage references, and `label_available_ts` metadata
  references.
- Code version plus code content hash.
- Config version plus config hash.
- Optional cost-model version plus hash, populated by later phases.

The manifest hash is deterministic and derived from those version and lineage
references. It excludes wall-clock values and run-directory paths. A manifest
missing required version or lineage references is invalid.

## RuntimeArtifactManifest

`RuntimeArtifactManifest` is an ordered artifact ledger. Each entry carries:

- `artifact_id`;
- artifact `kind`;
- relative `location` under the local data root or run artifact area;
- `content_hash`;
- `size_bytes`;
- `local_only`, defaulting to `True`;
- `commit_allowed`, defaulting to `False`.

Heavy or value-bearing outputs, including Parquet, Arrow, Feather, DBN, ZST,
SQLite or DB files, NumPy arrays, feature or label value tables, and raw runtime
values, can never be marked `commit_allowed`. A commit-allowed artifact must be
a tiny curated, row-free summary under the documented size threshold. Entries
under `runs/**`, data cache/raw/canonical/factor/label locations, metadata DB
locations, or generic artifact directories remain local-only.

## Contract Posture

These objects are immutable and hashable. They are contracts, not runtime
operators. Later phases may populate them, but this phase only defines the
reference shape and validation rules. The committed manifest and record surfaces
are row-free reproducibility evidence; value-bearing runtime outputs remain
local-only.
