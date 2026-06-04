# DATA-P17 Dataset Version Registry Integration

`DatasetVersion` is the reproducibility record for a canonical dataset after
quality and coverage checks. It binds the dataset identity, source manifest,
code, config, and quality report hashes needed to reproduce and audit the
dataset version.

The record is a data-admissibility object only. It does not imply research
approval, alpha value, tradability, broker readiness, paper trading, live
trading, or production readiness.

## Required Fields

`DatasetVersion` has exactly these fields:

- `dataset_version_id`
- `source`
- `symbol_universe`
- `bar_size`
- `what_to_show`
- `start_ts`
- `end_ts`
- `contract_universe`
- `roll_policy_id`
- `manifest_hash`
- `code_hash`
- `config_hash`
- `quality_report_hash`
- `created_at`

Construction is fail-closed. Missing fields, extra fields, blank identifiers,
malformed identifiers, non-timezone-aware timestamps, reversed dataset windows,
empty symbol or contract universes, duplicate universe members, and malformed
SHA-256 hashes raise `DataFoundationValidationError`.

## Reproducibility Binding

The required hash set is:

- `manifest_hash`: the source manifest content hash.
- `code_hash`: the code hash for the dataset construction path.
- `config_hash`: the configuration hash for the dataset construction inputs.
- `quality_report_hash`: the deterministic hash of the linked
  `DataQualityReport`.

`compute_quality_report_hash(...)` computes the quality report hash that a
dataset version must carry. The lifecycle gate recomputes this hash from the
linked `DataQualityReport`, checks the linked `CoverageReport` for the same
`dataset_version_id`, and requires a source manifest object or mapping that
exposes the same `manifest_hash`. The gate also compares caller-supplied code
and config hashes to the stored `code_hash` and `config_hash`.

## Lifecycle Gate

`DatasetVersion.require_lifecycle_prerequisites(...)` is the local gate for
`VERSIONED` and `READY_FOR_RESEARCH` data admissibility. It requires:

- a non-blocking `DataQualityReport` for the same `dataset_version_id`;
- a non-blocking `CoverageReport` for the same `dataset_version_id`;
- successful coverage-to-quality linkage via
  `CoverageReport.require_linked_quality_report(...)`;
- a source manifest exposing `manifest_hash`;
- caller-supplied code and config hashes;
- exact binding between the dataset version's stored hashes and the linked
  report, manifest, code hash, and config hash.

Missing reports, blocking reports, mismatched dataset IDs, missing source
manifest references, or mis-bound hashes raise `DataFoundationValidationError`.
Silent gaps or incomplete chunks remain blocking because the coverage report
cannot satisfy the gate when it is `BLOCKING`.

## Registry Integration

`alpha_system.data.foundation.version_registry` persists and resolves dataset
versions through the existing local SQLite metadata registry:

- `persist_dataset_version(registry_path, dataset_version, quality_report=...,
  coverage_report=..., source_manifest=..., code_hash=..., config_hash=...)`
- `resolve_dataset_version(registry_path, dataset_version_id)`

The adapter calls `core.registry.init_registry(...)` and
`core.registry.connect_registry(...)`; it does not open an ad-hoc database. It
requires the same lifecycle prerequisites before writing a registry row. It
uses the existing `dataset_versions` table at schema version 1:

- `data_version` stores `DatasetVersion.dataset_version_id`;
- `created_at` stores the dataset version timestamp;
- `source_uri` stores the source ID;
- `content_hash` stores `manifest_hash`;
- `config_hash` stores `config_hash`;
- `metadata_json` stores the complete DATA-P17 object and adapter schema marker.

On resolve, the adapter reconstructs `DatasetVersion` from `metadata_json` and
checks that the table columns are still bound to the same object. Duplicate
`dataset_version_id` writes are rejected with no overwrite.

No registry migration was required for DATA-P17 because the existing table can
store the full object losslessly in `metadata_json`.

## Local-Only DB Policy

The registry database is local-only metadata. It must not be committed.
Integration tests use temporary databases under `tmp_path`; they do not write
to the repository `metadata/` directory.

The adapter refuses paths that fail the existing local-only registry path guard,
including unsupported suffixes and known synced/nonlocal locations. Repository
artifact audits must continue to show no committed SQLite, DB, journal, WAL,
raw, canonical, provider-response, cache, or heavy data artifacts.
