# LabelStore And LabelRegistry

`alpha_system.labels.registry.LabelRegistry` registers materialized label
metadata in a local-only SQLite registry. It is a discoverability and lineage
surface only. A registered label is not alpha, not a promoted candidate, not a
live feature input, not tradable, and not strategy-ready.

## Local Registry

The default registry path is:

```text
$ALPHA_DATA_ROOT/registry/labels.sqlite
```

`ALPHA_DATA_ROOT` is required for the default path and must resolve outside the
repository tree. Tests may pass an explicit temporary SQLite path. The registry
stores label contract metadata, deterministic `LabelVersion` ids, lineage,
duplicate/equivalent exposure reports, materialization summary timestamps, and
deprecation records. It does not store `LabelValueRecord.value` payloads,
materialized label values, raw/canonical data, provider files,
parquet/arrow/feather files, or broker state.

## Registration Contract

Registration fails closed unless all of these are true:

- the caller supplies a `LabelMaterializationResult` from the FLF-P21 label
  materialization engine;
- the result is not dry-run and carries a `LabelMaterializationPlan`;
- the plan lifecycle gate is `MATERIALIZATION_ALLOWED`;
- the plan legal consumer is `labels_only`;
- the supplied `LabelContractSpec` carries a governed `lspec_` LabelSpec
  binding;
- the supplied `LabelVersion` is the deterministic version derived from that
  `LabelContractSpec`;
- a `LabelLineageRecord` can be bound to the same `LabelContractSpec`,
  `LabelVersion`, and governed `lspec_` id;
- the materialization result contains `LabelValueRecord`s for the registered
  version;
- every registered value record has timezone-aware `event_ts`, `horizon_end_ts`,
  and `label_available_ts`, with `label_available_ts >= horizon_end_ts`;
- the materialization output path remains under `ALPHA_DATA_ROOT`.

The registry records value counts and min/max event and label-availability
timestamps. It does not copy label values into SQLite.

## Duplicate And Equivalent Exposure

The registry records prior label exposure so it does not become a dumping
ground. Re-registering the same `LabelVersion` is idempotent. Registering a
different version with the same `label_id` records `DUPLICATE_RECORDED`.
Registering a different label id with an equivalent label contract exposure
signature records `EQUIVALENCE_RECORDED`.

Exposure reports are metadata for audit and later study-spec resolution. They
do not promote labels, approve research hypotheses, or turn labels into feature
inputs.

## Resolution

`LabelRegistry.resolve_label(label_version_id)` resolves a deterministic
`LabelRegistryRecord` by `LabelVersion` id.

`LabelRegistry.resolve_lineage(label_version_id)` resolves the bound
`LabelLineageRecord`. Missing labels return `None`; callers that require a
complete study input must fail closed rather than silently continuing with a
partial label set.

## Deprecation

`LabelRegistry.deprecate_label(...)` writes a `LabelDeprecationRecord` and marks
the registry record `DEPRECATED`. Lineage is retained for audit and
reproducibility. The registry lifecycle is deliberately narrow:
`REGISTERED`, `READY_FOR_STUDY`, and `DEPRECATED` only. Prohibited MVP states
such as `ALPHA_VALIDATED`, `STRATEGY_READY`, `LIVE_READY`, `PROFITABLE`,
`TRADABLE`, and `PRODUCTION_READY` are not valid registry states.

`READY_FOR_STUDY` means a governed future `StudySpec` consumer may reference the
registered label version. It is not a result claim.

## Boundary

The LabelRegistry consumes accepted DatasetVersion materialization outputs. It
does not call Databento, IBKR, or any external provider; it does not read raw
provider files; it does not create broker/live/paper/order/account behavior;
it does not expose labels as live features; and it does not make alpha,
profitability, tradability, or production-readiness claims.
