# FUTCORE-P15 Primitive Additions

`FUTCORE-P15` resolves the P13 minimal gap list with exactly five governed
budget items. The outcome is **minimal additions**, not a no-op, because the
P14 StudySpecs still carry `P15-G1` through `P15-G5`.

## Added Governed Records

| P13 gap | Record | Governance id | Notes |
| --- | --- | --- | --- |
| `P15-G1` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` | `lspec_8ea5c33463a47d467963d216` | Fixed-horizon `15m` close-to-close forward-return LabelSpec. The label remains offline and labels-only. |
| `P15-G2` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g2_vwap_session.json` | `freq_c2a4bc747eb9a0602327de2d` | VWAP/session request for running VWAP, anchored VWAP, distance-to-VWAP, and opening-range context. |
| `P15-G3` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g3_cross_market_derived_state.json` | `freq_54d8ae828e0bf68c675734cb` | Cross-market derived-state request for residual, spread, divergence/agreement, and rotation context. |
| `P15-G4` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json` | `freq_65e52467c10ca7dbc01e39bb` | OHLCV/structure request for trendiness, ATR, prior-boundary, compression, sweep, and failed-breakout state. |
| `P15-G5` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` | `freq_9593f8957b283031a62447bf` | BBO top-book confirmation request for spread, depth, quote-quality, wide-spread, and low-depth context. |

`fwd_ret_10m` and `fwd_ret_30m` are intentionally not added here because P13 and
P14 record them as locked P03/P13 LabelPack members.

## Code And Tests

The only label primitive extension is `fwd_ret_15m` in
`src/alpha_system/labels/families/fixed_horizon/family.py`. It uses the existing
fixed-horizon calculation path:

- terminal row must be exactly `source.event_ts + 15m`;
- rows without an exact terminal row are excluded;
- `label_available_ts = max(terminal.available_ts, LabelSpec.availability_time)`;
- the label remains offline and labels-only.

No feature source code was changed for `P15-G2` through `P15-G5`; the existing
OHLCV, cross-market, structure, and BBO feature families already expose the
needed causal primitives. Focused tests bind the P15 FeatureRequests to those
families and check point-in-time `available_ts` behavior.

No feature values, label values, provider responses, Parquet/Arrow/Feather
files, SQLite/DB files, diagnostics outputs, or local run artifacts are recorded
here.
