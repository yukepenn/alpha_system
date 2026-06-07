# VWAP / Session AlphaSpec Batch

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P08`  
Family: VWAP / session auction  
Status: draft batch for later independent critique

`FUTCORE-P08` adds eight value-free governance `AlphaSpec` draft payloads under
`research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/`. The batch
uses the family target and cap from the `FUTCORE-P05` protocol: minimum six,
target eight, maximum eight.

## Draft Coverage

| Draft | Focus |
| --- | --- |
| `FUTCORE-P08_vwap_session_01.md` | RTH running-VWAP reclaim after the opening window. |
| `FUTCORE-P08_vwap_session_02.md` | Objective running-VWAP reject / close-back-side event. |
| `FUTCORE-P08_vwap_session_03.md` | Bucketed distance to running VWAP. |
| `FUTCORE-P08_vwap_session_04.md` | Completed opening range with running-VWAP confluence. |
| `FUTCORE-P08_vwap_session_05.md` | Completed overnight high/low context with running RTH VWAP. |
| `FUTCORE-P08_vwap_session_06.md` | RTH gap construction with first eligible running-VWAP context. |
| `FUTCORE-P08_vwap_session_07.md` | RTH open versus completed ETH VWAP. |
| `FUTCORE-P08_vwap_session_08.md` | Diagnostic pre-RTH/post-RTH transition distance to running VWAP. |

## Common Boundaries

Every draft distinguishes `running_vwap_so_far` under `available_ts` from
final-session VWAP. Final-session VWAP, high, low, range, volume, or any other
final aggregate is forbidden as an intraday input before the relevant session
is complete.

Each draft declares opening-range availability, overnight high/low
availability, gap construction timing, session-transition handling, and final
aggregate lookahead rejection. Primary horizons remain five, ten, fifteen, and
thirty minutes; one-minute and three-minute views are diagnostic-only; extended
intraday views are caveated diagnostics.

The cost contract is
`cmv_futcore_pilot_three_layer_session_stress_v1` with exactly `zero_cost`,
`base`, `stress_1`, `stress_2`, and `double_cost`. `zero_cost` is
diagnostic-only and cannot satisfy any continuation criterion. ETH, pre-RTH,
and post-RTH views carry thin-session overlays.

The batch drafts no StudySpec, FeatureRequest, LabelSpec, diagnostic result,
review, verdict, promotion decision, broker/live/paper/order behavior, or
market-value artifact.
