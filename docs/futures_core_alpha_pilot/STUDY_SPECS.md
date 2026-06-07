# Approved StudySpec Pack

`FUTCORE-P14` binds the 10 `FUTCORE-P12` accepted AlphaSpecs to one value-free governance `StudySpec` each. The canonical pack is:

- `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`
- `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`

The pack consumes the locked `FUTCORE-P03` DatasetVersion, FeaturePack, and LabelPack ids/hashes by reference only. It runs no diagnostics and includes no market rows, feature values, label values, costs, returns, signals, or performance evidence.

## StudySpec Set

| Family | AlphaSpecs | StudySpecs | Budget result |
| --- | ---: | ---: | --- |
| Cross-market / relative value | 4 | 4 | Matches 40% accepted-set budget. |
| VWAP / session auction | 2 | 2 | Matches 20% accepted-set budget. |
| Regime momentum / reversion | 1 | 1 | Matches P12 integer-rounding decision for the 15% family. |
| Liquidity sweep / failed breakout / objective PA | 2 | 2 | Matches P12 integer-rounding decision for the 15% family. |
| BBO tradability / confirmation | 1 | 1 | Matches 10% accepted-set budget. |
| **Total** | **10** | **10** | Holds the approved cap `<=10`. |

## Common Binding

- DatasetVersion `dsv_databento_ohlcv_05404069799decb0` with manifest hash `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31`.
- FeatureVersions `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` and `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` with P03 value-content hashes.
- LabelVersion `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` and LabelSpec `lspec_cd6523694c850c9943b2067e` for locked `5m` labels.
- Required sessions: `full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.
- Primary horizons: `5m`, `10m`, `15m`, and `30m`; fragile diagnostics: `1m` sampling-only and `1m`/`3m` execution-fragile.
- Cost profiles: `zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost`; thin-session penalties apply to `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and `post_RTH`.

## Deferred P15 Inputs

P13 identified five bounded gap items that this pack carries forward by id without implementing:

- `P15-G1`: fwd_ret_10m LabelPack binding.
- `P15-G2`: fwd_ret_15m LabelPack binding.
- `P15-G3`: fwd_ret_30m LabelPack binding.
- `P15-G4`: causal OHLCV derived FeaturePack binding for VWAP, anchored VWAP, distance-to-VWAP, opening range, returns, volatility/range, ATR, range position, trendiness, volume overlay, and fixed completed-bar reference levels.
- `P15-G5`: BBO top-book confirmation FeaturePack binding for spread, spread ticks, spread zscore, top-book depth, wide/low-depth/missing/bad-quote flags.

Diagnostics that require a pending horizon label, derived OHLCV primitive, or BBO primitive must stop until `FUTCORE-P15` resolves that binding or records an explicit no-op constraint.

## Guardrails

Every StudySpec declares `variant_budget: 4`. Sessions, horizons, instruments, and cost profiles are evaluation slices, not additional grid knobs. The payloads require `available_ts` / `label_available_ts` ordering, running-vs-final session aggregate separation, cross-instrument availability discipline where applicable, and no holding period across the exchange maintenance / trade-date break.

This document makes no alpha, profitability, tradability, paper/live, broker, production, deployment, or capital-allocation claim.
