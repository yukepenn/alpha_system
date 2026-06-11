---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P194500_FUTSUB_OHLCV_RTH_TRUTH_REPOINT
lane: yellow
status: in_progress
---

# P194500_FUTSUB_OHLCV_RTH_TRUTH_REPOINT: reference OHLCV family adopts the shared session truth

## Purpose

P183000 (merged) fixed the degenerate RTH segmentation by introducing a
single timestamp-derived session truth (`data/foundation/sessions.py`) and
repointing the session family, its fast twin, and `fast/vwap_session_auction`.
Its review (P183000-review.md, W1, medium) found the remaining consumer:
`src/alpha_system/features/families/ohlcv/family.py` — the REFERENCE twin
for the vwap/session-auction feature pack — still keys RTH/ETH membership
off the static canonical `session_label` constant. Until it adopts the
shared truth, fast (now correct) and reference (still degenerate) diverge on
real data, so vwap-pack parity validation and any reference recomputation
would be wrong. This must merge BEFORE the vwap_session_auction pack is
re-materialized and before FUTSUB-P27/P28 rely on RTH-conditioned features.

## Scope (in-bounds)

1. `src/alpha_system/features/families/ohlcv/family.py`: replace every
   RTH/ETH membership decision keyed off `session_label` (or any local
   window constant) with the shared truth from
   `data/foundation/sessions.py` (same template, America/Chicago,
   RTH [08:30, 15:00)). `session_label` may remain as input metadata only.
2. Absolute-truth tests for the reference family mirroring P183000's
   pattern: DST boundary (EST + EDT dates), segment edges, and an
   RTH-conditioned output (e.g. opening_range) non-null on an RTH fixture.
3. Parity: fast vwap_session_auction == reference OHLCV family on the same
   fixtures (now both correct; the P183000 fixtures should be reusable).
4. Stale-expectation updates authorized with provenance notes (same basis
   as P183000 section 6); no assertion deleted or weakened.
5. Record in the handoff: the labels 15:00-inclusive close-out-anchor
   boundary note (P183000 review N1) carried into the labels-adoption
   follow-up; and the optional `dt.offset_by("1d")` rollover hardening
   (P183000 review W2) — implement W2 only if trivially safe, else record.

## Hard constraints

- FORBIDDEN: `src/alpha_system/labels/**`, `data/databento/canonicalize.py`,
  dataset configs, registry write-paths/schema.
- `data/foundation/sessions.py` changes additive-only if any are needed.
- No values/SQLite/runs committed; explicit staging only.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "ohlcv or session or vwap or rth" -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Full-suite green modulo the 3 known pre-existing env failures; exact counts
in the handoff.

## Done criteria

- Zero `session_label`-keyed RTH/ETH decisions remain in
  `features/families/ohlcv/family.py`; shared-truth import is the only
  session-window source; absolute-truth + parity tests green; full
  validation green; truthful handoff; fresh adversarial review verdict PASS
  or PASS_WITH_WARNINGS under `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
