# AlphaSpec Critique

```yaml
draft_id: "aspec_5abca2fa010fc9e7174e0d7d"
family: "vwap_session"
title: "Pre-RTH/post-RTH transition distance to running VWAP"
source_path: "research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/FUTCORE-P08_vwap_session_08.md"
drafter_role: "Hypothesis Scout:rq.p08.vwap_session_drafting"
critic_role: "AlphaSpec Critic:FUTCORE-P12"
decision: "reject"
reasons:
  - "The draft is mostly a diagnostic transition-window variant of generic distance-to-running-VWAP exposure."
  - "Reject as a standalone StudySpec candidate because thin-session transition diagnostics should be overlays or matrix splits, not a separate accepted family seat."
protocol_refs:
  - "research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md: session-view rules and fragile horizon/session caveats"
  - "campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md: volume/activity and session views as overlays where applicable"
duplicate_exposure_hint: "vwap-transition-distance; duplicates distance bucket draft 03 and session matrix overlays."
flags:
  - "no_lookahead_route: no immediate breach recorded; any future overlay must preserve transition-session available_ts."
  - "budget_route: reject as overlay-only diagnostic, not as alpha evidence."
```
