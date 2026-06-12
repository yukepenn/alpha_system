# RIGOR-P07 Full-Gated-Path Integration Audit

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
Phase: `RIGOR-P07`
Evidence type: value-free gate engagement and bypass-canary map

This audit records only gate names, issue codes, test node ids, canary ids, and
status citations. It contains no feature, label, return, score, PnL, or market
values.

## Audit Command

```bash
python -m pytest tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py -q
```

Expected focused result: `1 passed`.

## Gate Table

| Gate station | Engaged evidence | Fail-closed trigger proven by integration audit | Existing bypass-canary / canary-style ref |
|---|---|---|---|
| Variant/family budget entry hook | `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py::test_full_gated_path_engages_every_rigor_floor_gate_and_blocks_bypasses` calls `validate_variant_and_family_budget`, persists one `VariantLedgerRecord`, and confirms study/family budgets are `RESPECTED`. | Same node injects three observed variants against budget 2 and blocks with `variant_budget_overrun`. | `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_entry_hook_canary_blocks_variant_budget_overrun`; `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_unwritable_ledger_canary_blocks_entry_hook` |
| Trial-ledger recording and presence/writability gate | Same node writes a tmp trial-ledger JSON containing the synthetic `TrialLedgerRecord` and reaches `DIAGNOSTICS_RUN -> EVIDENCE_READY` only with that ledger path. | Same node blocks missing ledger with `missing_trial_ledger` and chmod-unwritable ledger with `unwritable_trial_ledger`. | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_missing_trial_ledger_path`; `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_transition_blocks_unwritable_trial_ledger`; `tests/unit/governance/test_promotion_gate_state_machine.py::test_trial_ledger_presence_probe_is_non_destructive` |
| Sealed holdout access log and contamination gate | Same node arms a tmp `SealedHoldoutWindow`, calls the study-entry hook with intersecting access metadata, and confirms one `HoldoutAccessLog` row. | Same node pokes intersecting `LOCKED_TEST` access outside an authorized evaluation context and blocks with `unauthorized_locked_test_holdout_access`; contaminated trial blocks promotion with `locked_test_contamination_blocks_evidence_ready`. | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_access_log_canary_blocks_unwritable_log`; `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_contamination_canary_blocks_evidence_ready_even_with_metadata`; `tests/unit/governance/test_sealed_holdout.py::test_unauthorized_locked_test_access_is_logged_then_blocks` |
| Negative-control floor: 4/4 controls plus planted fake-alpha | Same node runs `run_planted_fake_alpha_canary` in a pytest tmp workspace, carries its `future_shift` outcome into the audit bundle, adds the other three required control results, and validates `validate_evidence_ready_gate`. | Same node omits `optimistic_fill` and blocks with `missing_required_negative_control_result`. | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_required_negative_controls_are_four_executable_in_catalog_order`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_planted_fake_alpha_canary_rejects_contaminated_study`; canary ids `governance_random_target`, `governance_permuted_labels`, `governance_future_shift`, `governance_optimistic_fill`, `planted_fake_alpha` |
| Reason-coded verdict requirement | Same node creates an `INCONCLUSIVE` reviewer verdict with `reason_code=UNDERPOWERED` and confirms it validates. | Same node creates an `INCONCLUSIVE` reviewer verdict without `reason_code` and blocks with `missing_reason_code_for_inconclusive`. | `tests/unit/governance/test_reviewer_verdict.py::test_reviewer_verdict_inconclusive_requires_reason_code`; `tests/unit/governance/test_promotion.py::test_promotion_decision_inconclusive_requires_reason_code`; `tests/unit/governance/test_evidence_bundle.py::test_evidence_bundle_diagnostics_inconclusive_requires_reason_code` |
| Promotion gate composition | Same node reaches `DIAGNOSTICS_RUN -> EVIDENCE_READY` only when trial ledger, VariantLedger, sealed holdout, no contamination, and all controls agree, then reaches `REVIEWED -> CANDIDATE` with an independent reviewer verdict and complete trial refs. | Same node blocks contaminated evidence with `locked_test_contamination_blocks_evidence_ready` and an unrecorded promotion VariantLedger with `variant_ledger_missing_records`. | `tests/unit/governance/test_promotion_gate_state_machine.py::test_reviewed_to_candidate_requires_complete_promotion_gate`; `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_promotion_gate_canary_blocks_unrecorded_variant_ledger`; `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_requires_all_required_negative_controls` |

## Isolation Confirmation

The integration audit writes only to pytest `tmp_path` namespaces: trial ledger
JSON, VariantLedger JSONL, sealed-holdout declaration JSON, holdout access log
JSONL, and planted-fake-alpha workspace output. No run dir, FUTSUB state,
registry, value store, raw data, canonical data, or historical evidence path is
targeted by the test.
