# FeatureStore And FeatureRegistry

`alpha_system.features.store.FeatureStore` registers materialized feature
metadata in a local-only `FeatureRegistry`. It is a discoverability and lineage
surface only. A registered feature is not a promoted candidate, not alpha, not
tradable, and not strategy-ready.

## Local Registry

The default registry path is:

```text
$ALPHA_DATA_ROOT/registry/features.sqlite
```

`ALPHA_DATA_ROOT` is required for the default path and must resolve outside the
repository tree. Tests may pass an explicit temporary SQLite path. The registry
stores feature contract metadata, lineage, feature-set membership,
duplicate/equivalent exposure reports, materialization summary timestamps, and
deprecation records. It does not store `FeatureValueRecord.value` payloads,
raw/canonical data, provider files, parquet/arrow/feather files, or any broker
state.

## Registration Contract

Registration fails closed unless all of these are true:

- the `FeatureSpec` is already implementation eligible;
- the supplied `FeatureVersion` is the deterministic version derived from that
  `FeatureSpec`;
- a `FeatureLineageRecord` can be bound to the same `FeatureSpec`,
  `FeatureVersion`, and governed `freq_` request id;
- the supplied `FeatureRequest` is admitted by the FLF-P05 request gate as
  `APPROVED`;
- the materialization result is not dry-run and contains
  `FeatureValueRecord`s for the registered version;
- every registered value record preserves timezone-aware `event_ts` and
  `available_ts`, with `available_ts` not preceding `event_ts`;
- the materialization output path remains under `ALPHA_DATA_ROOT`.

The store records value counts and min/max event and availability timestamps.
It does not copy feature values into SQLite.

## Duplicate And Equivalent Exposure

The store consumes `DuplicateExposureReport` and `EquivalentFeatureGroup` from
`alpha_system.features.request_gate`. It does not reimplement duplicate logic.
The registry exposes a read-only guard view over already registered features so
new requests are checked against prior registered exposure.

Blocking duplicate findings reject registration. Non-blocking equivalent
findings are persisted with an explicit equivalence link in the duplicate
exposure report; they are not silently admitted.

## Resolution

`FeatureStore.resolve_feature(feature_version_id)` resolves a deterministic
`FeatureRegistryRecord` by `FeatureVersion` id.

`FeatureStore.resolve_feature_set(feature_set)` resolves registered records in
the order defined by a `FeatureSetSpec`. Missing members fail closed rather
than returning a partial feature set silently.

Re-registering the same `FeatureVersion` with the same approved request handle
is idempotent and does not create a duplicate feature row.

## Deprecation

`FeatureStore.deprecate_feature(...)` writes a `FeatureDeprecationRecord` and
marks the registry record `DEPRECATED`. Lineage and feature-set membership are
retained for audit and reproducibility. The registry lifecycle is deliberately
narrow: `REGISTERED` and `DEPRECATED` only. Prohibited MVP states such as
`ALPHA_VALIDATED`, `STRATEGY_READY`, `LIVE_READY`, `PROFITABLE`, `TRADABLE`,
and `PRODUCTION_READY` are not valid registry states.

## Boundary

The FeatureStore consumes accepted DatasetVersion materialization outputs. It
does not call Databento, IBKR, or any external provider; it does not read raw
provider files; it does not create broker/live/paper/order/account behavior;
and it does not make alpha, profitability, tradability, or production-readiness
claims.
