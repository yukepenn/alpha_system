# End-to-End Data Foundation Dry Run

DATA-P24 adds `alpha_system.data.foundation.dry_run`, a synthetic-only dry-run
driver for the full data-foundation path. It composes existing campaign objects
over tiny hand-authored fixtures and performs no external IBKR call, socket
probe, raw data write, canonical data write, broker action, order action, or
account access.

## Entry Point

The driver is callable as a module when the local source tree is on
`PYTHONPATH`:

```bash
PYTHONPATH=src python -m alpha_system.data.foundation.dry_run
```

The default mode is `synthetic`. `dry_run` is also accepted. Both modes have
`allows_external_api = false`; external modes are rejected by the driver before
the path can run.

## Synthetic Path Exercised

The successful dry run walks this lifecycle in memory:

```text
source -> connection -> request/manifest -> pacing/chunk/resume
-> raw object metadata -> parsed bars -> canonical bars
-> quality/coverage -> dataset version -> optional registry round-trip -> partitions
```

Aggregate result from the default fixture:

| Field | Value |
| --- | --- |
| Fixture | `synthetic_ibkr_e2e_provider_fixture_v1` |
| Access mode | `synthetic` |
| External call attempted | `false` |
| clientId | `201` |
| Manifest | `hrm_synthetic_ibkr_e2e_v1` |
| Pacing policy | `rpp_ibkr_historical_conservative_tobeverified_v1` |
| Manifest chunk count | `1` |
| Completed ledger chunks | `1` |
| Pending resume chunks | `0` |
| Raw object metadata records | `1` |
| Parsed bars | `3` |
| Canonical bars | `3` |
| Quality status | `PASSING` |
| Coverage status | `PASSING` |
| Dataset version | `dsv_data_p24_synthetic_e2e_v1` |
| Registry round-trip | `true` in the integration test with a caller-supplied temp registry |
| Partition IDs | `development_partition`, `validation_partition`, `locked_test_candidate` |

The summary intentionally omits raw fixture payloads and canonical bar dumps.

## Lifecycle Blocks

`assert_lifecycle_blocks_fail_closed()` asserts these missing-prerequisite
blocks:

- Missing `HistoricalRequestManifest` blocks provider-pull preflight.
- clientId `101` and `102` are hard-blocked.
- clientIds outside `201-209` fail closed.
- Missing `RequestPacingPolicy` blocks pull preflight and naive loops.
- Missing `LocalDataRootPolicy` / raw layout policy blocks raw writes.
- Missing `available_ts` blocks canonicalization.
- `available_ts < bar_end_ts` blocks canonicalization.
- Quality gaps block dataset versioning.
- Incomplete chunks block dataset versioning through coverage.
- `READY_FOR_TRADING`, `LIVE_FEED_READY`, `BROKER_ENABLED`,
  `ALPHA_VALIDATED`, and `PROFITABLE` are not accepted lifecycle states.
- Order/account methods remain unreachable from the data boundary.

## Boundary Posture

The dry run confirms the IBKR boundary remains read-only historical only:

- `DataAccessMode.synthetic().allows_external_api` is `false`.
- The default clientId remains `201`; reserved clientIds fail closed.
- No read-only handler is registered or invoked for an external provider call.
- Order/account/position/execution-style method names are refused by the data
  boundary.
- The run does not create raw data, canonical data, local DBs, logs, caches, or
  generated report bundles.

## Interpretation

This is a data-foundation wiring and guard dry run, not evidence of market-data
completeness, research approval, alpha value, profitability, tradability,
execution readiness, broker readiness, paper readiness, live readiness, or
production readiness.
