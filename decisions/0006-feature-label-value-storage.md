# ADR-0006: Feature And Label Value Storage Tiers

## Status

Accepted for the Feature/Label + Research Runtime baseline.

## Context

[ADR-0001](0001-local-first-stack.md) sets the local-first stack: "large
datasets" are local Parquet, SQLite is the metadata/registry source of truth,
DuckDB queries Parquet, and Polars/NumPy/Numba serve pipelines and hot loops.
That decision is realized in the data foundation: canonical OHLCV/BBO bars are
written as Hive-partitioned Parquet (`schema=.../root=<sym>/part-*.parquet`) and
read through optional, dependency-guarded `pyarrow`/`polars`/`duckdb` paths while
core `dependencies` stay empty.

The Feature/Label Foundation diverged for *value* payloads: feature and label
materialization writes deterministic **JSONL** (`values.jsonl`) under
`ALPHA_DATA_ROOT`, and the `features.sqlite` / `labels.sqlite` registries store
**metadata only** (counts, `event_ts`/`available_ts`/`label_available_ts`
ranges, a value-path pointer, lineage, exposure, deprecation) — never the value
payloads. ADR-0001's "large datasets as Parquet" was never tied to feature,
label, or factor value matrices, and no ADR reconciled the JSONL value store
with the Parquet intent. The docs neither labelled JSONL an MVP placeholder nor
named a Parquet successor. This left an unflagged architecture question:
*is JSONL the permanent research store, or an audit/MVP tier?*

A second, related coupling gap surfaced while wiring the first real seed packs:
the dataset registry (`datasets.sqlite`) persists only the quality/coverage
**hashes** of an accepted `DatasetVersion`, not the report objects. Because
`DatasetVersion.require_versioned_prerequisites` demands a `DataQualityReport`
that reproduces the stored hash, an accepted DatasetVersion cannot be
re-resolved for downstream feature/label materialization without re-supplying
its original reports, which are not stored.

## Decision

Adopt an explicit two-tier value-storage policy for feature, label, and factor
**values**. SQLite registries remain metadata/pointer only and never store value
payloads.

1. **Audit / small tier — JSONL (current).** Deterministic, atomic, idempotent
   `values.jsonl` under `ALPHA_DATA_ROOT` is the sanctioned format for tiny
   synthetic fixtures, deterministic audit/debug output, MVP smoke runs, and
   small seed packs. It is the only tier implemented today and is acceptable for
   those uses. JSONL is **not** the permanent large-scale research store.

2. **Research-scale tier — Parquet (intended, deferred).** Multi-year,
   multi-symbol feature/label value matrices intended for repeated columnar
   scans must be stored as local Parquet under `ALPHA_DATA_ROOT`, read through
   DuckDB/Polars, consistent with ADR-0001. This tier is **not** implemented in
   this baseline. It is scoped to a dedicated follow-up,
   `FEATURE_LABEL_PARQUET_SINK_V1`, which must: write Parquet through the
   existing optional-dependency pattern; record a `parquet_path` pointer
   (alongside the optional `jsonl_path`), `value_count`, content hash, and
   schema version in the registries; generalize the JSONL-only reader gate in
   `features/reports.py`; and ship synthetic-fixture tests. It should land
   before any large-scale, value-consuming Agent Factory study.

3. **Registry/value boundary (unchanged, restated).** `features.sqlite`,
   `labels.sqlite`, and `datasets.sqlite` are local-only metadata registries.
   They record paths, hashes, counts, timestamp ranges, lineage, exposure, and
   status — never value payloads, raw/canonical data, or Parquet/Arrow/Feather
   blobs. Value and registry files are never committed.

4. **Dataset acceptance evidence (coupling gap, follow-up).** Until a follow-up
   persists or re-derives dataset quality/coverage reports, governed seed
   materialization may derive and run the real quality/coverage builders over
   exactly the partition being materialized and construct the consumption
   handle directly, rather than resolving the stored full-dataset hash. A
   follow-up should let an accepted `DatasetVersion` be re-resolved with its
   reports (persist reports, or add a `load_accepted_dataset_version` /
   report re-derivation helper).

## Consequences

JSONL stays correct for the current scope: the Research Runtime resolver is
value-free (it reads registry metadata and never opens value files), so the
real-data runtime smoke and Agent Factory *wiring* do not depend on the value
format. The Parquet tier becomes required only when an actual value-consuming,
research-scale study arrives — at which point `FEATURE_LABEL_PARQUET_SINK_V1`
must be delivered. Recording the policy here prevents JSONL from silently
becoming the de-facto permanent store and gives the registries a forward-
compatible place for a `parquet_path` pointer. The dataset-acceptance coupling
gap is documented so the follow-up is explicit rather than discovered again.

This ADR records policy and follow-ups. It does not, by itself, implement the
Parquet sink or change the dataset registry schema.
