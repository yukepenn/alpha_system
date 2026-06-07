# AlphaSpec Critique

```yaml
draft_id: "aspec_928e60d5096d2383a25f66c6"
family: "liquidity_pa"
title: "Wick rejection beyond prior high or low"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_03.md"
drafter_role: "Hypothesis Scout:rq.p10.liquidity_pa_drafting:wick_rejection_sweep"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft records fixed body/wick ratios and objective level availability rather than subjective chart annotations."
  - "It remains close to accepted close-back-inside and broad sweep exposure; revise to define whether wick rejection is a diagnostic flag or the primary trigger."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: objective PA rule requirement and ambiguous level exclusions"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md: AlphaSpec quality and duplicate-exposure hints"
duplicate_exposure_hint: "pa-wick-sweep; compare against accepted draft 02 and broad sweep draft 01."
flags:
  - "no_lookahead_route: completed-bar wick/body inputs and prior levels need audit."
  - "budget_route: revise due two-seat rounded liquidity allocation."
```
