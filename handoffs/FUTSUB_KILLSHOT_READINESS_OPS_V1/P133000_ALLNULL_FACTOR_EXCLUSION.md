# P133000_ALLNULL_FACTOR_EXCLUSION Handoff

- Branch: `wf1/allnull-factor-exclusion`
- Phase: `P133000_ALLNULL_FACTOR_EXCLUSION`
- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Commit status: not committed by this executor. Explicit staging was attempted
  for the four curated paths, but Git could not create
  `/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-wf1-allnull-factor/index.lock`
  because the linked gitdir is read-only in this sandbox.
- Bounded repair status: W1/W2/W3 cleanup applied in this worktree and left
  uncommitted per repair instruction; no push and no PR.

## Scope Completed

- Wrote the required committed spec:
  `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P133000_ALLNULL_FACTOR_EXCLUSION-recorded-exclusion.md`.
- Changed `tools/discovery_rigor_floor/run_real_surrogate_calibration.py` so a
  declared factor partition with locked rows but zero numeric content and all
  null values becomes a value-free recorded exclusion after existing resolver,
  content-hash, and fver-filter checks pass.
- Preserved fail-closed behavior for integrity defects:
  hash mismatch, lock mismatch, fver absence, ambiguity, runtime factor mismatch,
  and non-null/non-numeric feature rows still reject rather than being excluded.
- Calibration now runs over included numeric factor sub-configs only. Declared K
  remains the per-included-sub-config run count per perturbation config.
- Added a value-free `excluded_factors` section to the Markdown report and
  `excluded_factors` / `excluded_factor_count` fields to the result payload.
- Added a value-free staging manifest under the isolated namespace so
  `--rescore-existing` uses the included sub-config count from the original
  staging pass and does not treat intentionally excluded factor namespaces as
  missing seed outputs.
- Kept the zero-content case fail-closed with structured error code
  `no_numeric_declared_factors_for_surrogate`.

## Tests Added

- Mixed fixture: one all-null factor plus one numeric factor stages and runs the
  numeric factor, records the all-null factor as `all_null_values`, and rescoring
  reproduces the same run count and exclusions.
- All-null fixture: all declared factors all-null rejects with
  `no_numeric_declared_factors_for_surrogate`.
- Repair W1: JSONL value-store hash mismatch with a healthy sibling factor
  rejects with `FeatureLockValidationError` and cannot become an
  `all_null_values` exclusion; this test is polars-free.
- Repair W2: a 3-of-6 partial-null factor stages, calibrates, and records zero
  exclusions.

## Bounded Repair Notes

- W1 fixed by adding the polars-free JSONL integrity-boundary test in
  `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`.
- W2 fixed by adding the partial-null inclusion/calibration test in the same
  module.
- W3 cleanup completed by removing the unreachable
  `no_declared_factor_sub_configs` fallback raise after
  `_raise_if_no_numeric_declared_factors`; the existing fail-closed
  `no_numeric_declared_factors_for_surrogate` behavior remains unchanged.
- Mutation A was applied locally by swallowing feature hash mismatches into an
  `all_null_values` exclusion. The new W1 test failed as expected, then the
  mutation was restored.
- Mutation B was applied locally by widening the all-null exclusion boundary to
  include 50% null rows. The new W2 test failed as expected, then the mutation
  was restored.

## Substrate Finding

`bbo_tradability_spread_ticks` all-null-everywhere is a substrate finding, not a
calibration-code finding. It belongs in the kill-shot caveat register and the
refit first-light list: the calibration can now proceed over numeric BBO factors
while recording `spread_ticks` as excluded, but the all-null substrate itself
still needs explicit caveat/refit tracking before interpreting the BBO family.

## Validation

- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py -q`
  - PASS: 12 passed in 0.59s.
- Mutation A check:
  `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py::test_real_surrogate_calibration_refuses_jsonl_hash_mismatch_with_sibling -q`
  - Expected FAIL under mutation: test did not raise
    `FeatureLockValidationError`.
- Mutation B check:
  `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py::test_real_surrogate_calibration_includes_partial_null_factor -q`
  - Expected FAIL under mutation:
    `no_numeric_declared_factors_for_surrogate`.
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m pytest tests/unit/discovery_rigor_floor tests/unit/governance -q`
  - PASS: 690 passed in 3.98s.
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed.
- `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python tools/verify.py --smoke`
  - PASS: exit 0.
- `just ci-parity`
  - PASS via `/home/yuke_zhang/.venvs/alpha_system_ci/bin/python`: 3317 passed,
    80 skipped in 83.59s.

## Explicit File Set

- Bounded repair touched:
  `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`,
  `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`,
  and this handoff.
- Original phase file set:
- `specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P133000_ALLNULL_FACTOR_EXCLUSION-recorded-exclusion.md`
- `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`
- `tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py`
- `handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P133000_ALLNULL_FACTOR_EXCLUSION.md`

## Artifact And Git Notes

- `git ls-files runs` returned empty.
- No run-local, value, SQLite, Parquet, cache, or registry artifact is staged.
- Explicit staging command attempted and failed before any staged set was
  created:
  `git add specs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P133000_ALLNULL_FACTOR_EXCLUSION-recorded-exclusion.md tools/discovery_rigor_floor/run_real_surrogate_calibration.py tests/unit/discovery_rigor_floor/test_real_surrogate_calibration_tool.py handoffs/FUTSUB_KILLSHOT_READINESS_OPS_V1/P133000_ALLNULL_FACTOR_EXCLUSION.md`
  with `fatal: Unable to create .../index.lock: Read-only file system`.
- No push and no PR, per instruction.
