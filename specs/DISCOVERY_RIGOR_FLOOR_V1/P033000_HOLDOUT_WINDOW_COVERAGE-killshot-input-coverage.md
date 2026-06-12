---
campaign_id: DISCOVERY_RIGOR_FLOOR_V1
phase_id: P033000_HOLDOUT_WINDOW_COVERAGE
lane: yellow
status: in_progress
---

# P033000_HOLDOUT_WINDOW_COVERAGE: the sealed holdout must cover the kill-shot's actual inputs

## Purpose

Compass v4.4 §3.C readiness precondition 1 (red-team VERIFIED gap): the
declared window `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json`
pins `symbols=[ES]`, `dataset_family=futures_core_alpha_pilot_v1`, frozen
`end_date=2026-06-11`. The kill-shot studies are ES/NQ/RTY consuming FUTSUB
scaleout packs; `_partitions_intersect` (sealed_holdout.py:~1265) returns
False on disjoint shared-key values, so NQ/RTY locked-test access is never
logged and never contamination-gated. This is a SCOPE-CORRECTION (widening
coverage so the guard arms on real inputs), NOT a boundary move: the
locked-test temporal boundary (2025→latest) and all P03 machinery/access-log
history are unchanged.

## Scope (in-bounds)

1. Re-declare the window (supersede the JSON in place, with a
   `superseded_declaration` field preserving the old payload + a
   `redeclaration_reason` naming this spec): symbols `[ES, NQ, RTY]`;
   dataset/partition vocabulary covering BOTH the Core Pilot family AND the
   FUTSUB scaleout partition naming as actually used in the committed
   re-locked StudySpecs (`research/futures_substrate_scaleout_v1/rerun/study_specs/*.json`
   — derive the vocabulary from those files, do not guess); end_date policy:
   open-ended (`null`/absent) or an explicit `rolling: true` marker per what
   the schema supports — "2025→latest" must mean LATEST, not a frozen date.
2. INTERSECTION CONTRACT TEST (the load-bearing deliverable): a unit test
   that loads the declared window + every committed re-locked StudySpec and
   asserts the window INTERSECTS each study's locked-test-period inputs
   (every symbol, every dataset scope) via the REAL `_partitions_intersect`
   code path — so a future mis-scoped declaration fails CI. Plus the
   negative: a study referencing a symbol/family outside the window must NOT
   intersect (proves the test isn't vacuously true).
3. If the schema cannot express multi-family or open-ended end_date, extend
   the SCHEMA minimally (sealed_holdout.py) with fail-closed semantics
   preserved — never weaken `_partitions_intersect`; widening happens in the
   DECLARATION, not the matcher.

## Hard constraints

- The locked-test temporal boundary (2025-01-01→latest) must not move
  backward; discovery/validation split dates unchanged.
- No weakening of contamination gating, access-log append semantics, or
  `require_sealed_holdout` behavior; no `src/alpha_system/runtime/**` changes.
- Explicit staging; no runs/values; no git worktree/.git config; research-only
  language.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/governance -k "holdout or sealed" -q
ALPHA_DATA_ROOT=$HOME/alpha_data/alpha_system ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor tests/unit/futures_substrate_scaleout/test_studyspec_relock_smoke.py -q
python tools/hooks/canary_runner.py
python tools/verify.py --smoke
```

## Done criteria

Window covers all kill-shot inputs (proven by the contract test against the
real matcher); negative case proves non-vacuity; old declaration preserved as
superseded payload; no matcher weakening; validation green; truthful handoff;
fresh adversarial review PASS/PASS_WITH_WARNINGS under reviews/DISCOVERY_RIGOR_FLOOR_V1/.
