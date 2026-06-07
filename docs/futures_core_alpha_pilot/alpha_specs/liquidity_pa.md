# Liquidity Sweep / Objective PA AlphaSpec Batch

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P10`  
Family: `liquidity_sweep_failed_breakout`  
Status: draft evidence only

`FUTCORE-P10` records six value-free governance `AlphaSpec` drafts for the
liquidity sweep / failed-breakout / objective price-action family. The
`FUTCORE-P05` protocol quota is minimum 4, target 6, maximum 6; this batch uses
the target count and does not reallocate budget from another family.

No draft is implemented, run, reviewed, promoted, or converted into a StudySpec
in this phase.

## Draft Index

| File | AlphaSpec id | Instruments | Focus |
| --- | --- | --- | --- |
| `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_01.md` | `aspec_1c1cfee8bedf55ced10a391e` | ES, NQ, RTY | Prior high/low liquidity sweep against a causal 20-bar range. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_02.md` | `aspec_df2d040e45564c259ef3de6d` | ES, NQ, RTY | Sweep followed by close back inside the fixed prior range. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_03.md` | `aspec_928e60d5096d2383a25f66c6` | ES, NQ, RTY | Wick rejection beyond a prior level with fixed body/wick ratios. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_04.md` | `aspec_bc9bbcd07669384e51b1661f` | ES, NQ, RTY | Post-sweep reversal displacement relative to prior median true range. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_05.md` | `aspec_55c1351d04054c943c2c3721` | ES, NQ, RTY | Compression breakout from a fixed 8-bar compression boundary. |
| `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_06.md` | `aspec_39ffc190cfbfa6ba0b1a2a25` | ES, NQ, RTY | Failed-breakout reversal back inside a fixed boundary. |

## Common Rule Contract

Every draft defines objective, computable rules for sweep, close-back-inside,
wick rejection, displacement, compression, breakout, and failed-breakout
conditions. Prior high/low levels are available only after the contributing
20 completed one-minute bars have `available_ts`; compression boundaries are
available only after the contributing 8 completed bars have `available_ts`.
Rows with missing, stale, degenerate, cross-boundary, or ambiguous reference
levels are excluded.

Primary horizons are `5m`, `10m`, `15m`, and `30m`. `1m` and `3m` are
execution-fragile diagnostics only. Extended intraday horizons are diagnostics
only, and no modeled holding interval may cross the exchange maintenance or
trade-date break.

Session views follow the P02/P05 matrix. `RTH` and `RTH_only` are primary
decision views; `RTH_with_ETH_context` is in scope only when the ETH context is
point-in-time or completed. `full_session`, `ETH_only`, `ETH_evening`,
`ETH_overnight`, `pre_RTH`, and `post_RTH` are diagnostic or coverage views
with thin-session caveats where applicable.

The drafts cite `CostModelVersion`
`cmv_futcore_pilot_three_layer_session_stress_v1` with exactly `zero_cost`,
`base`, `stress_1`, `stress_2`, and `double_cost`. `zero_cost` is
diagnostic-only and cannot support retaining or advancing a draft that fails
required non-zero profiles. ETH, pre-RTH, and post-RTH views require
thin-session overlays.

## Boundaries

The batch records ids, assumptions, objective rules, exclusions, failure modes,
and later-review criteria only. It adds no FeatureRequest, LabelSpec, StudySpec,
diagnostic run, runtime path, broker/live/paper/order behavior, review artifact,
verdict, promotion decision, market-value artifact, or value/heavy/DB file.
