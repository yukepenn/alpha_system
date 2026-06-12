---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P085901_BBO_EVENT_TS_GRID
lane: yellow
status: in_progress
---

# P085901_BBO_EVENT_TS_GRID: bar-grid event_ts for bbo features + written grid contract + canary

## Purpose

LIVE FINDING (2026-06-12): bbo_tradability feature packs stamp `event_ts`
with the sampled quote's sub-second timestamp (canonical layer passes raw
`ts_event` through `canonicalize.py:990/:1013`; the family copies it at
`src/alpha_system/features/families/bbo/family.py:638` and
`src/alpha_system/features/fast/bbo_tradability.py:106/:317`), while every
other family inherits OHLCV `bar_end` grid (`canonicalize.py:646`). The
production diagnostics join requires EXACT event_ts equality
(`src/alpha_system/research/diagnostics.py:205-212`) → a bbo factor row NEVER
joins a minute-grid label (verified: 349,532/349,532 missing-label on real
2019 ES). The kill-shot bbo rerun (sspec_6088f0) would be INCONCLUSIVE (n=0).
No written contract pins factor event_ts to the bar grid — this phase fixes
the family, writes the contract, and adds a registry canary. PIT note:
re-stamping to `bar_end_ts` claims the observation LATER than it occurred
(quote at :59.8 stamped :00) — conservative, no lookahead; `available_ts`
(already bar_end+latency, `canonicalize.py:1014`) is untouched.

## Scope (in-bounds)

1. **Family fix (reference + fast, parity-gated)**: bbo feature family emits
   `event_ts = bar_end_ts` (the bar-grid timestamp the row's `available_ts`
   already derives from): `families/bbo/family.py:638` (+ spread_zscore
   primitive points `:701/:711`) and `fast/bbo_tradability.py` (`:106`
   event_ts_expr, `:317` cast). Keep all other fields (incl. available_ts,
   quality_flags) unchanged. Fast/reference parity must hold (existing
   reconciliation tests + the DST parity fixture must stay green; update
   bbo-family test fixtures' expected event_ts honestly).
2. **Written contract**: docs/FACTOR_COMPUTE.md (and/or the family base-class
   docstring) gains an explicit normative statement: emitted FeatureValue
   `event_ts` MUST lie on the bar grid (bar_end_ts) for bar-indexed
   families; the canonical layer's quote-time event_ts is an INPUT property
   that families must normalize on emission. State the PIT rationale.
3. **Registry grid canary** (governance/canaries idiom, COMPOSE with
   canary_runner): a canary that scans REGISTERED feature AND label
   registrations' first/last_event_ts for off-grid (non-:00-second)
   timestamps and FAILS naming the family/pack. It must (a) FAIL today on
   the current bbo registrations (and the 469 cost/spread-adjusted label
   registrations) when run against the live registry — so register it with
   an explicit allowlist/grandfather mechanism that lists the KNOWN-off-grid
   packs with reason codes (bbo: pending re-materialization;
   cost/spread labels: documented mirror defect) so canaries stay green in
   CI while the debt is visible and shrinking; removing an allowlist entry
   after repair must be a one-line change. CI runs use synthetic fixtures
   (no local registry in CI — loud condition-driven skip idiom for the
   live-registry mode).
4. **Identity note**: changing emitted event_ts changes pack CONTENT (values
   parquet) but feature_version_id identity derives from spec/config — state
   in the handoff whether fvids rotate (consult the identity-pins test
   P036000) and why re-materialization + re-lock is the sanctioned path for
   consumers (no in-place mutation of registered packs).
5. **Do NOT re-materialize in this phase** (coordinator runs the sanctioned
   scaleout CLI afterward); do NOT touch diagnostics join semantics, label
   families, or canonical-layer event_ts (the canonical quote record
   legitimately preserves quote time; normalization is the FAMILY's job).

## Hard constraints

- features/** edits limited to the bbo family (reference + fast) emission
  timestamps + their tests/fixtures; no other family, no engine changes.
- Fast/reference parity gate intact; no test weakening (fixture updates must
  preserve assertion strength).
- Explicit staging; no values/SQLite/runs committed; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features tests/unit/feature_compute_fast_path tests/unit/futures_substrate_scaleout -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

bbo family emits bar-grid event_ts on both paths with parity green; contract
written; grid canary registered (live mode fails on known debt via visible
allowlist, CI green on fixtures); identity implications stated; validation
green incl. ci-parity; truthful handoff; fresh adversarial review
PASS/PASS_WITH_WARNINGS under reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/.
