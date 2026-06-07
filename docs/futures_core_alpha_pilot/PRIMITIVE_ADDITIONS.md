# FUTCORE-P15 Primitive Additions

`FUTCORE-P15` resolves the P13 minimal gap list with exactly five governed
primitive budget items. The outcome is **minimal additions**, not a no-op,
because the P14 StudySpecs still carry the P15 gap ids.

## Added Governed Records

| P13 gap | Record | Governance id | Notes |
| --- | --- | --- | --- |
| `P15-G1` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_10m.json` | `lspec_297ba9c00b50043020a1945e` | Fixed-horizon `10m` label binding. Existing label code already supported it. |
| `P15-G2` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` | `lspec_c9e388fde3d860ae012b2ad0` | Fixed-horizon `15m` label binding. Adds minimal `fwd_ret_15m` support and tests. |
| `P15-G3` | `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_30m.json` | `lspec_85a5a466430a814f6a608b2c` | Fixed-horizon `30m` label binding. Existing label code already supported it. |
| `P15-G4` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g4_causal_ohlcv_derived.json` | `freq_ef650ea8306d52dd9edfb6a3` | Grouped causal OHLCV/structure request for VWAP, returns, volatility/range, ATR, range position, trendiness, volume zscore, and prior/compression range context. Existing feature code already supported these families. |
| `P15-G5` | `research/futures_core_alpha_pilot_v1/feature_requests/p15_g5_bbo_top_book_confirmation.json` | `freq_5ed19554444f449b7c2da377` | Grouped BBO top-book confirmation request for spread, spread ticks, spread zscore, top-book depth, and quote-quality flags. Existing feature code already supported these primitives. |

## Code Change

The only primitive code change is the minimal `fwd_ret_15m` addition in
`src/alpha_system/labels/families/fixed_horizon/family.py`. It uses the
existing fixed-horizon calculation path:

- terminal row must be exactly `source.event_ts + 15m`;
- rows without an exact terminal row are excluded;
- `label_available_ts = max(terminal.available_ts, LabelSpec.availability_time)`;
- the label remains offline and labels-only.

No feature code was changed. No feature values, label values, provider
responses, Parquet/Arrow/Feather files, SQLite/DB files, diagnostics outputs,
or local run artifacts are recorded here.
