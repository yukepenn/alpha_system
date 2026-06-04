# Historical Request Spec And Manifest

`DATA-P07` defines the request-planning records for IBKR historical data. These
records are declarative only: they describe what would be requested later, but
they do not call IBKR, write data, prove coverage, or authorize a pull.

## `HistoricalRequestSpec`

`HistoricalRequestSpec` lives in
`src/alpha_system/data/foundation/requests.py`. It describes one planned
historical-data request before any provider call.

Required fields:

- `request_spec_id`
- `source_id`
- `symbol_root`
- `contract_ref`
- `sec_type`
- `exchange`
- `currency`
- `bar_size`
- `what_to_show`
- `use_rth`
- `duration`
- `end_datetime_policy`
- `start_ts`
- `end_ts`
- `chunk_policy`
- `client_id`

Validation is fail-closed. The record rejects missing fields, unknown futures
roots, empty references, non-boolean `use_rth`, naive timestamps, `end_ts`
earlier than `start_ts`, empty or zero-valued `chunk_policy`, exchange/currency
that do not reconcile with the instrument master, and unsafe IBKR client IDs.

The `client_id` validation delegates to DATA-P03
`IBKRClientIdPolicy.default().validate_client_id()`. clientId `101` and `102`
remain hard-blocked, the data namespace remains `201-209`, and the default data
client remains `201`. DATA-P07 does not reimplement or relax that policy.

`contract_ref` is a reference to a discovered dated-contract identity or a
root/continuous reference. It is not a provider response and not a claim that
IBKR has historical availability for the referenced contract.

## `HistoricalRequestManifest`

`HistoricalRequestManifest` describes a planned batch of request specs and
chunk count. It carries:

- `manifest_id`
- `batch_id`
- `request_specs`
- `chunk_count`
- `expected_coverage`
- `pacing_policy_id`
- `data_root`
- `created_by`
- `created_at`
- `manifest_hash`

The manifest validates every embedded request spec, requires at least one
request, requires a positive `chunk_count`, rejects duplicate
`request_spec_id` values, validates `data_root` through DATA-P02
`LocalDataRootPolicy` semantics, and stores no real data. `expected_coverage`
is planned coverage metadata only; it is not a coverage report and not a
quality pass.

## `manifest_hash`

`manifest_hash` is a SHA-256 digest over normalized manifest content using
stable JSON field ordering and compact separators. The hash body includes:

- schema id `alpha_system.historical_request_manifest.v1`
- `manifest_id`
- `batch_id`
- normalized `request_specs`
- `chunk_count`
- `expected_coverage`
- `pacing_policy_id`
- `data_root`
- `created_by`

`created_at` is excluded because it is wall-clock audit metadata. The
`manifest_hash` field itself is also excluded because it is the digest being
computed. Recomputing the hash over unchanged non-wall-clock content produces
the same value; persisted manifests reject mismatched hashes.

## Lifecycle Block

The DATA-P07 lifecycle predicates encode the first request-planning block:

- `NOT_REQUESTED -> REQUEST_PLANNED` requires a valid `HistoricalRequestSpec`.
- `REQUEST_PLANNED -> REQUEST_AUTHORIZED` requires a valid
  `HistoricalRequestManifest`.
- A missing or invalid manifest blocks provider-pull preflight.

The guard functions are planning predicates only:

- `plan_historical_request_transition(...)`
- `authorize_historical_request_transition(...)`
- `require_validated_manifest_for_provider_pull(...)`
- `provider_pull_manifest_guard(...)`

They are not wired to any external call in DATA-P07. External IBKR pulls remain
out of scope until later authorized phases and still require their separate
authorization environment.

## Synthetic Sample Policy

`templates/data/synthetic_historical_request_manifest.json` is a tiny synthetic
manifest for validation and documentation examples. It uses fake planning
metadata, includes `synthetic: true`, and marks both `real_coverage_claim` and
`authorization_claim` as `false`.

The sample is not raw data, canonical data, a provider response, a real coverage
statement, pull authorization, or evidence for alpha, profitability,
tradability, or production readiness.

## Safety Boundaries

DATA-P07 adds no broker, order, account, paper, live, real-time, or production
execution scope. It performs no provider pull and writes no data into the repo.
Real and canonical market data remain local-only under the configured
`ALPHA_DATA_ROOT` policy, outside git.
