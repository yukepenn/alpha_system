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

- `MET`: 13
- `PENDING-coordinator`: 0
- Coordinator closure record: rows 8, 9, 11 re-reconciled vs the POST-RELOCK_V2
  corpus 2026-06-13 (V2 audits, see in-row); row 6 closed 2026-06-13 by six
  per-family real-data calibrations (all `zero-pass-met`). All 13 rows `MET`.
- Kill-shot fire condition: all 13 rows `MET` — SATISFIED.

## Checklist

| # | Item | Status | Deterministic evidence | Closing step if pending |
|---:|---|---|---|---|
| 1 | Full gated-path integration audit engages every RIGOR gate and proves fail-closed direction | `MET` | `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py::test_full_gated_path_engages_every_rigor_floor_gate_and_blocks_bypasses`; audit table `research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`; command `python -m pytest tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py -q` expected `1 passed` | n/a |
| 2 | Sealed window exactly one active declaration | `MET` | `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json` has one `SEALED` open-ended window; `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py::test_kill_shot_sealed_holdout_declaration_validates_value_free`; `tests/unit/governance/test_sealed_holdout.py::test_registry_enforces_exactly_one_active_window` | n/a |
| 3 | 4/4 required negative controls and planted fake-alpha canary are executable and expected green through `canary_runner` | `MET` | `research/discovery_rigor_floor_v1/canary_floor/RIGOR-P04_canary_floor.md`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_required_negative_controls_are_four_executable_in_catalog_order`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_planted_fake_alpha_canary_rejects_contaminated_study`; command `python tools/hooks/canary_runner.py` expected `All Frontier canaries passed.` | n/a |
| 4 | TrialLedger and VariantLedger presence/writability gates are live | `MET` | Integration audit row 2 and row 1; `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_transition_blocks_unwritable_trial_ledger`; `tests/unit/governance/test_variant_ledger.py::test_entry_hook_blocks_missing_and_unwritable_ledger` | n/a |
| 5 | Reason-code validation is live for INCONCLUSIVE verdicts | `MET` | `tests/unit/governance/test_reviewer_verdict.py::test_reviewer_verdict_inconclusive_requires_reason_code`; `tests/unit/governance/test_promotion.py::test_promotion_decision_inconclusive_requires_reason_code`; integration audit issue code `missing_reason_code_for_inconclusive` | n/a |
| 6 | Surrogate calibration satisfies compass v4.4 section 7.2 statistical floor | `MET` | Six per-family real-data calibrations 2026-06-13 (`research/discovery_rigor_floor_v1/surrogate_fdr/{vwap_session_f6cbd8,vwap_session_1604b0,regime_dec89a,liquidity_pa_840e83,liquidity_pa_c237c6,bbo_tradability_533f66}_real_calibration_v2.md`): per-family K (combined `Run count` = sub_configs×3×2) = 864/864/720/1296/1296/1140, all `>= 60`; **zero statistic passes; error count 0** in all six; both dependence-preserving nulls (`trade_date_block_shuffle` + `trade_date_block_bootstrap`) equal-weighted per family; bound `zero passes in K bounds false-pass rate at about 3/K at 95%` → `<= 0.42%` (floor ~5%); detection statistic = shared `directional.pearson_ic` `>=0.95` threshold proven by the TRUE-alpha canary (#399). Degenerate-input exclusions are RECORDED substrate findings (not errors): bbo 74 (24 `spread_ticks` all-null + 50 constant/zero-variance flag sub-configs — RIGOR-P05 constant-factor exclusion, fresh adversarial mutation review PASS_WITH_WARNINGS, all 5 mutations killed); other families 0. Note: report line "Declared K per perturbation config: 3" is the per-sub-config budget; family K is the report `Run count`. | n/a |
| 7 | HOLDOUT COVERAGE: declared window intersects every committed re-locked StudySpec input | `MET` | P033000 contract test `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py::test_kill_shot_window_intersects_every_relocked_locked_test_input`; review `reviews/DISCOVERY_RIGOR_FLOOR_V1/P033000_HOLDOUT_WINDOW_COVERAGE-review.md`; declaration provenance cites 10 re-locked specs and 32 locked-test partitions | n/a |
| 8 | VARIANT RECONCILIATION: every kill-shot study invocation matched to a VariantLedger entry | `MET` | Coordinator audit re-run vs POST-RELOCK_V2 corpus 2026-06-13: `research/discovery_rigor_floor_v1/variant_reconciliation/FUTSUB_KILL_SHOT_variant_reconciliation_v2.md` (supersedes the 2026-06-12 V1 audit) — six V2 rerun invocations `pending_creation_enforced` with fail-closed citations (`promotion_gate.py:208-243`, `variant_ledger.py:731-745`), zero `unmatched_gap`; V2 Track-B pooled entries 2/2 exact-matched (`poolhyp_d3b3d986369b525618a1caa0` cross_symbol, `poolhyp_0755f59753552574a8092624` cross_horizon, anchor `sspec_f6cbd88caa0445f0f56d81fd`). | n/a |
| 9 | SUBSTRATE-INVARIANT AUDIT: live registries green | `MET` | Coordinator audit re-run vs POST-RELOCK_V2 + post-re-materialization registry 2026-06-13: `research/discovery_rigor_floor_v1/substrate_invariant/FUTSUB_KILL_SHOT_substrate_invariant_audit_v2.md` (supersedes the 2026-06-12 V1 audit; corrects the stale `4560` count) — predicates 1/2/4 PASS (0 constant flag columns; 17,055/17,073 trading-day cells with 2 session values, 18 exceptions are 3 exchange-closure dates; V2 corpus **4112 feature + 840 label lock handles → 1168 distinct fver + 96 distinct lver, all `REGISTERED`** with 0 missing-Parquet / 0 DEPRECATED-referenced / 0 hash mismatch, coordinator-spot-verified; 168 deprecate-first + 448 R-036 retired locks all 0-referenced; 24/24 DatasetVersions accepted), predicate 3 the role-marker WARN re-verified (696-row, benign DEPRECATED growth) and tolerated via `input_resolver.py:1824-1828`. | n/a |
| 10 | POWER MEMOS: per-study MDE memos on real N_eff written before Track A metrics | `MET` | `research/discovery_rigor_floor_v1/power_memos/KILL_SHOT_POWER_MEMOS.md` covers the six re-locked rerun candidates and states it was written before Track A rerun metrics; review PR #394 cited by the phase spec | n/a |
| 11 | TRACK-B MANDATORY MINIMUM: >=1 cross-symbol and >=1 cross-horizon pooled hypothesis registered pre-metric | `MET` | POST-RELOCK_V2 registration 2026-06-12T12:40:00Z against the V2 anchor `sspec_f6cbd88caa0445f0f56d81fd`, `registered_before_metrics: true` (coordinator-verified in live registry 2026-06-13): `poolhyp_d3b3d986369b525618a1caa0` (cross_symbol ES/NQ/RTY@5m) + `poolhyp_0755f59753552574a8092624` (cross_horizon ES@5m/15m/30m), both exact-matched to the live VariantLedger (see row 8 v2 audit); the 2026-06-12T05:06:10Z V1 records (`poolhyp_67427c04...`, `poolhyp_797417343...`, retired anchor `652fcc`) remain as immutable history and are NOT post-RELOCK_V2 evidence. Value-free record `research/discovery_rigor_floor_v1/track_b/REGISTERED_RECORD.md`. | n/a |
| 12 | SUBSTRATE-CAVEAT REGISTER: residuals stated before kill-shot context | `MET` | This checklist and resume handoff state the required caveats: R-037 `contract_id` caveat, BBO-proxy regime limits, and (added 2026-06-13 from the row 6 bbo calibration) the **BBO proxy-flag degeneracy** caveat — `spread_ticks` all-null on 24/24 sampled instrument-years, `low_depth_flag` zero-variance on 24/24, `wide_spread_flag` on 18/24 (74 bbo sub-configs excluded as degenerate substrate). FUTSUB resume step 3 requires copying them into the kill-shot run context before STOP removal. | n/a |
| 13 | REAL FEE CONSTANTS: versioned sourced fee schedule live in base cost profile | `MET` | `src/alpha_system/backtest/futures_fees.py` exposes `fee_schedule_cme_equity_index_retail_discount_v2_2026_06_11`; `tests/unit/runtime/cost/test_real_fee_schedule.py::test_real_fee_schedule_pins_symbol_all_in_totals_and_keeps_history`; `tests/unit/runtime/cost/test_real_fee_schedule.py::test_default_base_profile_consumes_real_fee_version_and_zero_cost_stays_zero`; review `reviews/DISCOVERY_RIGOR_FLOOR_V1/P035000_REAL_FEE_CONSTANTS-review.md` | n/a |

## Pending Items

The coordinator must close these before removing the FUTSUB boundary STOP:

1. `PENDING-coordinator` surrogate section 7.2 calibration: run and record the
   qualifying real-data, dependence-preserving, per-family calibration. Any
   shuffled pass is a `LEAKAGE_BLOCKED` diagnosis first. (Machinery merged via
   PR #397: `trade_date_block_shuffle` + `trade_date_block_bootstrap` +
   `tools/discovery_rigor_floor/run_real_surrogate_calibration.py`.)

Closed 2026-06-12, RE-RECONCILED vs POST-RELOCK_V2 corpus 2026-06-13 (rows 8, 9,
11): the original audits/registration were generated 2026-06-12T05:06Z — BEFORE
P110000_RELOCK_V2 rotated the substrate later that day — so they cited V1
objects. Re-run against V2: VariantLedger reconciliation
(`variant_reconciliation/..._v2.md`, PASS, 0 unmatched_gap), substrate-invariant
audit (`substrate_invariant/..._v2.md`, GREEN, 1168 distinct fver + 96 lver all
REGISTERED), Track-B re-registered pre-metric against anchor f6cbd88
(`poolhyp_d3b3d986`, `poolhyp_0755f597`). All three rows now cite V2 evidence.

## Caveat Register

- R-037 `contract_id` caveat: roll/contract identity caveats remain part of the
  kill-shot context; verdicts must inherit the caveat rather than rediscover it.
- BBO-proxy regime limits: BBO inputs are a top-book proxy and not execution
  truth; missing or proxy-limited BBO evidence remains a reason-code caveat,
  not a tradability claim.
- BBO proxy-flag degeneracy (added 2026-06-13, row 6 calibration): the bbo
  tradability flag factors are largely degenerate substrate on the sampled
  instrument-years — `spread_ticks` all-null (24/24), `low_depth_flag`
  zero-variance (24/24), `wide_spread_flag` (18/24), plus `bad_quote_flag` /
  `missing_bbo_flag` constant on a few partitions (74 bbo sub-configs total
  excluded as degenerate). These exclusions are recorded substrate findings,
  not pipeline errors; they reinforce that BBO is a tradability proxy and that
  bbo-family verdicts must carry this coverage caveat rather than treat absent
  flag variance as signal.

No alpha, profitability, tradability, execution-quality, production-readiness,
paper-trading, live-trading, broker, order-routing, or deployment claim is made.
