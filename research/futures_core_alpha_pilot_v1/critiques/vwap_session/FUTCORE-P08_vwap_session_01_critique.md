# AlphaSpec Critique

```yaml
draft_id: "aspec_b40aee52d4399dd5b855a6ed"
family: "vwap_session"
title: "RTH running-VWAP reclaim after opening window"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_01.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "accept-for-StudySpec"
reasons:
  - "P05 fields are complete and the draft cleanly distinguishes running_vwap_so_far from final-session VWAP."
  - "The reclaim event is objective, completed-bar based, and more specific than generic VWAP distance buckets."
  - "Selected as one of two VWAP/session representatives under the 20% accepted budget."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: running-vs-final VWAP and session aggregate lookahead rules"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: VWAP/session family priority"
duplicate_exposure_hint: "vwap-reclaim-reject; compare against drafts 02 and 03."
flags:
  - "no_lookahead_route: opening-window and running VWAP availability must be audited."
  - "p13_p15_gap_route: non-5m horizons need audited label binding before diagnostics."
```
