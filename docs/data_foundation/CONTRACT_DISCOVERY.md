# Contract Details Snapshot And Discovery

`DATA-P06` adds dated futures contract identity and contract-details
provenance for the `ALPHA_DATA_FOUNDATION_V1` data foundation.

This is a local-only scaffold. It does not call IBKR, open a socket, request
contract details, write raw data, select a live contract, or claim historical
availability. Authorized external reads remain reserved for later data-pull
phases.

## Dated Contract Record

`FuturesContractRecord` lives in
`src/alpha_system/data/foundation/instruments.py`. It carries the campaign
required fields:

| Field | Meaning |
| --- | --- |
| `contract_id` | Dated-contract identity key. |
| `root_symbol` | Futures root reconciled against `InstrumentMasterRecord`. |
| `contract_month` | Contract month in `YYYY-MM` or month-code style such as `H5`. |
| `ib_symbol` | IBKR symbol, reconciled against the root instrument master. |
| `trading_class` | IBKR trading class for the dated contract. |
| `con_id` | IBKR numeric contract id, or `None` until discovered. |
| `last_trade_date_or_contract_month` | IBKR last-trade/contract-month field. |
| `expiration` | Contract expiration date. |
| `multiplier` | Multiplier, reconciled against the root instrument master. |
| `exchange` | Exchange, reconciled against the root instrument master. |
| `currency` | Currency, reconciled against the root instrument master. |
| `include_expired_support_status` | Enumerated support status for includeExpired discovery. |

The includeExpired status defaults to `not_checked`, not `supported`.
Construction fails closed when the root is absent from the instrument master,
when multiplier, exchange, currency, or IB symbol do not reconcile with the
root anchor, or when the contract id, month, expiration, `con_id`, or support
status is invalid.

The record does not imply full historical availability, a selected current
contract, alpha value, tradability, broker readiness, or execution readiness.

## Contract Details Snapshot

`ContractDetailsSnapshot` is a frozen, content-addressed snapshot of a
normalized contract-details response. It carries:

| Field | Meaning |
| --- | --- |
| `snapshot_id` | Stable id for this snapshot record. |
| `contract_id` | Link to `FuturesContractRecord.contract_id`. |
| `raw_details_ref` | Reference to a local-only raw object or synthetic fixture. |
| `normalized_fields` | Immutable normalized subset of contract details. |
| `retrieved_at` | Timezone-aware retrieval timestamp. |
| `client_id` | DATA-P03 data-client id, validated against `201-209`. |
| `source` | Provider or synthetic source label. |
| `hash` | SHA-256 content hash. |

The hash is computed over the contract id, raw-details reference, normalized
fields, retrieval timestamp, client id, and source. It excludes `snapshot_id`,
so two snapshot records for the same content produce the same hash. Persisted
snapshots loaded with `from_mapping()` must include the hash and the hash must
match the content.

The snapshot stores a reference only. It must not embed or commit a provider
payload. Nested normalized fields are frozen; mutation attempts fail at runtime
instead of silently changing hashed content. The client id is validated by the
DATA-P03 `IBKRClientIdPolicy`, so `101`, `102`, and out-of-range ids fail
closed.

## IncludeExpired Discovery

The discovery scaffold uses these records:

- `ContractDiscoveryRequest`
- `ContractDiscoveryAvailabilityLogEntry`
- `ContractDiscoveryResult`
- `record_contract_discovery()`

The request accepts declarative or synthetic inputs only: a root symbol, security
type `FUT`, optional `include_expired`, client id, and source label. It rejects
invalid roots, `CONTFUT`, broker/live/order/account style inputs, and out-of-
policy client ids.

`record_contract_discovery()` emits an availability log entry. If
`include_expired=True` and no support status is supplied, the status is
`unknown`. If includeExpired was not requested, the status is `not_checked`.
`supported` and `unsupported` require `include_expired=True` plus an
`evidence_ref`, such as a synthetic fixture id or a future local-only raw-object
reference.

The log entry intentionally has no history-depth field. It records what was
checked and what was discovered; it does not promise full historical coverage or
CME economic truth.

## No-Live-Call Boundary

DATA-P06 performs no external IBKR call and introduces no provider client. The
scaffold is pure Python over declarative inputs and optional synthetic fixtures.
Later authorized phases can pass a real, local-only contract-details reference
and normalized fields into the same `FuturesContractRecord` and
`ContractDetailsSnapshot` contracts without changing these record shapes.

No broker, order, account, position, paper, live, real-time feed, deployment,
alpha, profitability, tradability, full-history, or production-readiness scope
is introduced by this phase.
