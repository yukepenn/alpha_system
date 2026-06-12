---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P235500_FUTSUB_SESSION_RESET_TRUTH_REPOINT
lane: yellow
status: in_progress
---

# P235500_FUTSUB_SESSION_RESET_TRUTH_REPOINT: session truth for the remaining session-conditioned families

## Purpose

Deterministic registry evidence (probe 2026-06-11, /tmp/staleness_probe3.out):
REGISTERED feature contracts declaring `reset_on_session=true` with
`session_label` among inputs and NO `field_roles` exist for:

- `liquidity_structure_*` (range_contraction, prior_high/low_distance, sweep
  and failed-breakout flags) — structure family
- `bbo_tradability_spread_zscore` — bbo family
- `base_ohlcv_atr`, `base_ohlcv_trendiness`, `base_ohlcv_rolling_volume` —
  ohlcv family
- 8 `cross_market_*` reset/return features — cross_market family

All were materialized while the canonical `session_label` column was a
degenerate static constant ("ETH" config copy, P183000 finding), so their
contractual session resets never fired: values diverge from contracts.
Additionally, P27 re-lock GAPPED 2 of 6 kill-shot studies because those
records lack the accepted session-metadata role marker
(`label_as_feature_input:feature_pack_refs[0]:session_label`,
`runtime/input_resolver.py:1214-1246` + `_is_exempt_session_field`
:1870-1889; required marker per `_field_roles_from_metadata` :1824-1829 and
SESSION_LABEL_GUARD.md).

This phase is the CODE half (same proven pattern as P183000/P194500/P210000).
A separate coordinator data-op phase re-materializes, deprecates, and
re-locks.

## Scope (in-bounds)

1. **Session truth repoint** — every compute path for the families above
   must derive session segmentation from the shared truth
   (`src/alpha_system/data/foundation/sessions.py::classify_session_timestamp`
   with template `session_cme_index_futures_eth`) instead of trusting the
   canonical `session_label` column:
   - reference family code: `features/families/structure/family.py`,
     `features/families/bbo/family.py`, `features/families/ohlcv/family.py`
     (atr/trendiness/rolling_volume paths), `features/families/cross_market/**`
   - fast twins: `features/fast/liquidity_pa_structure.py`,
     `features/fast/bbo_tradability.py`, `features/fast/regime_vol_compression.py`,
     `features/fast/volume_activity.py`, and the cross_market fast twin if one
     exists
   - Where P183000/P194500 already repointed a path, VERIFY and leave alone.
   - Reference and fast twins must repoint in THIS phase together so parity
     gates stay green.
2. **Role markers**: add `field_roles` with `"session_label": "SESSION_METADATA"`
   (consistent with `features/families/session/family.py:523,562` and
   SESSION_LABEL_GUARD.md) to the `_input_metadata()` of each family above
   wherever `session_label` is a declared input field.
3. **Session-provenance identity** (P210000 pattern): session-conditioned
   specs (those with `reset_on_session=true` or session-value-consuming
   logic) include the session template id + resolved window parameters in
   their identity contract so re-materialization yields NEW fvids.
   Non-session-conditioned features must NOT rotate — over-rotation guard
   test required (e.g. plain `returns`, `volume_zscore`, `rolling_range`
   registered with reset=false keep bit-identical identity).
4. **Absolute-truth tests** (fixtures must NOT implement the property under
   test):
   - reset actually fires at an RTH/ETH boundary on a synthetic frame whose
     session labels come from timestamps spanning the boundary
     (RTH [08:30,15:00) America/Chicago);
   - DST correctness: RTH open at 14:30Z under EST and 13:30Z under EDT;
   - resolver acceptance: a record built from the new contracts passes
     `_is_exempt_session_field` / does NOT trip `label_as_feature_input`
     for `session_label` (unit-level, temp registry);
   - parity: fast vs reference equality on the synthetic boundary frame for
     at least one repointed feature per family.
5. Handoff records the data-op expectation: affected packs re-materialize to
   NEW fvids; old rows get sanctioned coordinator deprecation with
   replacement pointers; P27 re-lock tooling re-runs afterward.

## Hard constraints

- FORBIDDEN: `src/alpha_system/labels/**`, canonicalize/dataset configs,
  registry write-path/schema changes, `governance/duplicate_exposure.py`,
  `runtime/input_resolver.py` (the guard is correct; satisfy it, never
  modify it), historical evidence under `research/futures_core_alpha_pilot_v1/**`.
- No blanket identity rotation (over-rotation guard mandatory).
- No values/SQLite/runs committed; explicit staging only.
- Do NOT run any `git worktree` command; do not modify .git config.
- Research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "identity or session or parity or structure or bbo or regime or volume or cross_market" -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Full-suite green modulo the 3 known pre-existing env failures; exact counts
in the handoff.

## Done criteria

- All four families' reference + fast paths derive sessions from the shared
  truth; role markers present; session-conditioned identities rotate and
  unconditioned do not; absolute-truth + parity + resolver-acceptance tests
  green; full validation green; truthful handoff; fresh adversarial review
  PASS or PASS_WITH_WARNINGS under
  `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
