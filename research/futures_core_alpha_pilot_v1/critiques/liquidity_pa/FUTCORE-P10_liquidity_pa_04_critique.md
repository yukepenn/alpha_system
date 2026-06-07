# AlphaSpec Critique

```yaml
draft_id: "aspec_bc9bbcd07669384e51b1661f"
family: "liquidity_pa"
title: "Post-sweep reversal displacement"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/FUTCORE-P10_liquidity_pa_04.md"
drafter_role: "Hypothesis Scout:rq.p10.liquidity_pa_drafting:sweep_reversal_displacement"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft supplies objective displacement and median true-range rules with completed-bar timing."
  - "It overlaps accepted close-back-inside and failed-breakout reversal candidates; revise to decide whether displacement is an overlay severity flag rather than a separate StudySpec."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: displacement and objective PA requirements"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012 variant explosion"
duplicate_exposure_hint: "pa-sweep-displacement; compare against accepted drafts 02 and 06."
flags:
  - "no_lookahead_route: median true-range window and displacement bar timing need audit."
  - "budget_route: revise to control liquidity/PA variants."
```
