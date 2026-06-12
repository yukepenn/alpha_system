# Review: P040500_TRUE_ALPHA_DETECTION_CANARY

- Campaign: DISCOVERY_RIGOR_FLOOR_V1
- Phase: P040500_TRUE_ALPHA_DETECTION_CANARY
- Lane: yellow
- Reviewer: fresh adversarial Claude review (WF1)
- Reviewed at: 2026-06-12
- Worktree: `/home/yuke_zhang/projects/alpha_system-wf1-session-reset` (branch `feat/true-alpha-detection-canary`, base `80008c5`, diff UNCOMMITTED)
- Verdict: **PASS_WITH_WARNINGS**

## Scope of review

Danger class checked: a detection canary that "detects" via fixture leakage or
artifact rather than the planted relationship, or a tautological threshold.
All checks run live in the worktree with
`~/.venvs/alpha_system_research/bin/python`. Mutation tests were performed on
the real fixture files with sha256-verified byte-identical restore.

## 1. Fixture honesty — PASS

- Fixtures are static deterministic JSON (no RNG anywhere in the path):
  `evals/canaries/true_alpha_detection/{strong,weak}_fixture.json`. Labels are
  constructed as `label = coefficient * feature_t + noise_t` in
  `_factor_and_label_rows` from fixture-declared `feature_values`,
  `label_noise_values`, `label_signal_coefficient` — the relationship lives in
  fixture data, exactly the `labels = f(feature)+noise` construction the spec
  authorizes.
- Point-in-time clean: factor `available_ts = event_ts + 5s`;
  `label_available_ts = horizon_end + 5s = event_ts + 65s` > factor
  availability. No contamination tokens; `quality_flags = ["synthetic",
  "point_in_time_clean"]`. No gate trips: both fixtures reach
  `DIAGNOSTICS_RUN->EVIDENCE_READY`, `diagnostics_status=PASS`.
- Artifact check (signal removed): running the strong fixture through the live
  pipeline with `label_signal_coefficient = 0.0` yields
  `detected=False, measured |IC| = 0.296517` (equals corr(feature, noise) =
  -0.2965 computed independently). Detection collapses without the planted
  signal — it is measuring the planted relationship, not shared index
  ordering or offsets.
- Independent math check: computed Pearson r from raw fixture arrays matches
  the pipeline's measured values EXACTLY — strong 0.968325, weak 0.593103.
  Computed SNR (coef * sd_feature / sd_noise): strong 4.0002, weak 1.0000.

## 2. Non-tautology — PASS

- Strong and weak fixtures are byte-comparable: identical `feature_values`,
  identical `label_noise_values`, identical
  `detection_threshold_abs_pearson_ic = 0.95`, identical declared floor 3.0.
  The ONLY data difference is `label_signal_coefficient` (1.0 vs 0.25), i.e.
  the SNR.
- Both run through the identical code path
  `_run_true_alpha_detection_canary` -> `compute_diagnostic_summary` ->
  `validate_evidence_ready_gate` -> `validate_variant_and_family_budget` ->
  `validate_governance_transition(require_sealed_holdout=True)`; no per-strength
  branching anywhere.
- `tests/.../test_detection_fixtures_declare_threshold_pair` pins
  threshold/floor equality across the two fixtures, so a future drift into a
  per-fixture threshold tautology breaks the test.
- Weak NOT detected: 0.593103 < 0.95 through the same path. Confirmed live.

## 3. Pipeline truth — PASS

- The diagnostic is computed by the real research diagnostics engine
  `alpha_system.research.diagnostics.compute_diagnostic_summary` — the same
  function used by `src/alpha_system/cli/study.py` (real study runs) and
  `governance/surrogate_run.py`. Not a canary-private statistic.
- Gate stack mirrors the P04 `planted_fake_alpha.py` driver one-for-one
  (evidence-ready gate, variant/family budget, sealed-holdout-required
  promotion transition). The detection canary additionally runs real
  diagnostics, which P04 (metadata-only) does not — a superset, not a bypass.
- Diff check: changes touch only `src/alpha_system/governance/canaries/**`,
  `tools/hooks/canary_runner.py`, `evals/canaries/**`, `tests/**`,
  `research/**`, `docs/SYSTEM_MAP.md`. **No
  `src/alpha_system/{features,labels,runtime}/**` changes.** No pipeline
  special-casing for the canary.

## 4. Canary registration — PASS

- `tools/hooks/canary_runner.py` registers
  `true_alpha_detection_detect_strong` and
  `true_alpha_detection_no_detect_weak` following the existing
  `planted_fake_alpha` idiom (`expect_block=False`; snippet exits nonzero on
  wrong polarity, expectation mismatch, or any exception).
- Both polarities asserted: exit is
  `0 if result.detected is <expected> and result.expectation_met else 1`, so
  strong-stops-detecting => FAIL and weak-starts-detecting => FAIL. Verified
  live by mutation (below), not just by reading.

## 5. Mutation tests (sha256 byte-identical restore verified) — PASS

Pre-mutation sha256:

