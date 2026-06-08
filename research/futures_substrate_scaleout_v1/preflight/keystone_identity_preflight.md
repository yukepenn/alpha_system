# Keystone Identity Preflight

Campaign: `ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`
Phase: `FUTSUB-P04`

## Scope

This value-free preflight confirms that the value-store and registry metadata
contracts are sufficient for scaleout phases to preserve keystone identity. It
uses tiny synthetic rows and local temporary directories only; it does not
materialize the full 2018-2026 ES/NQ/RTY window.

## Representative Slice

The focused test materializes one synthetic OHLCV return feature and one
synthetic fixed-horizon label through the real feature and label materialization
engines with `ValueStoreFormat.PARQUET`.

Verified chain:

```text
dry-run preview -> execute -> Parquet values + manifest -> registry record
  -> version lock -> runtime resolver handle
```

Feature dry-run and execute use the same deterministic plan identity. Label
dry-run and execute preserve the same content-addressed `label_version_id`; the
label plan id intentionally includes the dry-run flag.

## Required Registry Metadata

Feature and label registry records are confirmed to expose:

- `value_store_format`
- `parquet_path`
- `value_content_hash`
- `value_schema_version`
- `dataset_version_id`
- `feature_version_id` or `label_version_id`

The preflight found no missing registry fields requiring a schema change.
Existing feature and label registries already include additive backfill columns
for the value-store fields.

## Resolver Fail-Closed Checks

The representative slice verifies that:

- an exact registered `feature_version_id` and `label_version_id` resolve;
- a stale but well-formed `feature_version_id` blocks as unresolved;
- a fuzzy feature name blocks as an invalid feature-pack ref;
- a stale but well-formed `label_version_id` blocks as unresolved;
- a fuzzy label name blocks as an invalid label-pack ref;
- no fallback or nearest-name substitution is accepted.

## Boundaries

No provider data, raw files, local registry data, Parquet values, SQLite files,
run logs, or heavy artifacts are commit-eligible from this preflight. The
runtime input pack remains value-free and omits materialization output paths by
design. Parquet path and content-hash checks belong to the value-store/registry
layer before runtime resolution.
