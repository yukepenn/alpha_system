# AlphaSpec Critique

```yaml
draft_id: "aspec_df2d040e45564c259ef3de6d"
family: "liquidity_pa"
title: "Liquidity sweep followed by close-back-inside confirmation"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_02.md"
drafter_role: "Hypothesis Scout:rq.p10.liquidity_pa_drafting:close_back_inside"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "The draft uses objective computable sweep and close-back-inside rules with timestamped reference levels."
  - "Accepted as one liquidity/PA representative because it narrows broad sweep exposure into a deterministic confirmation rule."
  - "Volume/activity appears only as an overlay/split and does not create a standalone family."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: liquidity sweep, close-back-inside, objective PA, and overlay rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: liquidity sweep / failed breakout / objective PA family"
duplicate_exposure_hint: "pa-sweep-closeback; compare against draft 01, wick draft 03, and VWAP reject draft 02."
flags:
  - "no_lookahead_route: reference level and close-back-inside deadline need available_ts audit."
  - "p13_p15_gap_route: non-5m labels need audited binding."
```
