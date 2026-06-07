# FUTCORE-P17 VWAP / Session Diagnostics Reports

This directory contains value-free VWAP/session diagnostics artifacts for `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` phase `FUTCORE-P17`.

## Runtime Scope

- StudySpecs covered: `sspec_ab3cbb830a2cede5485de19b` and `sspec_8b8037013e7b3c14fd5b2844`.
- Runtime surfaces used: runtime entry/input resolver, factor diagnostics, label diagnostics, session split diagnostics, cost stress diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.
- Registry-resolved inputs: two session-context FeaturePacks and the locked 5m LabelPack from the P03/P14 lock.
- No raw provider calls, no source primitive edits, no promotion decision, and no heavy or row-level payloads are represented here.

## Interpretation Boundary

VWAP-specific signal/probe diagnostics are inconclusive because the locked registry state for this phase does not resolve a materialized running VWAP, completed ETH VWAP, or VWAP trigger FeaturePack. The 10m, 15m, and 30m primary horizon cells are recorded as unresolved label-pack cells; the 1m and 3m horizons are diagnostic-only fragile horizons.

`zero_cost` is recorded only as diagnostic context and is not a promotion basis. Nonzero cost diagnostics use the pinned `base`, `stress_1`, `stress_2`, and `double_cost` profiles with thin-session stress mapped through the runtime `ETH` and `ILLIQUID` session penalties.
