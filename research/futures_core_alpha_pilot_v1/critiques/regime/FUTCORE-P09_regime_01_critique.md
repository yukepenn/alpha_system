# AlphaSpec Critique

```yaml
draft_id: "aspec_eb962fc197eaf3955c5e4711"
family: "regime"
title: "Trendiness, volatility, and range-compression gate for momentum versus reversion"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_01.md"
drafter_role: "Hypothesis Scout:rq.p09.regime_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "The draft states computable activation logic for momentum, reversion, and inactive transition states, satisfying the regime family requirement."
  - "Point-in-time regime inputs, session boundaries, label timing, non-zero cost profiles, and duplicate-exposure caveats are declared."
  - "Selected as the single rounded regime representative because it is the broadest but still explicit canonical regime gate."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: regime activation logic, point-in-time inputs, and inactive-state handling"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: regime-gated momentum versus reversion family"
duplicate_exposure_hint: "regime-trend-vol-range; compare against other broad trend/volatility filters and cross-market trend context."
flags:
  - "no_lookahead_route: regime metrics and labels require available_ts/label_available_ts audit."
  - "p13_p15_gap_route: non-5m labels and any unmaterialized regime primitives need audited binding."
```
