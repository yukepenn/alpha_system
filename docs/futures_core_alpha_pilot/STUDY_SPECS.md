# Approved StudySpec Pack

`FUTCORE-P14` binds the 10 `FUTCORE-P12` accepted AlphaSpecs to one value-free governance `StudySpec` each. The canonical pack is:

- `research/futures_core_alpha_pilot_v1/study_specs/study_specs.json`
- `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md`
- `research/futures_core_alpha_pilot_v1/study_specs/sspec_*.json`

The pack consumes the locked `FUTCORE-P03` DatasetVersion, FeaturePack, and LabelPack ids/hashes by reference only, as corrected by the `FUTCORE-P13` data-contract audit. It runs no diagnostics and includes no market rows, feature values, label values, costs, returns, signals, or performance evidence.

## StudySpec Set

| Family | AlphaSpecs | StudySpecs | Budget result |
| --- | ---: | ---: | --- |
| Cross-market / relative value | 4 | 4 | Matches 40% accepted-set budget. |
| VWAP / session auction | 2 | 2 | Matches 20% accepted-set budget. |
| Regime momentum / reversion | 1 | 1 | Matches P12 integer-rounding decision for the 15% family. |
| Liquidity sweep / failed breakout / objective PA | 2 | 2 | Matches P12 integer-rounding decision for the 15% family. |
| BBO confirmation / risk-control overlay | 1 | 1 | Matches 10% accepted-set budget. |
| **Total** | **10** | **10** | Holds the approved cap `<=10`. |

## Common Binding

- DatasetVersion `dsv_databento_ohlcv_05404069799decb0` with manifest hash `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31`.
- P13-corrected FeatureVersion ids are used, including `fver_acbfa7833cb2a07338a91abe750c934d9e9922477ad96e3ea3e0c001970573f9` for `base_ohlcv_rth_flag` and `fver_fd739ad918a557d2f4ca45d54c9ea700cc0168ad9c6fec90151d87479bf1b858` for `base_ohlcv_session_minute`; stale source-draft feature ids are not bound.
- Base OHLCV FeaturePack refs are included where P13 marks them required: returns, log returns, rolling volatility, rolling range, range position, and volume zscore.
- LabelVersion refs bind `5m`, `10m`, and `30m`; `15m` remains deferred to `P15-G1`.
- Required sessions: `full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.
- Primary horizons: `5m`, `10m`, `15m`, and `30m`; fragile diagnostics: `1m` sampling-only and `1m`/`3m` execution-fragile.
- Cost profiles: `zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost`; thin-session penalties apply to `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and `post_RTH`.

## Deferred P15 Inputs

P13 identified five bounded gap items that this pack carries forward by id without implementing:

- `P15-G1`: `fwd_ret_15m` LabelPack binding.
- `P15-G2`: VWAP/session FeaturePack binding.
- `P15-G3`: cross-market derived-state FeaturePack binding.
- `P15-G4`: additional base-OHLCV derived-state FeaturePack binding for regime and liquidity/PA.
- `P15-G5`: BBO top-book confirmation FeaturePack binding.

Diagnostics that require a pending horizon label, derived OHLCV primitive, VWAP/session primitive, cross-market derived state, or BBO primitive must stop until `FUTCORE-P15` resolves that binding or records an explicit no-op constraint.

## Guardrails

Every StudySpec declares `variant_budget: 4`. Sessions, horizons, instruments, and cost profiles are evaluation slices, not additional grid knobs. The payloads require `available_ts` / `label_available_ts` ordering, running-vs-final session aggregate separation, cross-instrument availability discipline where applicable, objective price-action timestamp rules, BBO validity flags when applicable, and no holding period across the exchange maintenance / trade-date break.

This document makes no alpha, profitability, paper/live, broker, production, deployment, or capital-allocation claim.
