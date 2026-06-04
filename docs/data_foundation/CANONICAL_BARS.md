# Canonical 1-Minute Bars

`DATA-P15` defines the silver-layer `CanonicalBarRecord` and
`TimestampSemanticsPolicy` contracts for `ALPHA_DATA_FOUNDATION_V1`. The phase
is contract-only: it does not canonicalize real data, call IBKR, write raw or
canonical datasets, or imply alpha value, tradability, broker readiness, paper
readiness, live readiness, or production readiness.

## Layer Position

The local data-foundation bar path is:

```text
RawDataObject -> ParsedBarRecord -> CanonicalBarRecord -> DatasetVersion
```

`ParsedBarRecord` remains bronze and provider-shaped. `CanonicalBarRecord`
carries canonical timestamp, instrument, contract, session, version, and quality
metadata that downstream quality, coverage, and versioning phases can validate.

## CanonicalBarRecord

`CanonicalBarRecord` is a frozen, fail-closed value object with exactly these
fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `instrument_id` | Yes | Canonical instrument identifier. |
| `contract_id` | Yes | Dated contract identifier. |
| `series_id` | Yes | Series identifier, kept separate from dated contract identity. |
| `bar_start_ts` | Yes | Timezone-aware one-minute interval start. |
| `bar_end_ts` | Yes | Timezone-aware one-minute interval end. |
| `event_ts` | Yes | Event timestamp for the completed bar after canonical validation. |
| `available_ts` | Yes | Earliest time the completed bar would have been usable in research/backtest logic. |
| `ingested_at` | Yes | Local ingestion timestamp, separate from `available_ts`. |
| `open` | Yes | Positive finite decimal open price. |
| `high` | Yes | Positive finite decimal high price. |
| `low` | Yes | Positive finite decimal low price. |
| `close` | Yes | Positive finite decimal close price. |
| `volume` | Yes | Non-negative finite decimal volume. |
| `source` | Yes | `DataSourceProfile.source_id`, such as a `dsrc_...` historical source. |
| `source_request_id` | Yes | Provenance link to the historical request. |
| `data_version` | Yes | Data version label for the canonical record. |
| `quality_flags` | Yes | Explicit collection of quality flags. It may be empty but cannot be implicit. |
| `session_label` | Yes | Session-model label such as `RTH`, `ETH`, `HOLIDAY`, or `EARLY_CLOSE`. |

Unsupported extra fields are rejected. A provider timestamp such as
`provider_ts` is not part of this canonical contract and is not treated as
research-ready input without canonical timestamp validation.

## Timestamp Semantics

`TimestampSemanticsPolicy.v1_no_lookahead()` pins the V1 no-lookahead meanings:

| Field | V1 meaning |
| --- | --- |
| `bar_start_ts` | Inclusive start of the one-minute bar interval in canonical timezone-aware time. |
| `bar_end_ts` | Exclusive end of the one-minute bar interval; must be greater than `bar_start_ts`. |
| `event_ts` | Event time of the completed bar after canonical timestamp validation. |
| `available_ts` | When the completed bar would have been usable by research/backtest logic. It is not the historical API return time. |
| `ingested_at` | Local ingestion time for the canonical record, stored separately from `available_ts`. |

The policy carries explicit `lookahead_rules`:

- canonicalization fails if `available_ts` is missing;
- `available_ts >= bar_end_ts` before research use;
- research consumers order usability by `available_ts`, not by `event_ts` or
  provider timestamps;
- provider timestamps are not research-ready without canonical validation;
- `ingested_at` must not be used as a substitute for `available_ts`.

## Fail-Closed Rules

Construction fails with `DataFoundationValidationError` when:

- any required field is missing;
- any timestamp is missing or timezone-naive;
- `bar_end_ts <= bar_start_ts`;
- `available_ts < bar_end_ts`;
- any OHLC price is zero, negative, non-finite, or malformed;
- `high < low`, `open` falls outside `[low, high]`, or `close` falls outside
  `[low, high]`;
- `volume` is negative;
- `session_label` is absent or outside the session model;
- `quality_flags` is not an explicit collection;
- the timestamp policy omits explicit lookahead rules or implies provider
  timestamps are research-ready.

This contract is a prerequisite for later quality, coverage, and versioning
work. It does not perform those later phases.
