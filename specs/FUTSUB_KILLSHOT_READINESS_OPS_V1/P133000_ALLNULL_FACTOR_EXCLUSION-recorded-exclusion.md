---
campaign_id: FUTSUB_KILLSHOT_READINESS_OPS_V1
phase_id: P133000_ALLNULL_FACTOR_EXCLUSION
lane: yellow
status: in_progress
---

# P133000_ALLNULL_FACTOR_EXCLUSION: record all-null factors as exclusions

## Purpose

LIVE FINDING (2026-06-12): `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
fail-closes the entire study staging with `non_numeric_feature_pack_for_surrogate`
when any declared factor has zero numeric values. `bbo_tradability_spread_ticks`
is all-null across all inspected partitions/years (verified 2019/2021/2024:
0 non-null of about 350k rows each), so the bbo V2 calibration cannot stage.
The kill-shot study itself would not refuse this substrate shape: its diagnostics
record per-factor missingness and continue with factors that have usable numeric
content.

## Scope

1. Per-factor staging continues past all-null declared factors after existing
   resolver, content-hash, fver-filter, and ambiguity checks have passed.
2. Each all-null factor becomes a recorded value-free exclusion in the report:
   factor_id, feature version, reason `all_null_values`, and row/null counts per
   partition. No factor values, labels, returns, diagnostics, or signal values
   may be recorded.
3. Calibration proceeds over the declared factors with numeric content only.
   Declared K semantics are unchanged for included factors: K remains the run
   count per included surrogate sub-config and perturbation configuration.
4. Fail-closed behavior remains when zero declared factors have numeric content:
   nothing is available to calibrate, so the tool raises a structured validation
   error rather than emitting a vacuous zero-pass report.
5. Existing integrity checks are not weakened: content-hash verification, fver
   filtering, lock ambiguity handling, resolver lock matching, label checks, and
   runtime factor-id matching remain fail-closed.
6. `--rescore-existing` treats omitted factor namespaces consistently by using
   value-free staging metadata when it exists, so exclusions do not become
   missing-output errors.

## Tests

- Synthetic fixture with one all-null declared factor and one numeric declared
  factor: staging proceeds, the all-null factor is recorded under
  `excluded_factors`, and calibration runs over the numeric factor.
- Synthetic fixture with all declared factors all-null: fail-closed with the
  structured error code `no_numeric_declared_factors_for_surrogate`.
- Existing integrity tests for hash mismatch, fver filtering, ambiguity, and
  rescore behavior remain untouched and green.

## Validation

```bash
PYTHONPATH=$PWD/src pytest tests/unit/discovery_rigor_floor tests/unit/governance -q
PYTHONPATH=$PWD/src python tools/hooks/canary_runner.py
PYTHONPATH=$PWD/src python tools/verify.py --smoke
just ci-parity
```

## Done Criteria

- All-null factors are recorded as value-free exclusions instead of blocking
  non-empty calibrations.
- Empty-after-exclusion calibrations fail closed with the required error code.
- Report output includes an `excluded_factors` section.
- Handoff exists at
  `handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P133000_ALLNULL_FACTOR_EXCLUSION.md`
  and notes the `bbo_tradability_spread_ticks` all-null-everywhere substrate
  finding for the kill-shot caveat register and refit first-light list.
- Curated files are committed with explicit paths only. No push and no PR.
