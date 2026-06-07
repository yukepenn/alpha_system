# FUTCORE-P17 VWAP / Session Diagnostics

`FUTCORE-P17` records value-free VWAP/session diagnostics for the
`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` family diagnostics gate.

## Scope

Covered StudySpecs:

- `sspec_ab3cbb830a2cede5485de19b` / `aspec_b40aee52d4399dd5b855a6ed`:
  RTH reclaim of running VWAP after the opening window.
- `sspec_8b8037013e7b3c14fd5b2844` / `aspec_43cd6c154bca2fcc419eee83`:
  RTH open location versus completed ETH VWAP, then first eligible running RTH
  VWAP relationship.

Diagnostics used the Research Runtime tool surface only: runtime entry/input
resolution, factor diagnostics, label diagnostics, session split diagnostics,
cost stress diagnostics, `RuntimeToolResult`, and `RuntimeRunSummary`.

The resolved locked inputs are the two P03/P14 session-context FeaturePacks and
the locked 5m LabelPack. No source primitive, runtime, feature, label, data,
broker, execution, or CLI code was edited.

## Reports

Commit-eligible report artifacts:

- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/README.md`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/FUTCORE-P17_vwap_session_summary.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_ab3cbb830a2cede5485de19b/runtime_reports.json`
- `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_8b8037013e7b3c14fd5b2844/runtime_reports.json`

The joined 5m runtime input surface contains 6,862 observations for the locked
development partition. In this lock, all joined observations classify outside
RTH: `full_session` and `ETH_only` each have 6,862 observations; `RTH`,
`RTH_only`, and `RTH_with_ETH_context` have zero eligible joined observations.
Those zero-count cells are preserved as diagnostics output rather than filled by
substitution.

## Session And Horizon Matrix

Each report contains the required session views:

`full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`,
`pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.

Each report also records the primary horizon matrix for `5m`, `10m`, `15m`,
and `30m`. The 5m cells resolve through the locked LabelPack. The `10m`, `15m`,
and `30m` cells are recorded as unresolved label-pack cells because no locked
LabelVersion for those horizons resolves in this phase. The `1m` and `3m`
horizons are flagged diagnostic-only and are not a promotion basis.

## VWAP Timing Boundary

Running VWAP and running session aggregates are point-in-time inputs only and
must carry `available_ts`. Final-session VWAP, high, and low are completed
session context only and are not used intraday before the relevant session has
ended.

For `sspec_ab3cbb830a2cede5485de19b`, no locked running VWAP or reclaim-event
FeaturePack resolves. For `sspec_8b8037013e7b3c14fd5b2844`, no locked completed
ETH VWAP or first-RTH running VWAP FeaturePack resolves. Therefore the
VWAP-specific signal-probe diagnostics are inconclusive. The runtime reports do
not substitute session-minute or RTH-flag context as a VWAP signal.

## Cost Boundary

Cost diagnostics use the pinned nonzero profiles `base`, `stress_1`,
`stress_2`, and `double_cost`. Thin-session stress is represented through the
runtime `ETH` and `ILLIQUID` session penalties for ETH, pre-RTH, and post-RTH
views where the runtime supports the overlay.

`zero_cost` is recorded only as diagnostic context and is not a promotion basis.
Cost outputs are representative session-view unit-fill sensitivity summaries;
they are not signal outcome, deployment, broker, order, or capital-allocation
evidence.

## Boundary Confirmation

The diagnostics are value-free summary and metadata artifacts only. They include
counts, split keys, report references, pack ids, and runtime statuses, but no
row-level feature values, label values, provider responses, heavy artifacts, or
local run artifacts. No promotion decision, reviewer action, PR, merge, live
operation, paper operation, broker call, order routing, or deployment action was
performed by the executor.
