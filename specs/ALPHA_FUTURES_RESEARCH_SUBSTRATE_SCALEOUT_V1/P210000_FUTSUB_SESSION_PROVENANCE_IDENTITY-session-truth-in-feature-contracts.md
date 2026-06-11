---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P210000_FUTSUB_SESSION_PROVENANCE_IDENTITY
lane: yellow
status: in_progress
---

# P210000_FUTSUB_SESSION_PROVENANCE_IDENTITY: session truth belongs to the feature contract

## Purpose

P183000/P194500 fixed session semantics (timestamp-derived tz-aware RTH from
the shared template truth), but the P194500 review (W1) found that
session-conditioned features whose computation now depends on that truth —
the `vwap_session_auction` pack (`_IS_RTH`-conditioned: opening_range,
overnight-range freeze, session anchoring) and `reset_on_session` OHLCV
features — did NOT rotate their content-addressed identity, because the
session truth is not part of `FeatureSpec.to_identity_dict`. Consequence:
previously materialized REGISTERED values at those ids are semantically
stale, and sanctioned supersession (deprecate → re-materialize) cannot flow
because the recomputed feature claims the SAME id (identity guard collision).

The session window/template is genuinely part of the computational contract:
two features computed under different session truths are different exposures.

## Scope (in-bounds)

1. Include session-truth provenance (the session template id and its
   resolved window parameters, e.g. `session_template_id` +
   `rth_start`/`rth_end`/timezone) in the identity contract of
   session-conditioned feature specs: the `vwap_session_auction` family
   (fast + its reference twin in `features/families/ohlcv/family.py`) and
   `reset_on_session=True` OHLCV features. Features NOT session-conditioned
   must NOT rotate (test this).
2. The session pack itself (`families/session`, `fast/session_calendar_roll`)
   already rotated via template params in P183000 — verify and leave alone
   unless inconsistent.
3. Tests: (a) identity differs between a spec built under the template truth
   vs the legacy constant (or absent) truth; (b) identity UNCHANGED for a
   non-session-conditioned feature (e.g. plain returns) before/after — no
   global identity churn; (c) gate + registration flow: a deprecated old-id
   row plus a new-id registration coexist (supersession works end to end on
   a temp registry).
4. Handoff records the resulting expectation: re-materializing the vwap
   pack post-merge produces NEW fvids; old ones get coordinator deprecation
   with replacement pointers.

## Hard constraints

- FORBIDDEN: `src/alpha_system/labels/**`, canonicalize/dataset configs,
  registry write-path/schema changes, `governance/duplicate_exposure.py`.
- No blanket identity rotation: only session-conditioned features may
  rotate; assertion (b) above is the over-rotation guard.
- No values/SQLite/runs committed; explicit staging only.
- Do NOT run any `git worktree` command; do not modify .git config.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "identity or version or vwap or ohlcv or session" -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Full-suite green modulo the 3 known pre-existing env failures; exact counts
in the handoff.

## Done criteria

- Session truth is part of the identity contract for session-conditioned
  features only; supersession flow proven on a temp registry; no identity
  churn for unconditioned features; full validation green; truthful handoff;
  fresh adversarial review PASS or PASS_WITH_WARNINGS under
  `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
