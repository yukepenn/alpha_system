# AlphaSpec Critique

```yaml
draft_id: "aspec_43cd6c154bca2fcc419eee83"
family: "vwap_session"
title: "RTH open versus completed ETH VWAP"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_07.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "The draft explicitly distinguishes completed ETH VWAP context from intraday final-session VWAP and records first RTH running VWAP timing."
  - "Selected to cover the RTH-open-vs-ETH requirement while avoiding a separate gap StudySpec candidate."
  - "Acceptance is value-free and only for later StudySpec binding after P13 label/input checks."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: running-vs-final VWAP, completed ETH context, and session transition rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: VWAP/session auction family focus"
duplicate_exposure_hint: "vwap-rth-open-eth; compare against gap draft 06 and overnight context draft 05."
flags:
  - "no_lookahead_route: completed ETH VWAP must be available before RTH open context is used."
  - "p13_p15_gap_route: non-5m horizons need audited label binding before diagnostics."
```
