# Keystone Identity Contract

`FUTSUB-P04` preflights the value-store and registry identity path used by the
futures substrate scaleout campaign. The invariant is:

```text
dry-run preview -> executed materialization -> value-store handle
  -> registry record -> StudySpec lock -> runtime resolver handle
```

For materialized values, the registry metadata must carry:

- `value_store_format`
- `parquet_path`
- `value_content_hash`
- `value_schema_version`
- `dataset_version_id`
- `feature_version_id` for feature records or `label_version_id` for label records

Feature and label registries are metadata stores only. They may hold local-only
Parquet paths and content hashes, but they must not copy feature or label values
into SQLite. Runtime input packs stay value-free: they resolve the locked
feature and label version ids, DatasetVersion id, partition id, materialization
plan id, lifecycle state, and availability windows. Parquet existence and value
hash equality are checked before runtime resolution, at the value-store/registry
layer.

Resolver behavior is fail-closed. A malformed lock, a fuzzy feature or label
name, a stale content-addressed id, a DatasetVersion mismatch, or a partition
mismatch must block resolution. The resolver must never substitute a nearby
registered version.

The focused preflight test is:

```bash
python -m pytest tests/unit/futures_substrate_scaleout/test_keystone_identity.py -q
```

The test uses tiny synthetic rows and pytest temporary directories only. It
does not read provider files, materialize full-window values, write repository
Parquet files, call external providers, run diagnostics, or make alpha,
profitability, tradability, live, paper, or broker claims.
