# DatasetVersion Entry Guide

Feature/Label workflows begin with accepted DatasetVersions. They do not begin
with Databento files, IBKR responses, parquet, arrow, feather, local registry
SQL, or ad hoc data files.

## Single Sanctioned Path

Use the Feature/Label consumption adapter described in
`../ENTRY_CONTRACT_CONSUMPTION.md`:

```python
from alpha_system.features.consumption import resolve_accepted_dataset_version
```

The adapter wraps:

```text
alpha_system.data.foundation.version_registry.resolve_dataset_version(...)
```

It returns one accepted handle for one DatasetVersion provenance line. Databento
and IBKR DatasetVersions remain separate handles and must not be merged into a
single input source.

## Admissible DatasetVersions

A DatasetVersion is consumable only when the resolved registry metadata shows:

- lifecycle state `VERSIONED` or `READY_FOR_RESEARCH`;
- non-blocking quality evidence;
- non-blocking coverage evidence linked to the same quality report;
- matching manifest, code, config, and quality-report hashes;
- required governance contamination metadata for locked-test or latest-shadow
  use outside QA.

Missing, malformed, unresolved, or inadmissible DatasetVersions block the path.

## Canonical Loaders

After resolution, reconstruct rows only through canonical record loaders:

- `CanonicalBarRecord.from_mapping` for sparse OHLCV trade truth.
- `CanonicalBBORecord.from_mapping` for BBO records with quote invariants.
- `DenseGridBarRecord.from_mapping` for derived dense research grids.

Every reconstructed row must bind back to the accepted DatasetVersion id. The
loader path rejects unsupported provider-shaped fields and preserves the
availability fields used by feature and label contracts.

## Timestamp Use

Feature usability keys off `available_ts`. Do not use `event_ts`,
`ingested_at`, provider timestamps, file timestamps, or row order as a proxy for
availability.

Label usability keys off `label_available_ts`. Forward observations can be used
inside a governed label horizon only after the label contract declares the
availability policy and the emitted value carries `label_available_ts`.

## Local-Only Data Posture

The default DatasetVersion registry path is local-only under:

```text
$ALPHA_DATA_ROOT/registry/datasets.sqlite
```

Materialized feature values, materialized label values, local registry DBs,
raw/canonical data, logs, caches, report bundles, and heavy artifacts are not
committed. Repository files describe contracts, docs, templates, tests, source,
handoffs, and review artifacts only.

## Block Conditions

Stop the workflow when any of these appears:

- a request to read raw Databento DBN/Zstd, IBKR responses, parquet, arrow,
  feather, raw/canonical directories, or provider payloads directly;
- an attempt to construct feature or label rows without an accepted
  DatasetVersion handle;
- a feature value without `available_ts`;
- a label value without `label_available_ts`;
- missing locked-test contamination metadata;
- a request that treats a feature, label, store record, or diagnostic as a
  trading or result claim.
