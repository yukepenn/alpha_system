# FUTCORE-P17 VWAP / Session Diagnostics Reports

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P17`
Family: `vwap_session`
Artifact type: value-free runtime diagnostics summaries

## Runtime Outcome

The runtime input resolver admitted both VWAP/session StudySpecs against the locked P03/P14 DatasetVersion, the two session-context FeaturePacks, and the locked 5m LabelPack. Label and session-split diagnostics summarize the locked 5m/session-context Parquet side in memory and commit only scalar reports.

VWAP factor and signal-probe diagnostics are blocked by the runtime contracts because no locked running or completed VWAP FeaturePack is bound to the RuntimeInputPack. The 10m, 15m, and 30m horizon cells are also blocked for evidence because P15 added governed LabelSpecs but no locked Parquet LabelPack binding exists in the P03/P14 pack.

## Study Reports

| StudySpec | AlphaSpec | Factor | Label | Session split | Signal probe | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| `sspec_ab3cbb830a2cede5485de19b` | `aspec_b40aee52d4399dd5b855a6ed` | `DIAGNOSTICS_FAILED` | `DIAGNOSTICS_COMPLETE` | `INCONCLUSIVE` | `BLOCKED` | `INCONCLUSIVE` |
| `sspec_8b8037013e7b3c14fd5b2844` | `aspec_43cd6c154bca2fcc419eee83` | `DIAGNOSTICS_FAILED` | `DIAGNOSTICS_COMPLETE` | `INCONCLUSIVE` | `BLOCKED` | `INCONCLUSIVE` |

## Files

- `summary.json`
- `session_horizon_matrix.json`
- `cost_profile_matrix.json`
- `sspec_ab3cbb830a2cede5485de19b/runtime_input_resolution.json`
- `sspec_ab3cbb830a2cede5485de19b/factor_diagnostics.json`
- `sspec_ab3cbb830a2cede5485de19b/label_diagnostics.json`
- `sspec_ab3cbb830a2cede5485de19b/session_split_diagnostics.json`
- `sspec_ab3cbb830a2cede5485de19b/signal_probe_blocked.json`
- `sspec_ab3cbb830a2cede5485de19b/cost_stress.json`
- `sspec_ab3cbb830a2cede5485de19b/runtime_tool_result.json`
- `sspec_ab3cbb830a2cede5485de19b/runtime_run_summary.json`
- `sspec_ab3cbb830a2cede5485de19b/session_horizon_matrix.json`
- `sspec_8b8037013e7b3c14fd5b2844/runtime_input_resolution.json`
- `sspec_8b8037013e7b3c14fd5b2844/factor_diagnostics.json`
- `sspec_8b8037013e7b3c14fd5b2844/label_diagnostics.json`
- `sspec_8b8037013e7b3c14fd5b2844/session_split_diagnostics.json`
- `sspec_8b8037013e7b3c14fd5b2844/signal_probe_blocked.json`
- `sspec_8b8037013e7b3c14fd5b2844/cost_stress.json`
- `sspec_8b8037013e7b3c14fd5b2844/runtime_tool_result.json`
- `sspec_8b8037013e7b3c14fd5b2844/runtime_run_summary.json`
- `sspec_8b8037013e7b3c14fd5b2844/session_horizon_matrix.json`

## Boundaries

These artifacts are diagnostics only. They embed no per-row market, feature, label, cost, return, or signal payloads; no Parquet, SQLite, provider response, or run-local artifact is committed. They make no promotion, profitability, paper/live, broker, deployment, or capital-use claim.
