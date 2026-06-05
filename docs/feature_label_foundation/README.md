# Feature/Label Foundation

This directory is the durable documentation root for
`ALPHA_FEATURE_LABEL_FOUNDATION_V1`. The campaign builds the governed
FeatureStore and LabelStore substrate that future research workflows consume
over accepted DatasetVersions.

This is research substrate documentation. It does not define alpha research,
strategy logic, backtests, portfolio construction, broker behavior, paper
trading, live trading, or production deployment.

## Entry Points

- `OVERVIEW.md` - narrative overview of the substrate, execution posture, and
  campaign wave shape.
- `../FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md` - pre-campaign entry contract
  for accepted DatasetVersion consumption.
- `../data_foundation/README.md` - data-foundation documentation for canonical
  records, DatasetVersions, partitions, quality, coverage, and local data-root
  policy.
- `../governance/README.md` - governance contracts consumed by this campaign.

## Hard Rules

- A feature is not alpha.
- A label is not alpha.
- A FeatureStore is not a factor library.
- A materialized FeatureSet is not a promoted candidate.
- A diagnostic report is not a research verdict.
- Accepted DatasetVersion input does not imply any alpha claim.
- No raw-data feature hacking: feature and label code consume accepted
  DatasetVersions through the sanctioned registry and canonical record APIs,
  never raw provider files.
- No `FeatureRequest` means no feature implementation.
- No `FeatureSpec` means no feature values.
- No `LabelSpec` means no label values.
- Labels are not features and must not be exposed as live feature inputs.
- Every feature value carries `available_ts`.
- Every label value carries `label_available_ts`.
- BBO missingness is flagged with `missing_bbo` or `bbo_quarantined`; it is not
  silently filled.
- Dense-grid no-trade rows remain flagged with `has_trade=false`,
  `synthetic=true`, and the `no_trade` quality flag; they are not trade bars.
- Raw data, canonical data, materialized feature values, materialized label
  values, local registries, local databases, logs, caches, and heavy artifacts
  remain local-only and uncommitted.
- This campaign makes no external Databento or IBKR provider calls.
- This campaign adds no broker, account, order, paper-trading, or live-trading
  behavior.

## DatasetVersion Entry Contract

The Feature/Label layer starts from accepted DatasetVersions, not provider
files. The sanctioned registry path is
`alpha_system.data.foundation.version_registry.resolve_dataset_version(...)`,
with the local registry under `$ALPHA_DATA_ROOT/registry/datasets.sqlite`.

An admissible DatasetVersion is in lifecycle state `VERSIONED` or
`READY_FOR_RESEARCH` with non-blocking quality and coverage. Databento
DatasetVersions and IBKR DatasetVersions keep distinct provenance and are not
merged into a single input line.

Feature and label code reconstructs input rows through canonical record
contracts:

- `CanonicalBarRecord` for sparse OHLCV truth, where a missing minute means no
  trade.
- `CanonicalBBORecord` for best bid/offer fields, derived mid/spread fields,
  and BBO quality flags.
- `DenseGridBarRecord` for derived dense research grids that explicitly mark
  no-trade synthetic rows.

Research usability keys off `available_ts`, not `event_ts`, `ingested_at`, or a
provider timestamp. Locked-test partition use requires governance
contamination metadata.

## Object Families

The Feature object family is governed by existing `FeatureRequest` semantics and
future campaign contracts for feature specs, versions, lineage, materialization,
quality, coverage, duplicate exposure, and deprecation. At a high level it
includes:

- request and contract objects: `FeatureRequest`, `FeatureSpec`,
  `FeatureFamily`, `FeatureInputSpec`, `TransformSpec`, `WindowSpec`,
  `NormalizationSpec`, and `FeatureSetSpec`;
- materialization and value objects: `FeatureMaterializationPlan`,
  `FeatureValueRecord`, `FeatureVersion`, and `FeatureLineageRecord`;
- store, registry, and report objects: `FeatureStore`,
  `FeatureRegistryRecord`, `FeatureQualityReport`, `FeatureCoverageReport`,
  `DuplicateExposureReport`, `EquivalentFeatureGroup`, and
  `FeatureDeprecationRecord`;
- BBO/top-book feature specs for spread, microprice, top-book imbalance, and
  liquidity-quality diagnostics.

The Label object family is governed by existing `LabelSpec` semantics and future
campaign contracts for label specs, versions, lineage, materialization, leakage
audits, quality, and coverage. At a high level it includes:

- request and contract objects: `LabelSpec`, `LabelFamily`, `LabelInputSpec`,
  `LabelHorizonSpec`, `LabelPathSpec`, `BarrierSpec`, and
  `CostAdjustmentSpec`;
- materialization and value objects: `LabelMaterializationPlan`,
  `LabelValueRecord`, `LabelVersion`, and `LabelLineageRecord`;
- store, registry, and report objects: `LabelStore`, `LabelRegistryRecord`,
  `LabelQualityReport`, `LabelCoverageReport`, `LabelLeakageAuditReport`, and
  `LabelAvailabilityPolicy`.

These object names describe the campaign substrate. They do not imply that any
feature or label value exists, that a study has been approved, or that any
research result has been found.

## Lifecycle Models

Feature lifecycle states:

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

Label lifecycle states:

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

`READY_FOR_STUDY` means the substrate object can be referenced by a governed
study input. It is not a result claim.

## Local-Only Values

Feature and label materialization is planned for local outputs under
`$ALPHA_DATA_ROOT`. The repository stores source code, contracts, schemas, docs,
tests, templates, handoffs, and review artifacts. It does not store real market
data, canonical datasets, materialized feature values, materialized label
values, or local registry databases.
