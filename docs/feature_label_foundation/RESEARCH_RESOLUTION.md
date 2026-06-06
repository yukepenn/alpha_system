# How Research Resolves Features And Labels

This is the contract for how the Research Runtime, the future Agent Factory, and
any research code should obtain feature and label inputs. It complements
[ADR-0006](../../decisions/0006-feature-label-value-storage.md) and the store
docs ([FEATURE_STORE](FEATURE_STORE.md), [LABEL_STORE](LABEL_STORE.md)).

## Resolve through registries, not raw paths

Research and runtime code **must**:

- resolve the `DatasetVersion` from `$ALPHA_DATA_ROOT/registry/datasets.sqlite`
  (via `alpha_system.data.foundation.version_registry.resolve_dataset_version`);
- resolve FeaturePack / FeatureVersion refs (`fver_…`) from
  `$ALPHA_DATA_ROOT/registry/features.sqlite` (via the `FeatureStore` /
  `FeatureRegistry` resolver surface);
- resolve LabelPack / LabelVersion refs (`lver_…`) from
  `$ALPHA_DATA_ROOT/registry/labels.sqlite` (via the `LabelRegistry` resolver
  surface);
- load values, when values are needed, from the **registered local value path**
  recorded on the registry record (`materialization_output_path`), never by
  guessing file locations.

Research and runtime code **must not**:

- read raw Databento DBN/Zstd, IBKR responses, or canonical provider files
  directly;
- parse arbitrary local paths by hand;
- recompute all features from scratch for every study;
- treat SQLite as a value store (the registries hold metadata only);
- treat JSONL audit output as the final research table once a Parquet
  research-scale tier exists (ADR-0006).

## Value-free resolution is the default

The Research Runtime input resolver is **metadata-only**: it resolves registry
records into handles and never opens value files. Diagnostics and studies that
need values load them explicitly from the registered value path. For
research-scale scans, prefer DuckDB/Polars over local Parquet once
`FEATURE_LABEL_PARQUET_SINK_V1` lands; until then JSONL is the small/audit tier.

## Creating new features/labels is governed

New draft features/labels are created only through the governed path:

1. an approved `FeatureRequest` (`freq_…`, gate-admitted) or governance
   `LabelSpec` (`lspec_…`);
2. a `FeatureSpec`/`FeatureSetSpec` or fixed-horizon/family label definition;
3. local materialization over an accepted `DatasetVersion` partition
   (`materialize_features` / `materialize_labels`);
4. registration into `features.sqlite` / `labels.sqlite`
   (`register_materialized_feature` / `register_materialized_label`).

The local-only seed materialization operator (`alpha feature materialize
--execute` / `alpha label materialize --execute` with a
`configs/seed_packs/*.json` config) wraps exactly this governed loop for seed
packs. It reads already-canonical local Parquet (never provider files), runs the
real quality/coverage gates over the materialized partition, writes
`values.jsonl` under `ALPHA_DATA_ROOT`, and registers metadata into the local
registries. No values, registries, or raw data are ever committed.

## No claims

Resolving or materializing features/labels makes no alpha, profitability,
tradability, factor-promotion, or strategy/portfolio claim. Those are out of
scope for the substrate and the runtime.
