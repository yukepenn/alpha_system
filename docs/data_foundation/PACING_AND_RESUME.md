# Pacing, Chunking, Retry, And Resume Ledger

`DATA-P08` defines local-only data-foundation records for future historical
pulls. These records do not call IBKR, do not write raw data, do not authorize a
pull, and do not imply that coverage or quality passed.

## Request Pacing Policy

`RequestPacingPolicy` is required before any future provider-pull preflight.
Missing or invalid pacing policy blocks the pull, which treats an unguarded
request loop as a fail-closed condition.

Required fields:

- `pacing_policy_id`
- `min_seconds_between_identical_requests`
- `max_requests_per_window`
- `window_seconds`
- `bid_ask_counts_double`
- `backoff_policy`
- `source`

The policy is configurable under
`configs/data/request_pacing_policy_to_be_verified.json`. Its values are
conservative local defaults and are marked `to_be_verified`, not current IBKR
truth. Before any authorized DATA-P22 or DATA-P23 pull, the values must be
checked against current IBKR historical-data pacing documentation or an
authorized local smoke-run result, and the verification method must be recorded.

`bid_ask_counts_double` must be true. `BID_ASK` requests have accounting weight
`2`; `TRADES` requests have accounting weight `1`. Backoff policy fields are
positive and finite, and retry attempts cannot silently exceed
`backoff_policy.max_attempts`.

## Chunk Lifecycle

`HistoricalChunkRecord` records one chunk request lifecycle. Required fields:

- `chunk_id`
- `request_spec_id`
- `symbol_root`
- `contract_ref`
- `start_ts`
- `end_ts`
- `status`
- `attempt_count`
- `provider_request_id`
- `raw_object_ref`
- `row_count`
- `error_ref`
- `retrieved_at`

Supported statuses are `NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`,
`INCOMPLETE`, `FAILED`, and `QUARANTINED`. There is no assumed-complete state.
Attempted chunks must carry `provider_request_id`; complete chunks must carry a
content-addressed `raw_object_ref`, `row_count`, and `retrieved_at`; incomplete,
failed, and quarantined chunks must carry `error_ref`.

`raw_object_ref` is a reference only, not a raw data write path. It must use
`sha256:<digest>` or `raw://sha256/<digest>`. Once present, it is immutable:
resume may reuse the same ref but must not overwrite it with a different ref.

## Provider Error Ledger

`ProviderErrorRecord` permanently records provider errors and incomplete
responses. Required fields:

- `error_id`
- `provider`
- `request_id`
- `chunk_id`
- `error_code`
- `error_message`
- `retryable`
- `attempt`
- `timestamp`
- `resolution`

Retryable errors use `RETRY_BACKOFF_SCHEDULED`, `RETRY_EXHAUSTED`, or
`INCOMPLETE_RESPONSE_RECORDED` and compute delay through the linked
`RequestPacingPolicy`. Non-retryable errors must use
`QUARANTINED_NON_RETRYABLE`, which quarantines the chunk rather than retrying.
The record classifies the error; it does not claim an unclassified error is
fatal.

## Pull Ledger And Resume Token

`HistoricalPullLedger` records the audited pull state for one manifest. Required
fields:

- `pull_id`
- `manifest_id`
- `chunk_records`
- `started_at`
- `finished_at`
- `status`
- `resume_token`
- `coverage_summary`
- `error_summary`

The ledger reconciles `coverage_summary.expected_chunk_ids` against
`chunk_records`. Missing expected chunks fail closed, and unexpected chunks fail
closed. Duplicate `chunk_id`, duplicate chunk request keys, and duplicate
`provider_request_id` values fail closed.

`resume_token` is a deterministic `sha256:<digest>` over the pull id, manifest
id, and recorded chunk state. Resuming with the token returns only non-complete
chunks. Complete chunks are reported separately and must not be regenerated or
raw-overwritten.

Ledger status is derived from chunk statuses:

- all complete -> `COMPLETE`
- any quarantined -> `QUARANTINED`
- any failed -> `FAILED`
- any incomplete -> `INCOMPLETE`
- all not started -> `NOT_STARTED`
- otherwise -> `IN_PROGRESS`

`coverage_summary` records expected, recorded, complete, incomplete, failed,
quarantined, not-started, and in-progress counts. `error_summary.error_refs`
must reconcile with chunk `error_ref` values. The summaries are audit records
only and use `quality_status = not_quality_checked`; they do not make a dataset
version ready or quality-accepted.

## Safety Boundary

DATA-P08 introduces no external IBKR call, real-data pull, raw data lake write
path, broker, order, account, paper, live, real-time, alpha, factor, label, or
production execution behavior. It adds only local validation records, tests,
configuration, and documentation for future guarded pulls.
