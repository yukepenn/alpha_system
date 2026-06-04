# BID_ASK Pilot Plan

DATA-P20 defines an optional, bounded `BID_ASK` / spread-proxy pilot for the
data foundation. It is a secondary research-diagnostics track only. It does not
run a pilot, does not call IBKR, does not pull real `BID_ASK` data, and does
not make `BID_ASK` part of the primary `TRADES` common panel.

## Posture

The pilot plan lives in `BidAskPilotPlan` under
`src/alpha_system/data/foundation/bid_ask_pilot.py`, with the default
declarative config in `configs/data/bid_ask_pilot_plan.json`.

Required posture:

- `optional = true`
- `pilot_only = true`
- `research_diagnostics_only = true`
- `secondary_to_primary_trades_panel = true`
- `what_to_show = BID_ASK`
- `merge_into_primary_trades_panel = false`
- `implies_pull_authorization = false`
- `external_provider_call = false`
- `real_data_pull = false`

The primary common panel remains the DATA-P10 `TRADES` panel for ES/NQ/RTY from
`2018-01-01` to `present_as_of_run`. The pilot is not a substitute for that
panel and does not feed canonical `TRADES` data.

## Default Bounds

The default pilot bounds are deliberately small and stay well below the primary
panel:

| Bound | Default |
| --- | ---: |
| Symbols | `ES` only |
| Contracts | 1 synthetic contract reference |
| Date window | `2025-01-02` through `2025-01-03` |
| Maximum date-window days | 3 |
| Planned chunks | 2 |
| Maximum chunks | 4 |
| Maximum local storage footprint | 5 MiB |
| Estimated local storage footprint | 128 KiB |

The plan enforces these caps fail-closed. It also has hard pilot ceilings so a
config edit cannot silently broaden the pilot into a primary-panel-scale pull:
at most 2 symbols, 4 contracts, 10 calendar days, 24 chunks, and 25 MiB local
storage.

## Pacing And Resume Contract

The pilot references the DATA-P08 conservative pacing policy:

```text
rpp_ibkr_historical_conservative_tobeverified_v1
```

`RequestPacingPolicy.bid_ask_counts_double` must be true. The plan validates
that `RequestPacingPolicy.accounting_weight("BID_ASK")` is greater than
`accounting_weight("TRADES")`, so `BID_ASK` consumes heavier request-window
accounting. Naive request loops remain forbidden.

The pilot is manifest-driven. Any future provider-pull preflight must carry:

- a validated `HistoricalRequestManifest`;
- `HistoricalRequestSpec` entries with `what_to_show = BID_ASK`;
- a matching `RequestPacingPolicy`;
- a matching `HistoricalPullLedger` resume ledger;
- the existing provider-error ledger contract (`ProviderErrorRecord`).

DATA-P20 adds no connector and no new pull path. Its preflight helper validates
contracts only and returns no pull authorization.

## Quality And Coverage Contract

Pilot coverage and quality must use the DATA-P16 fail-closed reporting
contracts:

- `DataQualityReport`
- `CoverageReport`

Coverage alone is not quality. The pilot linkage requires a non-blocking
quality report for the same dataset version before pilot outputs can be treated
as linked diagnostics. Blocking coverage, blocking quality, missing reports, or
dataset-version mismatches fail closed.

## Spread-Proxy Scaffold

`compute_spread_proxy_metrics()` derives pilot-only spread proxies from
synthetic or declarative BID_ASK observations where both bid and ask are
available. It computes:

- midpoint: `(bid + ask) / 2`;
- spread: `ask - bid`;
- spread in basis points relative to midpoint.

Inputs fail closed when:

- required fields are missing or extra fields are present;
- `bid` or `ask` is non-positive or non-finite;
- `ask < bid`;
- the observation is outside the pilot plan window;
- the contract reference or pilot plan ID does not match the plan.

Every `SpreadProxyMetric` is marked:

- `pilot_only = true`
- `research_diagnostics_only = true`
- `tradable_cost_claim = false`
- `liquidity_truth_claim = false`
- `feeds_canonical_trades_panel = false`

These metrics are diagnostics over available BID_ASK data only. They are not
tradable spread, transaction-cost, slippage, liquidity, or execution truth.

## Synthetic Fixtures

`tests/fixtures/data/synthetic_bid_ask_spread_proxy_inputs.json` contains tiny
hand-authored BID_ASK-like observations for unit tests. It is not a provider
response, not real market data, and not evidence about any venue or instrument.

## Non-Goals

- No external IBKR call.
- No real `BID_ASK` pull.
- No broker, order, account, paper, live, or real-time surface.
- No primary-panel integration.
- No alpha, factor, label, strategy, profitability, tradability, liquidity, or
  production-readiness claim.
- No raw, canonical, provider-response, database, log, cache, or heavy artifact
  committed to git.
