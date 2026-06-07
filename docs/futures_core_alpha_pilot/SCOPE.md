# Futures Core Alpha Pilot Scope

`FUTCORE-P02` records the bounded pilot scope for
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. The authoritative value-free contract is:

- `research/futures_core_alpha_pilot_v1/scope/scope_contract.md`

This page is a concise operator-facing pointer. The campaign bundle remains the
source of truth; if this page disagrees with
`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml`, the campaign file
wins.

## Boundaries

- In-scope universe: `ES`, `NQ`, `RTY`.
- Deferred universe: `MES`, `MNQ`, `M2K`, rates, FX, commodities, vol products,
  options, equities, L1 eventstream, and L2/L3.
- Required session views: `full_session`, `RTH_only`, `ETH_only`,
  `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`,
  `RTH_with_ETH_context`.
- Horizons: `1m` sampling only; `1m`/`3m` fragile diagnostics only; `5m`,
  `10m`, `15m`, and `30m` primary; `60m`, `120m`, `240m`, and `session_close`
  extended intraday.
- No position may cross the exchange daily maintenance / trade-date break.
- Family budget: cross-market / relative-value `0.40`; VWAP / session-auction
  `0.20`; regime momentum / reversion `0.15`; liquidity-sweep /
  failed-breakout `0.15`; BBO-tradability / confirmation `0.10`.
- Volume/activity is an overlay only, with no standalone budget and no new
  volume feature zoo.
- Research caps: `<=40` AlphaSpec drafts, `<=10` approved AlphaSpecs, `<=5` new
  feature or label requests, `<=3` diagnostics survivors, and `<=2` `WATCH` or
  `CANDIDATE_RESEARCH` outcomes.

## Safety Boundary

The scope is evidence-only. It does not authorize AlphaSpec drafting in this
phase, diagnostics, input-pack locking, cost-model definition, broker operations,
live trading, paper trading, order routing, deployment, capital allocation,
production behavior, or profitability / tradability claims. `runs/**`, raw or
canonical data, feature or label values, provider responses, heavy artifacts,
local databases, logs, caches, secrets, and credentials remain local-only.
