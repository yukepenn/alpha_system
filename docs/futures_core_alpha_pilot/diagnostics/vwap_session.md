# VWAP / Session Diagnostics

`FUTCORE-P17` records value-free diagnostics for the `vwap_session` StudySpec subset of `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`.

## Scope

The family subset contains two StudySpecs:
- `sspec_ab3cbb830a2cede5485de19b` / `aspec_b40aee52d4399dd5b855a6ed`: RTH reclaim of running VWAP after the opening window using only running, available intraday aggregates.
- `sspec_8b8037013e7b3c14fd5b2844` / `aspec_43cd6c154bca2fcc419eee83`: RTH open location versus completed ETH VWAP, then first eligible running RTH VWAP relationship.

## Runtime Surface

Diagnostics were produced through the Research Runtime surfaces: input resolution, factor diagnostics, label diagnostics, session-split diagnostics, the SignalProbeSpec contract gate, cost stress, RuntimeToolResult, and RuntimeRunSummary. The runtime resolved the locked DatasetVersion plus the P03/P14 session-context FeaturePacks and 5m LabelPack. No raw provider path or external provider call was used.

## Result Shape

- Label and session-split diagnostics summarize the locked 5m/session-context Parquet side as scalar runtime reports.
- VWAP factor and signal-probe diagnostics are blocked because no locked running or completed VWAP FeaturePack is bound.
- The 10m, 15m, and 30m primary horizon cells remain blocked for evidence because they have governed P15 LabelSpecs but no locked Parquet LabelPack binding in the P03/P14 input pack.
- Cost stress is recorded as a runtime cost report with zero fills, plus a value-free policy matrix for zero-cost and thin-session overlays.

## Running vs Final VWAP

Running VWAP is admissible only as a point-in-time running aggregate with `available_ts` no later than the decision timestamp. Final-session VWAP is not an intraday input. Completed ETH VWAP may be used only after the ETH session completes. P17 did not approximate any missing VWAP primitive from raw bars or session metadata.

## Artifacts

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/INDEX.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/session_horizon_matrix.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/cost_profile_matrix.json`

The reports are value-free: no per-row feature, label, return, signal, cost, market, Parquet, SQLite, DBN, Zstd, provider, cache, log, or run-local payload is committed.
