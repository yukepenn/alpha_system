# AlphaSpec Critique

```yaml
draft_id: "aspec_497f906c7b8f8ed80b64f42b"
family: "vwap_session"
title: "RTH gap with first eligible running-VWAP context"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_06.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "revise"
reasons:
  - "Gap timing, prior close/current open references, and running VWAP availability are declared in line with P05."
  - "The gap focus overlaps accepted RTH-open-vs-completed-ETH context; revise to decide whether gap or completed ETH VWAP is the governing session-auction input."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: gap construction timing and session transition handling"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml: finite approved AlphaSpec budget"
duplicate_exposure_hint: "vwap-gap-open; compare against accepted draft 07."
flags:
  - "no_lookahead_route: prior close, current open, and running VWAP timestamps need audit."
  - "budget_route: revise due two-seat VWAP/session cap."
```
