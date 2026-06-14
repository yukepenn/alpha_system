# SSRL-P03 First-Light Worked Example

SSRL-P03 declares one context-not-trigger setup and records two value-free readouts:

- `research/strategy_shaped_lane_v0/first_light/mechanism_card.json`
- `research/strategy_shaped_lane_v0/first_light/setup_spec.json`
- `research/strategy_shaped_lane_v0/first_light/EVIDENCE.json`
- `research/strategy_shaped_lane_v0/de_stack/EVIDENCE.json`

## First-Light Setup

The worked example is a range-contraction context plus a separate failed-high-breakout
trigger over a fixed `target_before_stop` path label:

- `entry_context.factor_id`: `liquidity_structure_range_contraction`
- `event_trigger.factor_id`: `liquidity_structure_failed_high_breakout_flag`
- `target.path_outcome`: `target_before_stop`
- `hold_time.max_minutes`: `120`
- `stamp`: `EXPLORATORY`

The P03 helper in `src/alpha_system/research/first_light.py` compiles this
`SetupSpec` with the SSRL-P02 conditional probe and does not change the compiler.
Synthetic tests exercise the full readout shape: path-label outcome source,
variant-ledger binding, surrogate-FDR gate, per-factor power statement, and
EXPLORATORY refusal by the trusted promotion guard.

The executor environment exposed matching materialization manifests under
`ALPHA_DATA_ROOT`, but no sanctioned Parquet reader module was importable. The
committed first-light evidence therefore records `INCONCLUSIVE` / `DATA_GAP` and
does not fabricate row values.

## De-Stack Read

The de-stack read records the settler-flagged isolated
`vwap_session.factor_session_minute` single-factor diagnostic through the existing
`single_factor_threshold` template. The evidence records the isolated IC read,
observation count, surrogate-FDR gate, and power statement without changing the
single-factor engine.
