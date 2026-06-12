# Adversarial Review: P080820_SURROGATE_DETECTION_STATISTIC

- Campaign: `FUTSUB_KILLSHOT_READINESS_OPS_V1`
- Phase: `P080820_SURROGATE_DETECTION_STATISTIC` (Yellow)
- Branch: `wf1/surrogate-detection-statistic` @ `741de9e`
- Reviewer: fresh adversarial Claude review (independent of executor)
- Date: 2026-06-12
- Verdict: **PASS_WITH_WARNINGS**

## Scope Reviewed

`git diff origin/main` (11 files, +929/-103): new
`src/alpha_system/governance/detection_statistic.py`, refactored
`src/alpha_system/governance/canaries/true_alpha_detection.py`, new pass
semantics in `src/alpha_system/governance/surrogate_run.py`, `--rescore-existing`
in `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`, test updates,
diagnosis note, spec, handoff. Stance: adversarial — assumed weakened tests,
fabricated statistics, or semantic drift until disproven.

## Must-Check Results

### 1. One IC truth — VERIFIED

`detection_statistic.py` is a genuine move, not a fork: the canary's private
`_pearson_ic` (incl. the `{"ic": ...}` writer-shape unwrap and finiteness
check) was deleted from `true_alpha_detection.py` and the canary now calls
`evaluate_detection_statistic` for `measured`, `detected`,
`detection_outcome`, and `diagnostic_name`. The surrogate runner
(`run_surrogate_study`), the calibration aggregator, and the rescore path all
call the same function. Comparison is `measured >= threshold` in one place
only (mutation A proves both legs consume it; see below).

Threshold source nuance: the canary's threshold remains fixture-declared
(`evals/canaries/true_alpha_detection/{strong,weak}_fixture.json`, 0.95,
unchanged in this diff) while the surrogate uses the new module constant
`TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC = 0.95`. Drift between the two
declarations is pinned by the new assertion in
`test_detection_fixtures_declare_threshold_pair` (fixture value == constant),
so divergence fails CI. Recorded as W2 below; not a blocking divergence.

### 2. Canary behavior preserved — VERIFIED

- Threshold VALUE unchanged: fixtures still declare 0.95; no fixture file in
  the diff; comparison stayed `>=`.
- `DetectionStatisticError` subclasses `ValueError`, the exact type the old
  canary helper raised — no behavioral widening.
- Reproduced: `canary_runner.py` → 25/25 PASS including
  `true_alpha_detection_detect_strong` (DETECTED),
  `true_alpha_detection_no_detect_weak` (NOT_DETECTED), `planted_fake_alpha`
  (clean-twin path) all green; P040500 test module 6/6 PASS.

### 3. Statistic honesty — VERIFIED

`statistic_passed` comes from the run's real measured diagnostic output:
fresh path evaluates `study_result.summary` (the same `DiagnosticSummary`
persisted by `write_study_outputs` to
`<namespace>/seed_<seed>/study_outputs/diagnostic_summary.json`); rescore path
reads `diagnostics.directional.pearson_ic` from that persisted file (plain
number or `{"ic": n}` writer shape). No default, no fabricated value: a
missing/None/NaN/bool/absent-directional statistic raises
`DetectionStatisticError` and every such exception routes to an ERROR row
(`ValueError` is in both catch lists; `GovernanceSerializationError` and
`GovernanceValidationError` also subclass `ValueError`, so corrupt
`surrogate_runs/*.json` records also fail closed per-seed). Reviewer
empirically exercised four uncomputable variants through
`_rescore_existing_seed` (null IC, NaN IC, missing `directional`, bool IC) —
all returned `gate_status=ERROR`, `error_type=DetectionStatisticError`.
Test-coverage gap for these file-present variants recorded as W1.

### 4. Field independence — VERIFIED

- `test_surrogate_pass_uses_statistic_not_clean_diagnostics`: both runs
  `eligibility_clean=True`; seed 200 → `statistic_passed=True`/PASSED, seed 20
  → `statistic_passed=False`/BLOCKED.
- `test_calibration_verdict_follows_statistic_not_eligibility`:
  `statistic_passed=True` with `eligibility_clean=False` (min_total=10 forces
  warnings) → `LEAKAGE_BLOCKED` with `eligibility_clean_count=0`.
- Both fields vary independently in both directions; `threshold_verdict`
  follows `statistic_pass_count` only (eligibility appears nowhere in verdict
  logic — confirmed in `surrogate_calibration_report_from_rows` and the
  per-perturbation bucket code).

### 5. Rescore parity and fail-closed seeds — VERIFIED

- Seed grid identical to fresh mode: fresh per-config base seed is
  `base + config_index * K` with `seed = base + run_index` inside
  `calibrate_surrogate_fdr` (single spec); rescore computes
  `base + config_index * K + run_index`. Directory layout matches
  (`namespace/seed_<seed>/study_outputs/`).
- Structural no-skip guarantee: rescore iterates the full declared
  `configs x K` grid and appends exactly one row per cell — a missing seed
  becomes an ERROR row, never an omission; `run_count` always equals the
  declared grid size.
- `test_real_surrogate_calibration_rescores_existing_seed_outputs` compares
  the full result payload (accepted, run/error/pass/eligibility counts,
  verdict, surrogate_study_spec_id) between fresh and rescored runs;
  `test_real_surrogate_rescore_marks_missing_diagnostic_summary_error` deletes
  one summary and asserts `error_count == 1` + `CALIBRATION_BLOCKED`.
- Optional `surrogate_runs/*.json` consistency checks (seed match,
  perturbation match, exactly-one record) raise → per-seed ERROR.

### 6. Mutation tests — ALL KILLED

