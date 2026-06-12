# Futures Core Alpha Pilot Cost Model

`FUTCORE-P04` records the value-free `CostModelVersion` and session-specific
cost stress contract for `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`. The canonical
contract is:

- [research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md](../../research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md)

## Version And Binding

- `CostModelVersion`: `cmv_futcore_pilot_three_layer_session_stress_v1`
- Semantic version: `1.0.0`
- Bound by reference to the `FUTCORE-P03` DatasetVersion, FeaturePack, and
  LabelPack ids/hashes.
- Applies to ES/NQ/RTY pilot research diagnostics only.

## Fee Schedule V2

`fee_schedule_cme_equity_index_retail_discount_v2_2026_06_11` supersedes the
Layer-1 placeholder amounts while retaining the v1 contract for history. It
covers ES, NQ, RTY, MES, MNQ, and M2K with USD-per-contract-per-side CME
exchange fee, clearing fee, NFA regulatory fee, and representative public retail
discount-broker commission components. As of 2026-06-11, the all-in per-side
research constants are $1.99 for ES/NQ/RTY and $0.36 for MES/MNQ/M2K. These are
offline public-source research assumptions only, not account-specific broker
terms, live/paper trading approval, or tradability evidence.

## Three Layers

- Layer 1 - hard transaction cost: versioned broker/exchange/clearing/regulatory
  fee schedule constants for the supported CME equity-index futures symbols.
- Layer 2 - spread crossing: point-in-time BBO bid/ask/mid/`spread_ticks`
  methodology, with missing or invalid BBO flagged rather than fabricated.
- Layer 3 - slippage proxy: bucketed adverse-slippage and capacity proxy
  methodology, scaled by profile and session overlays.

## Profiles

The ladder is exactly `zero_cost`, `base`, `stress_1`, `stress_2`, and
`double_cost`.

`zero_cost` is diagnostic-only and never a promotion basis. Non-zero profiles
progress from central assumption through escalating stress, with `double_cost`
as the upper stress bound. Cost and capacity outputs are proxy sensitivities,
not proof of tradability or fill capacity.

## Thin-Session Rules

`ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and `post_RTH` require
stricter spread, slippage, and capacity proxy treatment than comparable RTH
views. ETH evidence is research-in-scope but not trading-approved. The `1m` and
`3m` horizons remain execution-fragile diagnostics only, especially in thin
sessions.

This page adds no runtime behavior, diagnostics, broker/live/paper surface,
provider access, market data, fee amount, or cost result.
