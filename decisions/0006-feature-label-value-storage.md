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

2. **Research-scale tier — Parquet (implemented).** Multi-year,
   multi-symbol feature/label value matrices intended for repeated columnar
   scans are stored as local Parquet under `ALPHA_DATA_ROOT`, read through
   Polars, consistent with ADR-0001. This tier was **implemented** by
   `FEATURE_LABEL_PARQUET_SINK_V1` (in `PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1`):
   a shared `core/value_store.py` abstraction (`ValueStoreFormat`
   = jsonl|parquet|dual, `ValueStoreHandle`, Polars-guarded `write_parquet_values`
   / `load_parquet_values`, format-agnostic content hash, sidecar
   `values.parquet.manifest.json` for idempotency) writes Parquet through the
   existing optional-dependency guard; the `features.sqlite` / `labels.sqlite`
   registries record `parquet_path`, `value_store_format`, `value_content_hash`,
   and `value_schema_version` alongside the existing path/count/timestamp
   metadata (added by idempotent `ALTER TABLE` backfill, backward compatible with
   old JSONL-only rows); `features/reports.py` resolves Parquet or JSONL through
   the registry handle and fails closed otherwise; and the operator exposes
   `feature|label materialize --value-store {jsonl,parquet,dual}` (default
   `dual`). The low-level `materialize_*` API still defaults to JSONL for the
   audit/small tier and test substrate. Synthetic-fixture tests
   (polars-guarded) plus a real local seed smoke cover the sink.

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

This ADR records policy and follow-ups. The Parquet sink (item 2) is now
implemented by `FEATURE_LABEL_PARQUET_SINK_V1`; the dataset-acceptance coupling
gap (item 4) remains an open follow-up.
