---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P036000_IDENTITY_PINS_DST_FIXTURE
lane: yellow
status: in_progress
---

# P036000_IDENTITY_PINS_DST_FIXTURE: pinned-fvid identity regression + summer-DST parity fixture

## Purpose

Close P235500 review warnings W2/W3 (compass v4.4 readiness hygiene): (a) no
pinned-hash fvid regression test exists — the in-repo identity guard checks
template-change invariance only and would not catch accidental identity
rotation from an innocent-looking refactor (the exact class W1 found); (b) no
summer (EDT) boundary fixture exercises the fast-path session derivation —
DST correctness is asserted for the reference truth but the polars twins'
parity fixtures run on a single regime.

## Scope (in-bounds)

1. PINNED-FVID REGRESSION TEST (tests/unit/features/): for a representative
   set of CURRENT production specs — at least one session-conditioned per
   family (liquidity_structure_range_contraction, bbo_tradability_spread_zscore,
   base_ohlcv_atr, cross_market_synchronized_returns, base_ohlcv_opening_range)
   and at least two UNconditioned (base_ohlcv_returns, base_ohlcv_volume_zscore)
   — build the FeatureSpec exactly as the production family code does and
   assert the derived feature_version_id equals a HARDCODED hex pin (capture
   the current values at implementation time). A comment block must explain:
   pins break LOUDLY on any identity-affecting change; an intentional
   rotation updates the pins IN THE SAME reviewed commit that justifies it.
2. SUMMER-DST PARITY FIXTURE (tests/unit/feature_compute_fast_path/ +
   fixtures): a synthetic frame spanning an EDT trading day (RTH open
   13:30Z) AND the March DST transition week, with static canonical labels +
   real timestamps (fixture honesty — the fixture must NOT compute session
   labels from timestamps itself). Assert fast-vs-reference parity for at
   least one repointed feature per family (structure, bbo, regime/ohlcv,
   volume, cross_market) across the boundary, and assert the session
   classification flips at 13:30Z (EDT) vs 14:30Z (EST) on the
   straddling days.
3. Do NOT touch production code: if a parity mismatch is FOUND, stop and
   report it in the handoff as a finding (it would be a real bug, not a test
   problem).

## Hard constraints

- Tests + fixtures only; zero src/alpha_system/** changes.
- Fixture honesty per compass §4; no values/SQLite/runs committed; explicit
  staging; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features tests/unit/feature_compute_fast_path -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
```

## Done criteria

Pins assert current production identities for conditioned AND unconditioned
specs; DST fixture proves parity + correct boundary flip in both regimes;
zero production edits (or an honestly-reported finding); validation green;
truthful handoff; fresh adversarial review PASS/PASS_WITH_WARNINGS under
reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/.
