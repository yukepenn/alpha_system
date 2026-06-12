---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P110000_RELOCK_V2
lane: yellow
status: in_progress
---

# P110000_RELOCK_V2: re-lock the kill-shot StudySpecs against the repaired registry

## Purpose

The damaged-pack repair (deprecate-first 168 fvers + full-grid
re-materialization of session_calendar_maintenance, regime_volatility_compression,
bbo_tradability_top_book — runbook
`research/futures_substrate_scaleout_v1/repair/PACK_RESTORE_RUNBOOK.md`)
changes locked feature content (and for bbo, event_ts semantics per the
merged #401 grid fix). The 10 committed re-locked StudySpecs under
`research/futures_substrate_scaleout_v1/rerun/study_specs/` lock superseded
fvers/content hashes. Re-issue locks against the repaired registry and update
every committed artifact/test that pins the old sspec ids — keeping the
kill-shot evidence chain consistent and fail-closed.

## Preconditions (verify, fail-closed)

- Re-mat chain complete: `~/logs/alpha_pipeline/remat_chain.log` shows rc=0
  for all three families and the post-re-mat `pack_restore_audit` reports
  ZERO stale-registry paths for them (read the audit output; if any stale
  remain, STOP and report — do not lock against a dirty registry).
- Track-A metrics marker still absent:
  `runs/2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/phases/FUTSUB-P28/track_a_metrics_started.json`.

## Scope (in-bounds)

1. **Re-lock**: reuse the EXACT bounded-relock path that produced the
   current bundle (provenance `P022000_FUTSUB_RELOCK_RERUN` in the sspecs —
   find its driver/CLI under tools/ or the spec
   specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/P022000_*.md; reuse,
   never reimplement) over all 10 source sspecs against the live repaired
   registry. Expect NEW sspec ids (content-addressed over locks). The new
   bundle replaces `research/futures_substrate_scaleout_v1/rerun/study_specs/*.json`
   with the same naming convention; `studyspec_relock.md` gains a v2 section
   mapping old→new ids with the repair rationale (value-free: ids, counts,
   hashes).
2. **Lock validation**: run the existing feature-lock validator + the relock
   smoke test against the new bundle (every lock resolves to a REGISTERED
   record whose pack file contains the fver — the staging-integrity hash
   check from #400 and the pack-audit must both be green on the locked set).
   The bbo sspec's locks must resolve to post-grid-fix packs (spot-assert a
   bbo lock's first_event_ts is minute-grid).
3. **Reference updates** (every committed pin of the old ids):
   - tests/unit/discovery_rigor_floor/test_pooled_track_b_readiness.py
     RERUN_STUDY_IDS + tests/unit/governance/test_pooled_hypothesis.py
   - research/discovery_rigor_floor_v1/track_b/*_TEMPLATE.json candidate ids
   - research/discovery_rigor_floor_v1/power_memos/KILL_SHOT_POWER_MEMOS.md
     (id-mapping note section, memos themselves unchanged — they are
     pre-registered; add an explicit "applies to relocked successor <new id>"
     line per study, never rewrite the memo content)
   - research/discovery_rigor_floor_v1/variant_reconciliation/ +
     substrate_invariant/ audits: add a v2 addendum section noting the
     relock (ids old→new), NOT a rewrite of the original audit
   - sealed-holdout: run the intersection contract test against the new
     bundle (it loads committed sspecs — must pass; if the declaration needs
     vocabulary it lacks, STOP and report).
   - grep the repo for each old sspec id to catch any other committed pins;
     update or addendum as appropriate (run-local runs/** files are
     out of scope).
4. **Track-B note**: do NOT register pooled hypotheses (coordinator-owned,
   ordering-sensitive); instead update the DRAFT templates' member refs to
   the new anchor ids and state in the handoff that coordinator
   re-registration must precede any Track-A metric.

## Hard constraints

- Locks issued only via the sanctioned relock path; no manual JSON editing
  of lock payloads; no registry writes; no src/alpha_system/** changes.
- Pre-registered artifacts (power memos, original audits) are append-only —
  addenda, never rewrites.
- Explicit staging; no values/SQLite/runs committed; research-only language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor tests/unit/governance -q
ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
just ci-parity
```

## Done criteria

New 10-sspec bundle locked+validated against the repaired registry (bbo on
post-grid-fix content); old→new id map committed; every committed pin
updated or addended; intersection contract test green; validation green
incl. ci-parity; truthful handoff; fresh adversarial review
PASS/PASS_WITH_WARNINGS under reviews/FUTSUB_KILLSHOT_READINESS_OPS_V1/.
