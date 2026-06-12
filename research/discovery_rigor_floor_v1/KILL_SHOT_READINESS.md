# FUTSUB Kill-Shot Readiness Checklist

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
Phase: `RIGOR-P07`
Status vocabulary: `MET` or `PENDING-coordinator`.

Fail-closed rule: FUTSUB-P28 must not fire while any row is
`PENDING-coordinator`. Synthetic CI reports prove machinery only; they do not
stand in for required real-data calibration or live registry audits. This file
is value-free: it records statuses, commands, issue codes, ids, and citations
only.

## Status Roll-Up

- `MET`: 9
- `PENDING-coordinator`: 4
- Kill-shot fire condition: all 13 rows `MET`.

## Checklist

| # | Item | Status | Deterministic evidence | Closing step if pending |
|---:|---|---|---|---|
| 1 | Full gated-path integration audit engages every RIGOR gate and proves fail-closed direction | `MET` | `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py::test_full_gated_path_engages_every_rigor_floor_gate_and_blocks_bypasses`; audit table `research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`; command `python -m pytest tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py -q` expected `1 passed` | n/a |
| 2 | Sealed window exactly one active declaration | `MET` | `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json` has one `SEALED` open-ended window; `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py::test_kill_shot_sealed_holdout_declaration_validates_value_free`; `tests/unit/governance/test_sealed_holdout.py::test_registry_enforces_exactly_one_active_window` | n/a |
| 3 | 4/4 required negative controls and planted fake-alpha canary are executable and expected green through `canary_runner` | `MET` | `research/discovery_rigor_floor_v1/canary_floor/RIGOR-P04_canary_floor.md`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_required_negative_controls_are_four_executable_in_catalog_order`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_planted_fake_alpha_canary_rejects_contaminated_study`; command `python tools/hooks/canary_runner.py` expected `All Frontier canaries passed.` | n/a |
| 4 | TrialLedger and VariantLedger presence/writability gates are live | `MET` | Integration audit row 2 and row 1; `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_transition_blocks_unwritable_trial_ledger`; `tests/unit/governance/test_variant_ledger.py::test_entry_hook_blocks_missing_and_unwritable_ledger` | n/a |
| 5 | Reason-code validation is live for INCONCLUSIVE verdicts | `MET` | `tests/unit/governance/test_reviewer_verdict.py::test_reviewer_verdict_inconclusive_requires_reason_code`; `tests/unit/governance/test_promotion.py::test_promotion_decision_inconclusive_requires_reason_code`; integration audit issue code `missing_reason_code_for_inconclusive` | n/a |
| 6 | Surrogate calibration satisfies compass v4.4 section 7.2 statistical floor | `PENDING-coordinator` | P05 machinery and synthetic report exist at `src/alpha_system/governance/surrogate_run.py` and `research/discovery_rigor_floor_v1/surrogate_fdr/RIGOR-P05_synthetic_calibration.md`, but that report is `K=2` synthetic CI evidence and does not satisfy the kill-shot floor. Acceptance requires declared real-data K, zero passes, bound statement `zero passes in K bounds false-pass rate at about 3/K at 95%`, `K>=60` for about 5%, session/trade-date-block shuffling minimum, at least one block-bootstrap configuration, and per-family configurations. | `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 5 |
| 7 | HOLDOUT COVERAGE: declared window intersects every committed re-locked StudySpec input | `MET` | P033000 contract test `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py::test_kill_shot_window_intersects_every_relocked_locked_test_input`; review `reviews/DISCOVERY_RIGOR_FLOOR_V1/P033000_HOLDOUT_WINDOW_COVERAGE-review.md`; declaration provenance cites 10 re-locked specs and 32 locked-test partitions | n/a |
| 8 | VARIANT RECONCILIATION: every kill-shot study invocation matched to a VariantLedger entry | `PENDING-coordinator` | RIGOR-P02/P07 prove the hook and gate, but the live six-rerun invocation reconciliation audit has not been produced in this phase because FUTSUB-P28 remains stopped. | `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 6 |
| 9 | SUBSTRATE-INVARIANT AUDIT: live registries green | `PENDING-coordinator` | No committed live-registry audit artifact in this phase proves all required predicates: no constant-valued flag columns, >=2 session values per trading day, role-marker WARN documented, and zero locks referencing `DEPRECATED` records. | `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 7 |
| 10 | POWER MEMOS: per-study MDE memos on real N_eff written before Track A metrics | `MET` | `research/discovery_rigor_floor_v1/power_memos/KILL_SHOT_POWER_MEMOS.md` covers the six re-locked rerun candidates and states it was written before Track A rerun metrics; review PR #394 cited by the phase spec | n/a |
| 11 | TRACK-B MANDATORY MINIMUM: >=1 cross-symbol and >=1 cross-horizon pooled hypothesis registered pre-metric | `PENDING-coordinator` | Helper and draft templates are present: `src/alpha_system/governance/pooled_hypothesis.py::track_b_minimum_satisfied`; `tests/unit/discovery_rigor_floor/test_pooled_track_b_readiness.py::test_track_b_minimum_helper_is_callable_from_readiness_checklist`; draft JSON templates under `research/discovery_rigor_floor_v1/track_b/`. Actual registration is intentionally deferred until kill-shot time before any Track A metric. | `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 4 |
| 12 | SUBSTRATE-CAVEAT REGISTER: residuals stated before kill-shot context | `MET` | This checklist and resume handoff state the required caveats: R-037 `contract_id` caveat and BBO-proxy regime limits. FUTSUB resume step 3 requires copying them into the kill-shot run context before STOP removal. | n/a |
| 13 | REAL FEE CONSTANTS: versioned sourced fee schedule live in base cost profile | `MET` | `src/alpha_system/backtest/futures_fees.py` exposes `fee_schedule_cme_equity_index_retail_discount_v2_2026_06_11`; `tests/unit/runtime/cost/test_real_fee_schedule.py::test_real_fee_schedule_pins_symbol_all_in_totals_and_keeps_history`; `tests/unit/runtime/cost/test_real_fee_schedule.py::test_default_base_profile_consumes_real_fee_version_and_zero_cost_stays_zero`; review `reviews/DISCOVERY_RIGOR_FLOOR_V1/P035000_REAL_FEE_CONSTANTS-review.md` | n/a |

## Pending Items

The coordinator must close these before removing the FUTSUB boundary STOP:

1. `PENDING-coordinator` surrogate section 7.2 calibration: run and record the
   qualifying real-data, dependence-preserving, per-family calibration. Any
   shuffled pass is a `LEAKAGE_BLOCKED` diagnosis first.
2. `PENDING-coordinator` Track-B registration: fill and register at least one
   cross-symbol and one cross-horizon pooled hypothesis before any Track A
   metric marker exists.
3. `PENDING-coordinator` VariantLedger reconciliation: emit a value-free audit
   over the six rerun candidate invocations showing each invocation has the
   intended ledger entry.
4. `PENDING-coordinator` substrate-invariant audit: emit a value-free live
   registry audit proving the four required predicates.

## Caveat Register

- R-037 `contract_id` caveat: roll/contract identity caveats remain part of the
  kill-shot context; verdicts must inherit the caveat rather than rediscover it.
- BBO-proxy regime limits: BBO inputs are a top-book proxy and not execution
  truth; missing or proxy-limited BBO evidence remains a reason-code caveat,
  not a tradability claim.

No alpha, profitability, tradability, execution-quality, production-readiness,
paper-trading, live-trading, broker, order-routing, or deployment claim is made.