Run command: `PYTHONPATH=$PWD/src ~/.venvs/alpha_system_research/bin/python -m
pytest tests/unit/governance/test_surrogate_run.py
tests/unit/discovery_rigor_floor -q`; exact restore verified after each
(`git status --short` clean, diff stat unchanged at 11 files +929/-103).

| Mutation | Result |
|---|---|
| A. `detected = measured >= threshold` → `<` in `detection_statistic.py` | **KILLED** — 16 failed, including BOTH canary tests (`test_strong_true_signal_fixture_is_detected_through_gated_path`, `test_weak_true_signal_fixture_is_not_detected_below_declared_floor`) AND surrogate tests (`test_surrogate_pass_uses_statistic_not_clean_diagnostics`, `test_calibration_verdict_follows_statistic_not_eligibility`, ...) — proves both legs consume the one shared helper. |
| B. `statistic_passed = detection_statistic.detected` → `False` in `surrogate_run.py` | **KILLED** — 4 failed (`test_surrogate_pass_uses_statistic_not_clean_diagnostics`, `test_calibration_reports_leakage_blocked_when_any_shuffled_run_passes`, `test_calibration_verdict_follows_statistic_not_eligibility`, P05 `test_zero_pass_threshold_canary_blocks_any_shuffled_pass`) — zero-pass is not vacuous. |
| C. rescore drops ERROR rows instead of appending (silent missing-seed skip) | **KILLED** — `test_real_surrogate_rescore_marks_missing_diagnostic_summary_error` failed (error_count 0 != 1). |

### 7. P05 regression honesty — VERIFIED

No special-case branch anywhere in the diff. The P05 canary test
`test_zero_pass_threshold_canary_blocks_any_shuffled_pass` changed
`base_seed` 20→200 because under signal-aligned semantics seed 20's shuffled
synthetic run no longer "passes" (clean diagnostics no longer suffice); seed
200's run clears |IC| ≥ 0.95 and the test still asserts a shuffled pass →
`LEAKAGE_BLOCKED`. Purpose preserved, fixture updated truthfully. The
synthetic zero-pass CI canary and error-masking canary gained
`statistic_pass_count` assertions without weakening existing ones. No test
deletions; the only removed assertion text ("Gate pass rate") was replaced by
the renamed "Statistic pass rate" count-of-one assertion.

### 8. Scope, artifact policy, handoff truthfulness — VERIFIED

- Diff touches only the spec/handoff/diagnosis docs, the two governance
  modules, the new shared helper, the tool, and four test files. No
  `src/alpha_system/{features,labels,runtime}/**` edits, no perturbation
  writer changes (`write_label_shuffled_copy` / block writers untouched), no
  fixture/threshold value changes.
- `git ls-files runs` empty; `git diff --check` clean; no forbidden binary
  artifacts tracked; worktree clean post-review.
- Handoff validation table reproduced exactly: governance 640 passed; rigor
  floor 37 passed; canaries 25 PASS; `verify.py --smoke` exit 0;
  `just ci-parity` 3304 passed / 75 skipped. All claims truthful.
- Diagnosis note is value-free (counts/ids/file:line only, no measured
  values), cites the spec and the aligned canary threshold as required.

## Findings

### W1 (warning, minor): no direct test for file-present-but-uncomputable statistic

The only tested uncomputable path is a deleted `diagnostic_summary.json`
(rescore) and a missing labels file (fresh). The handoff documents that a
null/non-finite/absent `directional.pearson_ic` in a present summary is also
ERROR; the reviewer verified all four variants empirically (all →
`ERROR`/`DetectionStatisticError`), but no committed test pins this. Suggest a
small fixture test on `_rescore_existing_seed` or `evaluate_detection_statistic`
in a follow-up. Non-blocking: behavior is fail-closed by construction
(exception subclassing verified) and reviewer-exercised.

### W2 (warning, cosmetic): threshold declared twice

The detection threshold now exists as fixture JSON (canary source) and as
`TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC` (surrogate source). The new
pin assertion in `test_detection_fixtures_declare_threshold_pair` makes drift
a CI failure, which is adequate; noting so a future fixture edit is understood
to require the constant to move with it (single-truth would be the constant
feeding the fixture loader, but that is out of this phase's scope).

### N1 (note): `reason_code = UNDERPOWERED` for statistic non-pass

A null run that simply fails to clear the detection statistic (the expected
outcome) reuses the pre-existing `UNDERPOWERED` reason code. Pre-existing enum
reuse, value-free reporting unaffected; semantically imprecise but harmless.

### N2 (note): gate_outcome records threshold + diagnostic name, not measured IC

Consistent with the value-free artifact policy (counts/ids only); the measured
statistic stays in local-only study outputs. Intentional, correct.

## Validation Reproduced (this reviewer, this worktree)

```text
PYTHONPATH=$PWD/src pytest tests/unit/governance -q              -> 640 passed
PYTHONPATH=$PWD/src pytest tests/unit/discovery_rigor_floor -q   -> 37 passed
PYTHONPATH=$PWD/src python tools/hooks/canary_runner.py          -> 25 PASS, "All Frontier canaries passed."
PYTHONPATH=$PWD/src python tools/verify.py --smoke               -> exit 0
PYTHONPATH=$PWD/src PATH=ci-venv just ci-parity                  -> 3304 passed, 75 skipped
```

## Verdict

**PASS_WITH_WARNINGS** — one shared IC truth proven by mutation; canary
outcomes preserved with unchanged threshold; surrogate pass now measures the
detection statistic with eligibility retained as context only; rescore is
grid-complete and fail-closed; P05 updated honestly; handoff truthful.
Warnings W1/W2 are non-blocking follow-ups.
