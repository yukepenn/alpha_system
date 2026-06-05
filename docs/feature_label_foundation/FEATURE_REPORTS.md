# Feature Quality and Coverage Reports

FLF-P15 adds descriptive evidence objects for registered feature values:

- `alpha_system.features.reports.FeatureQualityReport`
- `alpha_system.features.reports.FeatureCoverageReport`
- `alpha_system.reports.feature_card.FeatureCard`

These objects consume `FeatureRegistryRecord` metadata, lineage, duplicate /
equivalent exposure views, and local materialized `values.jsonl` output under
`ALPHA_DATA_ROOT`. They do not compute features, read raw provider files,
resolve provider data, or write report bundles.

## Quality Report

`FeatureQualityReport` reports row-level aggregate evidence only:

- observed row count and contract-shaped row count;
- null / NaN-like value rate;
- constant-output detection over non-missing values;
- `missing_bbo` and `bbo_quarantined` exposure counts;
- missing, invalid, or event-preceding `available_ts` defects;
- registry span consistency for `event_ts` and `available_ts`;
- duplicate / equivalent exposure status from the registry.

Hard contract defects are placed in the `blocking` finding partition. Descriptive
statistics are placed in `non_blocking`.

## Coverage Report

`FeatureCoverageReport` reports observed coverage by:

- symbol, from `FeatureValueRecord.entity_id`;
- session, from a structured value field such as `session_label` / `session_id`
  or a session quality flag;
- partition, from the materialization row and registry partition id.

Partition ids are mapped to `development`, `validation`, or
`locked_test_candidate` when they carry those semantics. Unknown partition
semantics are blocking.

Expected symbols, sessions, and partitions are read from registry metadata, for
example:

```json
{
  "coverage_expectations": {
    "symbols": ["ES", "NQ"],
    "sessions": ["ETH", "RTH"],
    "partitions": ["development_partition"],
    "documented_gaps": {
      "sessions": ["ETH"]
    }
  }
}
```

Undocumented missing expected coverage is blocking. Documented gaps are retained
as non-blocking evidence. Missing symbol or session expectation metadata is also
blocking because the report cannot distinguish complete coverage from silent
coverage loss.

## Feature Card

`FeatureCard` renders quality, coverage, and duplicate / equivalent exposure
status into plain text or structured payloads. The card is descriptive substrate
evidence only. It is not a readiness decision and does not make predictive,
trading, performance, broker, live, or deployment claims.

## Artifact Policy

Reports read local materialized JSONL values but do not commit values, report
bundles, local registries, raw/canonical data, parquet/arrow/feather files,
provider responses, DB files, or caches. Curated source, tests, docs, and
handoffs are the only commit-eligible outputs for this phase.
