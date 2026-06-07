# BBO Tradability AlphaSpec Batch

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P11`  
Family: BBO tradability / top-book confirmation  
Status: draft evidence only

`FUTCORE-P11` records four value-free governance `AlphaSpec` drafts for the
BBO tradability / top-book confirmation family. The family quota from the
`FUTCORE-P05` protocol is minimum 3, target 4, maximum 4; this batch uses the
target count and does not reallocate budget from any other family.

No draft is implemented, run, reviewed, promoted, or used for broker, paper,
live, order-routing, deployment, production, capital, profitability, or
standalone tradability conclusions in this phase.

## Draft Index

| File | AlphaSpec id | Instruments | Overlay role |
| --- | --- | --- | --- |
| `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_01.md` | `aspec_1284e49b083df11eeb0481ea` | ES, NQ, RTY | Spread-zscore plus top-book depth filter for confirmation or risk control. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_02.md` | `aspec_cfb2aad22b43bc23391a7806` | ES, NQ, RTY | Microprice-minus-mid and top-book imbalance confirmation overlay. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_03.md` | `aspec_857ea832d75aa4fc23b376d6` | ES, NQ, RTY | Top-book depth and imbalance risk-control or confirmation filter. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/FUTCORE-P11_bbo_tradability_04.md` | `aspec_89fa98eb6439f131de4151cb` | ES, NQ, RTY | Missing-BBO, bad-quote, wide-spread, and low-depth quarantine overlay. |

## Declared Diagnostics

Every draft declares the mandatory BBO-family diagnostics for later phases:

- valid BBO requirements for bid, ask, sizes, mid, spread, quality flags, and
  `available_ts`;
- spread, microprice, top-book imbalance, depth, and quote-quality framing;
- stale, crossed, missing, quarantined, invalid-size, and unavailable-quote
  exclusions;
- confirmation or risk-control role only, not standalone edge evidence;
- timestamp and no-lookahead constraints for BBO fields, session context, and
  label references;
- non-zero cost profile review under
  `cmv_futcore_pilot_three_layer_session_stress_v1`, with `zero_cost`
  diagnostic-only and not a criterion basis;
- duplicate-exposure notes so `FUTCORE-P12` can compare spread, microprice,
  depth, quote-quality, liquidity/PA, VWAP/session, and regime overlaps.

## Boundaries

The drafts cite existing BBO feature-family primitive names and the locked P03
input-pack ids by reference. They do not read raw provider data, BBO rows,
feature values, label values, Parquet files, SQLite registries, runtime
diagnostics, or broker/account surfaces. Any missing BBO FeaturePack binding
or non-5m LabelSpec binding is deferred to `FUTCORE-P13` and `FUTCORE-P15`
rather than assumed available.
