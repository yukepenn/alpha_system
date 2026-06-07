# AlphaSpec Critique

```yaml
draft_id: "aspec_ad998ced05be1a90c92bee1e"
family: "regime"
title: "VWAP-distance expansion gate for momentum versus reversion"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_06.md"
drafter_role: "Hypothesis Scout:rq.p09.regime_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "reject"
reasons:
  - "The draft is structurally complete, but VWAP distance plus broad trendiness is too close to accepted VWAP/session and accepted regime representatives."
  - "Reject as a standalone regime candidate to keep volume/session/VWAP concepts from being double-budgeted across families."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: family boundary and duplicate-exposure rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-025 family budget ignored"
duplicate_exposure_hint: "regime-vwap-distance; duplicates VWAP/session accepted draft 01 unless narrowed."
flags:
  - "no_lookahead_route: future rewrite would need running VWAP and regime metric timing audit."
  - "budget_route: reject as cross-family duplicate, not as result evidence."
```