```text
1ac7bda12d10ab6a16a9b1147de783c2359f3185f5d672a8a4aa14520ea275b0  strong_fixture.json
4775199fe35fa72d6d0303ccd5efb32be8153f1a8d8b849ffdbf1f8d2abd3d9c  weak_fixture.json
9f320bace9926451936e8acb4a618100cf970114eb7082cb690933d1c6324ef2  planted_fake_alpha_clean_twin/synthetic_fixture.json
```

- (a) Strong degraded (coefficient 1.0 -> 0.25):
  `true_alpha_detection_detect_strong` **FAILED** (`strong NOT_DETECTED
  0.593103 0.950000`, passed=False). Restored; `sha256sum -c` OK.
- (b) Weak planted (coefficient 0.25 -> 1.0):
  `true_alpha_detection_no_detect_weak` **FAILED** (`weak DETECTED 0.968325
  0.950000`, passed=False). Restored; `sha256sum -c` OK.
- (c) Clean twin re-contaminated (P04 pattern: `lookahead_k=1`,
  `source_bar_id` = next bar): phase test suite **FAILED 2** —
  `test_planted_fake_alpha_clean_twin_passes_gate_stack` and
  `test_clean_twin_matches_p04_shape_without_contamination`. Restored;
  `sha256sum -c` OK.
- Post-restore green re-confirmed: phase tests 6 passed; both detection
  canaries + `planted_fake_alpha` PASS with original measured values.

## 6. Threshold sanity — PASS (deterministic)

- Margin 0.968325 vs 0.95 (0.018) looks thin, but the fixture is fully static
  JSON with zero runtime randomness: measured IC is bit-reproducible (matched
  my independent computation to 6 decimals). No seed => no seed flakiness.
- The threshold is coherent with the declared floor: SNR 3.0 maps to
  r = 3/sqrt(10) ≈ 0.9487, just below 0.95; SNR ≈ 4.0 maps to ≈ 0.970. The
  0.95 threshold genuinely separates floor from declared-strong. The only
  thing that can move the measured value is a change in the IC implementation
  itself — which is precisely the regression this canary exists to catch.

## 7. Validation counts (run by reviewer)

- `pytest tests/unit/governance tests/unit/discovery_rigor_floor -q`:
  **661 passed in 3.30s** (matches executor claim).
- `tools/hooks/canary_runner.py`: **25 PASS**, "All Frontier canaries passed."
  (was 23; +`true_alpha_detection_detect_strong`,
  +`true_alpha_detection_no_detect_weak`). New total 25 > 23 as required.
- `tools/verify.py --smoke`: exit **0**.
- Executor-disclosed `verify.py --all` 3 failures (duckdb/polars/databento
  integration) touch files NOT in this diff; pre-existing/env, outside phase
  scope; smoke is the spec-required check.

## 8. Hygiene — PASS

- READMEs and the research note use research-only language: "synthetic canary
  metadata only", "not market evidence", explicit no-alpha/profitability/
  tradability/production disclaimers; declared strengths and measured
  threshold documented in
  `research/discovery_rigor_floor_v1/canary_floor/P040500_TRUE_ALPHA_DETECTION_CANARY.md`.
- `git diff --cached --name-only`: empty (nothing staged).
- `git ls-files runs`: empty.

## Warnings (non-blocking)

1. **Declared SNR 4.01 is slightly inaccurate.** Computed from the fixture
   arrays, coef * sd(feature)/sd(noise) = 4.0002 (population and sample sd
   give the same ratio). The fixture JSON, README table, and research note all
   say 4.01. Detection logic is unaffected (threshold acts on measured IC),
   but in a phase whose purpose is honest declared strengths, the declared
   value should be 4.00 (or the derivation shown). Recommend a one-line fix.
2. **Clean-twin contamination flag is hardcoded, not gate-mediated.**
   `_clean_twin_trial_record` sets `locked_test_contamination_flag=False`
   unconditionally; cleanliness is enforced by the canary's own precondition
   (`_fixture_has_lookahead_contamination` -> ValueError) rather than by
   passing the computed flag to the real gate as P04 does. Mutation (c) proves
   the assertion still fails loudly (cannot silently pass a contaminated
   twin), so the safety property holds, but the failure mode is a precondition
   exception, not a gate block. A more faithful mirror would compute the flag
   from the fixture and let the gate decide.
3. **Clean twin is asserted in pytest only**, not registered as a
   canary_runner scenario. Spec item 4 required runner registration only for
   the detect/no-detect pair, and item 3's "assert" is satisfied by
   `test_planted_fake_alpha_clean_twin_passes_gate_stack`; noted for
   completeness.

## Verdict

**PASS_WITH_WARNINGS.** Every claimed number reproduced exactly; detection is
honest (collapses to 0.297 with signal removed), non-tautological (identical
data/threshold/path, only SNR differs), runs the real diagnostics + gate
stack, both canary polarities fail loudly under live mutation, and all
fixtures were restored byte-identical. Warnings are documentation-level
(declared 4.01 vs actual 4.00) and a faithfulness nit on the clean-twin flag.
