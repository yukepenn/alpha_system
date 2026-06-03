# L2 Readiness

ASV1-P25 adds design-only Level-2 readiness schemas for future snapshot and event/delta research. The scope is schema metadata, timestamp semantics, synthetic in-memory validation, and documentation. It is not a replay engine and it is not execution infrastructure.

## Snapshot Schema

Each snapshot row represents one instrument, session, side, and book level:

- `instrument_id`
- `session_id`
- `event_ts`
- `receive_ts`
- `available_ts`
- `book_level`
- `side`
- `price`
- `size`
- `order_count`
- `data_version`
- `quality_flags`

`order_count` is present in the schema and may be null when the source does not provide it. `quality_flags` is always present as a tuple of string flags, empty when the synthetic record has no known quality issue.

## Event/Delta Schema

Each event/delta row represents one future update:

- `instrument_id`
- `session_id`
- `event_ts`
- `receive_ts`
- `available_ts`
- `sequence_id`
- `action`
- `book_level`
- `side`
- `price`
- `size`
- `order_count`
- `data_version`
- `quality_flags`

`sequence_id`, `book_level`, and `order_count` are schema fields even when a source or action makes a value unavailable. Missing values are represented as null rather than by removing the field.

## Timestamp Semantics

`event_ts` is the exchange or source event timestamp when available. `receive_ts` is the local or feed receive timestamp. `available_ts` is the earliest time the research system may use the information.

L2 records must satisfy `event_ts <= receive_ts <= available_ts`. Research consumers must order usability by `available_ts` first; using `event_ts` alone would create lookahead risk. Session assignment uses `event_ts`, while no-lookahead eligibility uses `available_ts`.

## Snapshot/Delta Consistency

Future replay work will need snapshot and delta rows to agree on `instrument_id`, `session_id`, and `data_version`. Deltas intended to follow a snapshot must not have `event_ts` or `available_ts` before the snapshot. When `sequence_id` is present, provided deltas must be monotonic.

## Boundaries

This readiness layer does not implement book reconstruction, queue-position modeling, latency simulation, passive fills, live market data, broker connectivity, paper trading, strategy validation, or production execution. The Tier 1 reference 1-minute bar engine remains the single PnL truth for this campaign.

The schemas and docs do not make alpha, profitability, robustness, tradability, or production-readiness claims.
