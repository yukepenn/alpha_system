---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P183000_FUTSUB_SESSION_SEGMENT_REPAIR
lane: yellow
status: in_progress
---

# P183000_FUTSUB_SESSION_SEGMENT_REPAIR: real RTH segmentation, single session truth

## Purpose

FUTSUB-P26's review surfaced a degenerate session dimension; coordinator
triage (2026-06-11, read-only, verified on real ES 2024 packs) found the P07
session features structurally degenerate at the source:

- `src/alpha_system/features/families/session/family.py:769-770` sets
  `rth_segment_flag = 1 if _session_label(row) == "RTH" else 0`, but every
  canonical bar's `session_label` is stamped from a STATIC per-dataset config
  constant (`data/databento/canonicalize.py:449,485`;
  `configs/data/databento_es_nq_rty_instruments.json:7` = `"ETH"` for all
  instruments). No bar ever carries "RTH", so the flag is 0 for 100% of rows;
  `eth_segment_flag` is constant 1; `minutes_from_rth_open`/
  `minutes_to_rth_close` are all null; `session_id` is one whole-day ETH
  session. The fast path mirrors it (`features/fast/session_calendar_roll.py:225`).
- Latent second bug: the family's RTH clock defaults are FIXED-UTC
  (`family.py:381-382` "14:30"/"21:00" UTC) — correct only during EST; CME
  RTH is 13:30–20:00 UTC during EDT. Any fix must be tz-aware.
- Knock-on: `features/fast/vwap_session_auction.py:293` keys `_IS_RTH` off
  the same label → `base_ohlcv_opening_range` is 0-non-null of 346,858 ES
  2024 rows; RTH-conditioned semantics in vwap/overnight features never
  trigger.
- The LABELS side has its own CORRECT session truth
  (`labels/families/fixed_horizon/family.py:240-244`: ZoneInfo
  America/Chicago, RTH 08:30–15:00, maintenance 16:00–17:00,
  timestamp-derived; verified DST-aware on real packs). Two divergent
  session truths is itself a defect class.
- Parity gates CANNOT catch this: fast and reference both read the same
  degenerate input. New tests must assert ABSOLUTE timestamp-derived truth.

P27 re-locks Core Pilot StudySpecs against the substrate and P28's
vwap_session alpha specs require RTH/ETH segmentation, so this must merge
BEFORE P27 executes (run is coordinator-STOPPED at P26/P27 boundary).

## Scope (in-bounds)

1. `src/alpha_system/features/families/session/family.py`: derive RTH
   segment membership from the bar timestamp converted to the session
   template's timezone against the template windows
   (`configs/data/session_templates_and_calendar.json`:
   `session_cme_index_futures_eth`, America/Chicago, rth 08:30–15:00,
   maintenance 16:00–17:00) — tz-aware (DST handled by ZoneInfo), mirroring
   the labels implementation. Replace the fixed-UTC `rth_*_time_utc`
   parameter defaults with template-sourced local-time windows. Semantics:
   `rth_segment_flag` true inside RTH; `eth_segment_flag` the complement
   (or finer if the template defines it); `session_id` gains RTH/ETH
   segmentation; `minutes_from_rth_open`/`minutes_to_rth_close` non-null
   inside RTH. `halt_status_flag` UNCHANGED (honest metadata-absent null).
2. `src/alpha_system/features/fast/session_calendar_roll.py`: identical
   change in the fast twin (values-only producer; parity gate applies).
3. `src/alpha_system/features/fast/vwap_session_auction.py`: `_IS_RTH` keyed
   off the same timestamp-derived truth (shared helper preferred) so
   opening-range/RTH-conditioned features produce real values.
4. SINGLE SOURCE OF TRUTH: the session window constants/template parsing
   must come from one shared place importable by both feature engines —
   ideally the same template file the labels side mirrors. Do NOT modify the
   labels implementation; if a shared helper is created it must be new code
   the labels side can adopt later (record that as a follow-up, do not do it).
5. Tests (absolute truth, not parity):
   - DST boundary: one EST date and one EDT date — RTH window lands at the
     correct UTC hours for both (e.g. 2024-01-10 vs 2024-07-10).
   - Segment edges: bar exactly at 08:30, 14:59, 15:00 America/Chicago.
   - minutes_from/to fields non-null and correct inside RTH, null outside.
   - vwap opening-range produces non-null values on a synthetic RTH day.
   - Parity: fast == reference on the same fixtures (existing gate pattern).
6. Stale-expectation authorization (same basis as FUTSUB-P20/P111500
   precedents): existing tests that PIN the degenerate behavior (rth always
   0, eth always 1, opening_range empty, session_id whole-day) MAY be
   updated to the repaired semantics with provenance notes. No assertion may
   be deleted or weakened; scenario coverage must survive.

## Hard constraints

- FORBIDDEN: `src/alpha_system/labels/**` (the correct truth, untouched),
  `data/databento/canonicalize.py` and dataset configs (canonical
  `session_label` is a coverage descriptor; do NOT re-canonicalize),
  registry write-paths/schema, `runtime/**` except if a shared session
  helper module needs a neutral home (prefer `features/` or a small
  `core/sessions.py`).
- Producer fast-path code stays values-only and reference-parity-gated.
- No values/SQLite/runs committed; explicit staging only.
- Re-materialization is a LOCAL validation step (next section), not a
  committed artifact.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/features -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit -k "session or vwap or rth" -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit tests/no_lookahead tests/integration -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Full-suite must be green modulo the 3 known pre-existing env failures
(databento_canonicalize, duckdb_query_fixture, polars_lazy_fixture — proven
failing at base). Record exact counts in the handoff (P151500 lesson:
spec-scoped validation is not enough for src-touching repairs).

Post-merge (coordinator, not this phase): re-materialize
`session_calendar_maintenance` + `vwap_session_auction` packs locally,
deprecate superseded FeatureVersions via the sanctioned API with replacement
pointers + registry backup, then clear STOP and resume FUTSUB (P26 finishes
from recorded stage; P27 re-lock absorbs the new FeatureVersions and the
lifecycle-enforced resolver fails closed on the stale ones).

## Done criteria

- rth/eth/minutes/session_id derived tz-aware from the single template truth
  in both engines; vwap RTH conditioning real; DST boundary tests prove EST
  and EDT windows; full validation green; truthful handoff with exact
  commands/counts; fresh adversarial review verdict PASS or
  PASS_WITH_WARNINGS under `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
