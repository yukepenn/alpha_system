# AlphaSpec Critique

```yaml
draft_id: "aspec_f2de85c342e1bc2018297ff7"
family: "regime"
title: "Session-transition momentum versus reversion gate"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_05.md"
drafter_role: "Hypothesis Scout:rq.p09.regime_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft declares session-transition inputs, high/low trendiness gates, and cost/session caveats."
  - "It risks becoming a session-transition split rather than a distinct regime gate; revise to keep transition handling as a matrix condition unless a unique gate is proven."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: session-view and regime-transition instability rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: session matrix and thin-session caveats"
duplicate_exposure_hint: "regime-session-transition; compare against VWAP transition and later session-matrix audits."
flags:
  - "no_lookahead_route: transition boundary and regime-input availability audit required."
  - "p13_p15_gap_route: non-5m labels and primitive bindings need audit."
```
