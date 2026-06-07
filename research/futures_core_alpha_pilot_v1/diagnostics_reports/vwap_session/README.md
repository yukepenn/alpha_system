# FUTCORE-P17 VWAP / Session Diagnostics Reports

This directory contains value-free VWAP/session diagnostics artifacts for `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` phase `FUTCORE-P17`.

## Runtime Scope

- StudySpecs covered: `sspec_69c22ec5847395ac8e81b5b6` and `sspec_aff70fcbc4b7ff226fcc8149`.
- Runtime surfaces used: runtime entry/input resolver, factor diagnostics, label diagnostics, session split diagnostics, cost stress diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.
- Registry-resolved inputs: six P14 FeaturePacks and three locked LabelPacks from the P03/P13/P14 lock; the 15m LabelSpec has no locked LabelVersion in this pack.
- No raw provider calls, source primitive edits, promotion decision, or heavy or row-level payloads are represented here.

## Interpretation Boundary

VWAP-specific signal/probe diagnostics are inconclusive because the locked registry state for this phase does not resolve a materialized running VWAP, completed ETH VWAP, distance-to-VWAP, or VWAP trigger FeaturePack. Session-minute and range-position diagnostics are context summaries only and are not substitutes for a VWAP trigger.

Joined observations by primary horizon: 5m `6862`, 10m `6832`, 15m `0`, and 30m `6712`. The 1m and 3m horizons are diagnostic-only fragile horizons.

`zero_cost` is recorded only as diagnostic context and is not a promotion basis. Nonzero cost diagnostics use the pinned `base`, `stress_1`, `stress_2`, and `double_cost` profiles with thin-session stress mapped through the runtime `ETH` and `ILLIQUID` session penalties.
