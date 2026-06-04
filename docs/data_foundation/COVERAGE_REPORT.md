# DATA-P16 Coverage Report

`CoverageReport` records aggregate coverage by symbol, contract, session, and
partition for canonical 1-minute bar inputs. It is a coverage gate only: by
itself, it never means quality passed. A caller must explicitly link it to a
non-blocking `DataQualityReport` with the same `dataset_version_id`.

The report is local-first and read-only. It performs no provider call, writes no
raw or canonical data, and introduces no broker, order, account, paper, live,
alpha, profitability, tradability, or production-readiness scope.

## Required Fields

The report has exactly these fields:

- `coverage_report_id`
- `dataset_version_id`
- `symbol_coverage`
- `contract_coverage`
- `session_coverage`
- `partition_coverage`
- `missing_intervals`
- `incomplete_chunks`

Construction is fail-closed. Missing fields, extra fields, malformed coverage
summaries, hidden raw/full canonical bar rows, undocumented missing coverage, or
partition counts that do not reconcile with `missing_intervals` and
`incomplete_chunks` raise `DataFoundationValidationError`.

## Blocking Coverage

`CoverageReport.coverage_status` is derived, not stored as an extra report
field. Missing intervals and incomplete chunks produce `BLOCKING`, and
`blocks_versioning` returns `True`.

Coverage summaries include expected, observed, and missing aggregate counts.
If any summary records missing coverage while `missing_intervals` is empty, the
report fails closed instead of silently passing. `partition_coverage` must also
record `missing_interval_count` and `incomplete_chunk_count`, and those counts
must match the aggregate detail lists.

## Coverage Is Not Quality

`CoverageReport.require_linked_quality_report(...)` enforces the linkage rule:

- `None` is rejected because coverage alone is not quality.
- A mismatched `dataset_version_id` is rejected.
- A blocking coverage report is rejected.
- A blocking `DataQualityReport` is rejected.

When the coverage report is non-blocking and the linked quality report is
non-blocking for the same dataset version, the method returns the linked quality
report for downstream DATA-P17 gating.

## Aggregate Bound

The report stores grouped counts plus capped missing-interval and
incomplete-chunk summaries. It does not embed raw provider responses, full
canonical bar series, or OHLCV row dumps.
