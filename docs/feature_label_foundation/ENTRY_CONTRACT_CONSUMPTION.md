# Entry Contract and DatasetVersion Consumption

This document records the FLF-P01 entry contract for
`ALPHA_FEATURE_LABEL_FOUNDATION_V1`. It extends the high-level overview in
`docs/feature_label_foundation/OVERVIEW.md` and the pre-campaign
`docs/FEATURE_LABEL_FOUNDATION_ENTRY_CONTRACT.md`.

The durable code surface is `alpha_system.features.consumption`.

## Sanctioned Entry Path

Feature and label code consumes one accepted DatasetVersion at a time through:

```python
from alpha_system.features.consumption import resolve_accepted_dataset_version
```

`resolve_accepted_dataset_version(...)` wraps
`alpha_system.data.foundation.version_registry.resolve_dataset_version(...)`.
It fails closed when the registry record is missing, when the lifecycle state is
not `VERSIONED` or `READY_FOR_RESEARCH`, or when supplied quality, coverage,
manifest, code-hash, and config-hash evidence does not bind to the resolved
DatasetVersion.

The returned `AcceptedDatasetVersion` handle represents exactly one provenance
line. Databento DatasetVersions and IBKR DatasetVersions must be resolved as
separate handles and must not be merged into a single input.

## Admissibility

A DatasetVersion is consumable by the Feature/Label layer only when all of these
conditions hold:

- the registry resolves the requested DatasetVersion id;
- the lifecycle state is `VERSIONED` or `READY_FOR_RESEARCH`;
- the linked `DataQualityReport` is non-blocking;
- the linked `CoverageReport` is non-blocking and linked to the same quality
  report;
- the source manifest hash, code hash, config hash, and quality report hash
  match the resolved DatasetVersion.

The adapter delegates those evidence checks to the existing data-foundation
DatasetVersion methods. It does not redefine governance or data-foundation
objects.

## Canonical Records Only

After resolving an accepted handle, callers may reconstruct records only from
canonical mappings:

- `canonical_bars_from_mappings(...)` returns `CanonicalBarRecord` objects.
- `canonical_bbos_from_mappings(...)` returns `CanonicalBBORecord` objects.
- `dense_grid_bars_from_mappings(...)` returns `DenseGridBarRecord` objects.

The underlying canonical `from_mapping(...)` loaders reject unsupported fields,
including raw provider-shaped fields. The adapter also requires each
reconstructed record's `data_version` to match the accepted DatasetVersion id.

The adapter does not read DBN, Zstd, parquet, arrow, feather, raw provider
responses, canonical data files, feature values, or label values. It performs no
external provider calls and no materialization.

## Partition Handling

Every record reconstruction call requires a partition id and purpose. The
adapter routes that pair through
`require_governance_metadata_for_locked_partition_use(...)`.

Development and validation partition use proceeds through the same guard. Any
non-QA use of `locked_test_candidate` or `latest_shadow_candidate` requires
substantive governance contamination metadata. Missing or vague metadata raises
`DataFoundationValidationError` before any records are exposed.

## Safety Boundary

This entry contract is substrate plumbing only. It does not create features,
labels, strategies, backtests, reports, broker behavior, order routing, paper
trading, live trading, provider calls, alpha claims, profitability claims, or
tradability claims.

Feature and label values remain local-only and uncommitted under the campaign
artifact policy.
