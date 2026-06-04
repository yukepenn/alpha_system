# Parsed Bar Records

`DATA-P14` defines the parsed, bronze bar layer for
`ALPHA_DATA_FOUNDATION_V1`. A parsed bar is a deterministic interpretation of an
immutable `RawDataObject` into provider-shaped bar fields. It is not a canonical
research bar, quality report, dataset version, or tradability signal.

## Parsed Bar Record

`ParsedBarRecord` is a frozen, fail-closed record with exactly these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `source` | Yes | `DataSourceProfile.source_id` from the raw object. |
| `symbol` | Yes | Provider-shaped symbol text from the raw row. |
| `contract_ref` | Yes | Provider-shaped contract reference from the raw row. |
| `provider_ts` | Yes | Provider-supplied timestamp text, preserved without canonical semantics. |
| `open` | Yes | Exact finite decimal provider open value. |
| `high` | Yes | Exact finite decimal provider high value. |
| `low` | Yes | Exact finite decimal provider low value. |
| `close` | Yes | Exact finite decimal provider close value. |
| `volume` | Yes | Exact non-negative decimal provider volume value. |
| `wap_if_available` | No | Optional exact non-negative decimal WAP when supplied by the provider. |
| `bar_count_if_available` | No | Optional non-negative provider bar count when supplied. |
| `request_id` | Yes | Provenance link to the source historical request. |
| `raw_object_id` | Yes | Provenance link to the immutable raw object. |

Validation rejects missing required fields, malformed identifiers, blank provider
timestamps, non-finite numeric values, negative volume/WAP, malformed bar count,
unsupported extra fields, and any canonical timestamp or session field such as
`event_ts`, `bar_start_ts`, `bar_end_ts`, `available_ts`, `ingested_at`, or
`session_label`.

## Parser

`ParsedBarParser` and `parse_raw_bar_records()` read one or more
`RawDataObject` refs and emit `ParsedBarRecord` tuples. The default parser reads
the raw object path already validated by the DATA-P09 raw-lake layout policy,
verifies the loaded bytes against `RawDataObject.content_hash`, parses the raw
CSV rows deterministically, and checks that the parsed row count matches
`RawDataObject.row_count`.

Malformed rows fail closed with `DataFoundationValidationError`. Rows are not
silently dropped, deduplicated, sorted, canonicalized, quality-scored, or
converted into session-aware bars at this layer.

## Boundary

Parsed bars remain provider-shaped. `provider_ts` is only the provider-supplied
timestamp text and does not define `event_ts`, bar start, bar end,
availability/lookahead timing, session membership, or exchange-calendar
semantics. Those contracts belong to DATA-P15 and later canonicalization phases.

The raw-to-parsed provenance link is mandatory: every parsed bar carries both
`request_id` and `raw_object_id`. Parser success advances local lifecycle state
from `RAW_COMPLETE` to `PARSED`; it does not imply canonical truth, alpha value,
profitability, tradability, broker readiness, paper/live readiness, or any
order/account capability.
