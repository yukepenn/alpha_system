# Regime Momentum/Reversion AlphaSpec Batch

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P09`  
Family: `regime_momentum_reversion`  
Status: draft evidence only

`FUTCORE-P09` records six value-free governance `AlphaSpec` drafts for the
regime-gated momentum-versus-reversion family. The family quota from the
`FUTCORE-P05` protocol is minimum 4, target 6, maximum 6; this batch uses the
target count and does not reallocate budget from any other family.

No draft is implemented, run, reviewed, promoted, or used for broker, paper,
live, order-routing, deployment, or capital behavior in this phase.

## Draft Index

| File | AlphaSpec id | Instruments | Momentum gate | Reversion gate |
| --- | --- | --- | --- | --- |
| `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_01.md` | `aspec_eb962fc197eaf3955c5e4711` | ES, NQ, RTY | High completed-bar trendiness with non-stressed volatility and no range compression. | Low trendiness or range compression after a failed directional extension. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_02.md` | `aspec_7db3a23e98ca7ff99b1805c6` | NQ, RTY | Rolling-volatility and ATR expansion with rising trendiness and completed return agreement. | Volatility contraction with compressed range and low trendiness. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_03.md` | `aspec_edc47c5593bcaaf6d2d8c42b` | ES, NQ | Completed ETH direction agrees with early RTH high-trendiness regime in `RTH_with_ETH_context`. | Early RTH low trendiness or range compression rejects completed ETH context. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_04.md` | `aspec_d26b7959b12be5b53f969067` | ES, NQ, RTY | Range compression releases beyond a causal rolling range boundary with high trendiness. | Compression release fails back inside the causal range or appears in low trendiness. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_05.md` | `aspec_f2de85c342e1bc2018297ff7` | RTY, ES | Allowed session transition with high trendiness and volatility expansion after the boundary. | Allowed session transition with low trendiness, volatility contraction, or range compression after the initial move. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_06.md` | `aspec_ad998ced05be1a90c92bee1e` | ES, NQ, RTY | Point-in-time VWAP distance expands with high trendiness and non-stressed volatility. | VWAP distance is extended while trendiness is low or rolling range is compressed. |

## Declared Diagnostics

Later StudySpec and diagnostics phases must record, by reference only:

- computable point-in-time activation counts for momentum, reversion, and
  inactive transition states;
- per-regime sample and coverage caveats by instrument, session view, and
  horizon;
- regime-transition instability near thresholds or session boundaries;
- duplicate exposure to broad trend filters, broad volatility filters,
  VWAP/session context, liquidity/PA compression, and other regime drafts;
- valid `available_ts` and `label_available_ts` ordering for every input and
  label reference;
- non-zero cost sensitivity coverage for `base`, `stress_1`, `stress_2`, and
  `double_cost`, with `zero_cost` retained only as diagnostic contrast.

## Boundaries

The drafts cite the P04 `CostModelVersion`
`cmv_futcore_pilot_three_layer_session_stress_v1` and the locked P03 input-pack
ids by reference. They do not read raw provider data, feature values, label
values, Parquet files, SQLite registries, runtime diagnostics, or broker/account
surfaces. Missing non-5m labels and any unmaterialized regime primitives are
deferred to `FUTCORE-P13` and `FUTCORE-P15` rather than assumed available.
