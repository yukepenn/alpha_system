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

## Three Layers

- Layer 1 - hard transaction cost: broker/exchange/clearing/regulatory fee
  placeholders with declared units and dated/versioned schedule references where
  later reviewed config supports them.
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
