# FUTCORE-P15 FeatureRequest / LabelSpec Decision

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P15`  
Decision: **Minimal additions**

## Basis

`FUTCORE-P13` recorded five P15 gap-list items in
`research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`.
`FUTCORE-P14` carried those gap ids into the approved StudySpec pack under
`research/futures_core_alpha_pilot_v1/study_specs/`.

This phase is not a no-op because P14 still defers `P15-G1` through `P15-G5`.
The `10m` and `30m` labels are not P15 gaps: P13/P14 record them as locked
LabelPack members with valid `label_available_ts` metadata. P15 therefore adds
only the missing `15m` LabelSpec binding and four FeatureRequest records for the
missing feature binding groups.

## Minimal Additions

Exactly five governed budget items are recorded, matching the P13 cap and
adding no speculative primitive.

| Gap id | Governed record | Governance id | Implementation outcome |
| --- | --- | --- | --- |
| `P15-G1` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` | `lspec_8ea5c33463a47d467963d216` | `src/alpha_system/labels/families/fixed_horizon/family.py` supports `fwd_ret_15m`; tests cover exact terminal-row matching and `label_available_ts = max(terminal.available_ts, LabelSpec.availability_time)`. |
| `P15-G2` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g2_vwap_session.json` | `freq_c2a4bc747eb9a0602327de2d` | Existing causal OHLCV family code covers running VWAP, anchored VWAP, distance-to-VWAP, and opening-range context with current-row `available_ts` and session-label metadata guards. |
| `P15-G3` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g3_cross_market_derived_state.json` | `freq_54d8ae828e0bf68c675734cb` | Existing cross-market family code covers residual, spread, divergence/agreement, and rotation-state primitives with as-of cross-instrument `available_ts` alignment. |
| `P15-G4` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json` | `freq_65e52467c10ca7dbc01e39bb` | Existing OHLCV and structure families cover trendiness, ATR, prior-boundary, compression, sweep, and failed-breakout state with causal windows. |
| `P15-G5` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` | `freq_9593f8957b283031a62447bf` | Existing BBO family code covers spread, spread ticks, spread zscore, top-book depth, wide/low-depth flags, missing-BBO flag, and bad-quote flag without quote filling. |

## Non-Gaps Kept Out

- `fwd_ret_10m` remains the locked P03/P13 LabelSpec
  `lspec_15c26c4368bb432b0b0dc6e9`; no P15 LabelSpec file is added for it.
- `fwd_ret_30m` remains the locked P03/P13 LabelSpec
  `lspec_65ba5b5c9b4fa37e0e42b6ef`; no P15 LabelSpec file is added for it.

## Boundaries

The additions are governance records, one minimal label-family extension, and
focused unit coverage. They do not materialize feature or label values, edit
consumed primitive packages outside `src/alpha_system/features/**` or
`src/alpha_system/labels/**`, write registry files, read raw provider data, add
diagnostics, or make any alpha, profitability, tradability, paper/live, broker,
production, or capital-allocation claim.
