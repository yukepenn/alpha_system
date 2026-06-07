# AlphaSpec Critique

```yaml
draft_id: "aspec_668088ee803855ce3e5617e6"
family: "vwap_session"
title: "Distance-to-running-VWAP buckets"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_03.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "reject"
reasons:
  - "The draft is structurally complete, but generic distance buckets are a baseline exposure that several event-specific VWAP drafts already refine."
  - "Reject as standalone to avoid a broad bucket grid becoming the seed of variant expansion in P14/P24."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: finite variant budget and final aggregate rejection"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md: R-012 variant explosion"
duplicate_exposure_hint: "vwap-distance-baseline; duplicate reference for drafts 01, 02, and 08."
flags:
  - "no_lookahead_route: no immediate breach recorded; future use must preserve running VWAP only."
  - "budget_route: reject as broad duplicate, not as a result judgment."
```
