# AlphaSpec Critique

```yaml
draft_id: "aspec_edc47c5593bcaaf6d2d8c42b"
family: "regime"
title: "Completed ETH context gating early RTH regime"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/regime/FUTCORE-P09_regime_03.md"
drafter_role: "Hypothesis Scout:rq.p09.regime_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "The draft states completed ETH context and early RTH activation logic with point-in-time caveats."
  - "It overlaps VWAP/session and session-auction exposure; revise to prove the completed ETH context is only a regime gate and not a separate session family draft."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: regime gates and session context no-lookahead rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: family boundary between regime and VWAP/session"
duplicate_exposure_hint: "regime-eth-rth-session; compare against VWAP/session drafts 06 and 07."
flags:
  - "no_lookahead_route: completed ETH context must be unavailable until the ETH window is complete."
  - "p13_p15_gap_route: non-5m labels and primitive bindings need audit."
```
