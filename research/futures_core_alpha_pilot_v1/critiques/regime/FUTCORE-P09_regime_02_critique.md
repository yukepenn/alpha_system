# AlphaSpec Critique

```yaml
draft_id: "aspec_7db3a23e98ca7ff99b1805c6"
family: "regime"
title: "Volatility and ATR expansion gate"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_02.md"
drafter_role: "Hypothesis Scout:rq.p09.regime_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft declares causal volatility, ATR, trendiness, and compression inputs under available_ts."
  - "It overlaps accepted draft 01 as another broad volatility/trend gate; revise to define what additional activation state survives duplicate-exposure review."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: regime activation and duplicate-exposure requirements"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-014 duplicate exposure"
duplicate_exposure_hint: "regime-vol-expansion; compare against accepted regime draft 01."
flags:
  - "no_lookahead_route: rolling volatility/ATR windows need causal-window audit."
  - "p13_p15_gap_route: non-5m labels and primitive bindings need audit."
```
