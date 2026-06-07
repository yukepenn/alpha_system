# AlphaSpec Critique

```yaml
draft_id: "aspec_4a0e170d68918d3c787db230"
family: "vwap_session"
title: "Opening-range exit with running-VWAP confluence"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_04.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft correctly declares opening-range availability only after the window closes and rejects final-session aggregates."
  - "It overlaps liquidity/PA breakout and opening-range ideas; revise to keep VWAP confluence as the primary family reason rather than a standalone price-action breakout."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: opening-range availability and family-specific VWAP declarations"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: VWAP/session versus liquidity/PA family boundaries"
duplicate_exposure_hint: "vwap-opening-range-confluence; compare against liquidity compression/breakout drafts."
flags:
  - "no_lookahead_route: opening range and running VWAP available_ts audit required."
  - "budget_route: revise due VWAP accepted cap and cross-family overlap."
```
