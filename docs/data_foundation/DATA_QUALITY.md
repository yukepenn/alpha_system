# DATA-P16 Data Quality Report

`DataQualityReport` is the DATA-P16 fail-closed audit layer for canonical
1-minute bars. It consumes DATA-P15 canonical bar fields read-only and records
aggregate findings only. It does not write data, connect to a provider, approve
research use, or make any alpha, profitability, tradability, broker, paper, live,
or production-readiness claim.

## Required Fields

The report has exactly these fields:

- `quality_report_id`
- `dataset_version_id`
- `gap_summary`
- `duplicate_summary`
- `non_monotonic_summary`
- `ohlc_errors`
- `zero_negative_price_errors`
- `zero_volume_anomalies`
- `dst_anomalies`
- `session_coverage`
- `roll_discontinuities`
- `provider_error_summary`
- `status`

Construction is fail-closed. Missing fields, extra fields, malformed summary
payloads, hidden raw/full canonical bar rows, or a top-level `status` that does
not reconcile with the findings raise `DataFoundationValidationError`.

## Status Semantics

`status` uses `PASSING`, `WARNING`, or `BLOCKING`.

`BLOCKING` means the report contains a defect that must block dataset
versioning. Silent gaps, duplicate timestamps, non-monotonic timestamps, OHLC
errors, zero or negative prices, DST/timestamp anomalies, missing expected
session coverage, undocumented roll transitions, and provider errors are
blocking findings.

`WARNING` is reserved for non-blocking anomalies currently represented by
zero-volume bars. A warning is still an audit finding and is not an acceptance or
research-readiness claim.

`PASSING` means the report found no warnings or blockers in the scoped
synthetic or in-memory inputs. It is not a claim about strategy value or live
use.

## Aggregate Bound

Report summaries store counts, statuses, grouped counts, and capped sample
intervals or identifiers. They do not embed raw provider responses, full
canonical bar series, or OHLCV rows. Sample detail is capped to keep reports as
audit summaries rather than data artifacts.

## Builder

`DataQualityReport.from_canonical_bars(...)` computes the report from
`CanonicalBarRecord` instances or strict canonical-shaped mappings. Mappings
must carry the DATA-P15 field names and no unsupported fields. This lets the
audit catch corrupted or malformed canonical-shaped inputs without changing the
DATA-P15 canonical record contract.
