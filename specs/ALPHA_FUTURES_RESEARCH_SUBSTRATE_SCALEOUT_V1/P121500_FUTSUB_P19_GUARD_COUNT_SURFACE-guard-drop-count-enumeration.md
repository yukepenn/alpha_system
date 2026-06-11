---
campaign_id: ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1
phase_id: P121500_FUTSUB_P19_GUARD_COUNT_SURFACE
lane: yellow
status: in_progress
---

# P121500_FUTSUB_P19_GUARD_COUNT_SURFACE: cost-adjusted dropped guard-window counts

## Purpose

FUTSUB-P21's guard audit BLOCKED partly because dropped roll-window and
maintenance-window counts for the P19 cost_adjusted pack are unrecoverable
from committed evidence (drops are not emitted as label rows;
"Guard-flagged emitted rows | 0" is the only committed figure). Surface
deterministic, value-free dropped-window counts so the P21 re-run can replace
all 24 `COUNT_GAP` cells with real counts.

## Scope (in-bounds)

- A read-only enumeration tool under `tools/futures_substrate_scaleout/`
  (new dir ok) that recomputes guard decisions for the cost_adjusted unit
  grid (symbol x year x horizon over the accepted window) by driving the
  EXISTING guard primitive (`labels/roll_guard.evaluate_roll_guard` + the
  maintenance-crossing logic the reference family uses) over canonical bar
  timelines — counting, per cell: dropped-by-roll-window, dropped-by-
  maintenance-crossing, truncated/flagged if applicable. NO value writes, NO
  registry writes, NO label emission — counts only.
- Write the value-free counts table to
  `research/futures_substrate_scaleout_v1/label_packs/cost_adjusted/guard_drop_counts.md`
  (per symbol x year x horizon + per-family totals + provenance: roll
  calendar id, guard version, policy).
- A synthetic unit test proving the enumerator's classification matches the
  reference family's guard behavior on a crafted fixture (crossing kept =
  violation; the four policies exercised), mirroring the P21 test pattern.

## Hard constraints

- READ-ONLY with respect to values/registries: the tool must not open any
  registry for writing and must not write Parquet/SQLite anywhere.
- No edits to `src/alpha_system/labels/**` or any `src/**` production module;
  the tool lives in `tools/` and imports existing primitives read-only.
- Counts must be derived from the same calendar/guard provenance P19 used
  (record ids in the output); any mismatch is reported, not papered over.
- No values/SQLite/runs committed; explicit staging only.

## Validation

```bash
~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/futures_substrate_scaleout -q
python tools/verify.py --smoke
python tools/hooks/canary_runner.py
```

Plus one real execution of the tool (coordinator or executor) producing the
committed counts table; record the exact command + elapsed in the handoff.

## Done criteria

- `guard_drop_counts.md` committed, value-free, per-cell counts with
  provenance; tool + test committed; all validation green; fresh adversarial
  review verdict PASS or PASS_WITH_WARNINGS under
  `reviews/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/`.
