---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P111500_FUTSUB_P19_COST_TEST_RECONCILE
lane: yellow
status: in_progress
---

# P111500_FUTSUB_P19_COST_TEST_RECONCILE: cost-adjusted regression reconcile

## Purpose

Reconcile the 5 LCFP cost-adjusted regression tests that FUTSUB-P19's merged
semantics change (PR #352, `bed5893`) left stale on main. P19 rewired
`src/alpha_system/labels/families/cost_adjusted/family.py` (+259 lines:
bar_end_ts terminal keying per the documented supersession, guard/BBO
semantics) under review authorization, but the LCFP regression tests pinning
the PRE-P19 semantics were not updated. They are `pytest.importorskip("polars")`
gated, so lean CI skipped them and PR #352 stayed green; any full local run
now fails 5 tests. This is the identical stale-regression pattern the
FUTSUB-P20 repair fixed for the path family (coordinator-authorized
expectation update, coverage preserved).

Failing on main (verified 2026-06-11T11:25Z, research venv):

```text
tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py — 3 FAILED
  (incl. test_cost_adjusted_matches_reference_on_misaligned_bbo_timestamps)
tests/unit/label_compute_fast_path/test_parity_matrix_suite.py — 2 FAILED
  (campaign-level parity matrix coverage + required guard/missingness cases)
```

## Scope (in-bounds)

- Update expectations/fixtures in the two failing test files to the
  POST-P19 governed semantics (bar_end_ts-aligned BBO anchor/terminal
  resolution, current guard behavior), mirroring how the P20 repair updated
  `test_path_label_pack.py`.
- Where a fixture was deliberately misaligned to prove pre-P19 exact-`event_ts`
  matching (e.g. `misaligned_bbo_timestamps`), preserve the SCENARIO and
  assert the post-P19 outcome (bar-aligned resolution semantics), so the
  coverage intent survives.
- Stale comments/docstrings describing pre-P19 matching conventions updated.

## Hard constraints

- **AMENDED 2026-06-11T11:45Z (coordinator), after the executor's correct
  BLOCKED diagnosis**: the failures are a REAL parity break, not stale tests —
  P19 moved the reference cost_adjusted family to bar_end_ts terminal keying +
  shared roll/maintenance guard, while the V1 fast cost_adjusted pack still
  keys raw `event_ts + horizon` with no guard. The coordinator AUTHORIZES
  edits to `src/alpha_system/labels/fast/**` STRICTLY to bring the fast
  cost_adjusted pack into exact parity with the post-P19 reference semantics
  (bar_end_ts-aligned BBO anchor/terminal resolution via
  `series_id + contract_id + bar_end_ts`, shared maintenance/roll terminal
  guard application), mirroring the authorized FUTSUB-P20 `fast/path.py`
  parity edit. The reference family is the truth: fast moves to match
  reference, NEVER the reverse. `src/alpha_system/labels/families/**`,
  `labels/engine.py`, `labels/roll_guard.py`, `labels/version.py` remain
  FORBIDDEN. Test-expectation updates in the two named files remain in scope
  where the post-P19 outcome legitimately differs.
- Fast-vs-reference PARITY assertions must be preserved; no assertion deleted
  or weakened; test count must not shrink.
- No values/SQLite/runs committed; explicit staging only.

## Authorization

Coordinator-authorized 2026-06-11 (this spec is the authorization record):
locked LCFP regression expectations may move to the post-P19 governed
semantics because the FUTSUB campaign contract supersedes the pre-FUTSUB
behavior these tests pinned (same basis as the FUTSUB-P20 F1 authorization;
see runs progress ledger 2026-06-11T11:10:00Z entry for precedent).

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path/test_session_maintenance_cost_pack.py tests/unit/label_compute_fast_path/test_parity_matrix_suite.py -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/label_compute_fast_path -q
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout/labels -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

## Done criteria

- All 5 previously-failing tests green (diff touches
  `src/alpha_system/labels/fast/**` per the AMENDED authorization plus
  `tests/unit/label_compute_fast_path/**`, nothing else).
- Parity assertions and scenario coverage preserved (reviewer verifies no
  assertion deletion/weakening).
- Full listed validation green; fresh adversarial review verdict PASS or
  PASS_WITH_WARNINGS under `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
