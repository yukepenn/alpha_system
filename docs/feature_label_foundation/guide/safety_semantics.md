# Safety Semantics

This page collects the operational checks that keep feature and label research
substrate point-in-time safe and artifact-clean.

## Availability

Every feature value must carry `available_ts`. The timestamp must be explicit,
timezone-aware, and derived according to the `FeatureSpec` rule. Usability must
not be inferred from provider time, event time, ingestion time, file ordering,
or materialization time.

Every label value must carry `label_available_ts`. The timestamp must be at or
after the label event time, the horizon end, and the governed
`LabelSpec.availability_time`.

## No Future Or Centered Live Windows

Feature contracts that can feed live-feature consumers must use causal windows.
Centered and future windows can appear only as offline-only metadata and cannot
be live-feature inputs.

Labels may use forward observations only inside a governed label horizon. That
permission belongs to label construction and does not transfer to features.

## No Label As Feature

Labels remain offline targets. A live feature request, feature spec, feature
set, or StudySpec input pack must not reference:

- a label value series;
- a label alias;
- a label transform;
- a `LabelSpec` id;
- a `LabelVersion` id;
- a `LabelRegistryRecord` identity.

The label leakage audit described in `../LABEL_LEAKAGE_AUDIT.md` consumes the
governance leakage guard and blocks label-as-feature paths.

## BBO Missingness

BBO missingness and quote quarantine are explicit quality signals:

- `missing_bbo` marks missing or bad quote rows;
- `bbo_quarantined` marks crossed or abnormal quote rows that remain surfaced.

Missing or quarantined rows are not silently forward-filled, interpolated, or
converted into substitute bid, ask, mid, spread, or microprice values.

## Dense-Grid No-Trade Rows

Sparse OHLCV is provider trade truth. A missing sparse minute means there was
no provider trade bar for that minute.

Dense research grids may carry synthetic no-trade placeholders. The canonical
signature is:

- `has_trade == False`;
- `synthetic == True`;
- `fill_method == "previous_close"`;
- `volume == 0`;
- `quality_flags` contains `no_trade`;
- `provider_bar_ref is None`.

Synthetic no-trade rows keep the grid aligned, but they are not trade bars and
must not be counted as provider trade activity.

## Local-Only Stores And Artifacts

FeatureStore and LabelStore registries are local-only. Default paths live under
`$ALPHA_DATA_ROOT/registry/`, outside the repository. Materialized values live
under `$ALPHA_DATA_ROOT/features/` or `$ALPHA_DATA_ROOT/labels/`.

Do not commit:

- raw or canonical data;
- materialized feature or label values;
- local registry SQLite files;
- parquet, arrow, feather, DBN, Zstd, logs, caches, or report bundles;
- provider responses or local data-root contents.

## Lifecycle States

Feature lifecycle:

```text
REQUESTED
SPEC_DRAFTED
SPEC_VALIDATED
IMPLEMENTATION_ALLOWED
IMPLEMENTED
MATERIALIZATION_PLANNED
MATERIALIZED_DRAFT
QUALITY_CHECKED
REGISTERED
READY_FOR_STUDY
REJECTED
QUARANTINED
DEPRECATED
```

Label lifecycle:

```text
LABEL_REQUESTED
LABEL_SPEC_DRAFTED
LABEL_SPEC_VALIDATED
MATERIALIZATION_ALLOWED
MATERIALIZED_DRAFT
LEAKAGE_AUDITED
QUALITY_CHECKED
REGISTERED
READY_FOR_STUDY
REJECTED
QUARANTINED
DEPRECATED
```

Only `READY_FOR_STUDY` is the terminal study-consumable state in this substrate.
It means a governed study may reference the object. It is not a result claim.
