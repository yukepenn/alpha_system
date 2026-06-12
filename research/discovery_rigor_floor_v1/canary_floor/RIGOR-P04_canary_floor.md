# RIGOR-P04 Canary Floor Evidence

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P04`  
Evidence type: value-free canary inventory and gate mapping

## Executable Negative Controls

All four catalogued `REQUIRED_NEGATIVE_CONTROL_TYPES` are executable through
`src/alpha_system/governance/canaries/harness.py` and
`tools/hooks/canary_runner.py`.

| Catalog order | Control | Fixture | Runner surface | Expected result |
|---:|---|---|---|---|
| 1 | `random_target` | `evals/canaries/random_target/synthetic_fixture.json` | `run_random_target_canary`, `main(['--canary', 'random_target'])`, `governance_random_target` | `PASS` when seeded random target has no surviving signal |
| 2 | `permuted_labels` | `evals/canaries/permuted_labels/synthetic_fixture.json` | `run_label_leakage_canary`, `governance_permuted_labels` | `PASS` when label overlap is blocked |
| 3 | `future_shift` | `evals/canaries/future_shift/synthetic_fixture.json` | `run_future_shift_canary`, `governance_future_shift` | `PASS` when lookahead is blocked |
| 4 | `optimistic_fill` | `evals/canaries/optimistic_fill/synthetic_fixture.json` | `run_optimistic_fill_canary`, `governance_optimistic_fill` | `PASS` when optimistic fill assumptions are blocked |

## Planted-Fake-Alpha Outcome

`PlantedFakeAlphaStudyCanary` uses
`evals/canaries/planted_fake_alpha/synthetic_fixture.json`, where each label at
bar `t` is constructed from future bar `t+1` metadata. The canary assembles a
strict `EvidenceBundle`, validates `validate_evidence_ready_gate`, writes only
tmp trial/variant/sealed-holdout ledgers, and then calls the real promotion
gate.

Outcome: `REJECTED`.

Blocking gate: `DIAGNOSTICS_RUN -> EVIDENCE_READY`.

Blocking issue: `locked_test_contamination_blocks_evidence_ready`.

## Gate To Bypass-Test Mapping

| Gate / fail-closed path | Test that fails if neutered |
|---|---|
| `RANDOM_TARGET` remains executable in catalog order | `tests/unit/governance/test_canary_harness.py::test_required_governance_canaries_run_in_canonical_scope`; `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_required_negative_controls_are_four_executable_in_catalog_order` |
| RANDOM_TARGET missed guard records `FAIL` | `tests/unit/governance/test_canary_harness.py::test_missed_guard_is_recorded_as_fail[random_target-run_random_target_canary]` |
| `EVIDENCE_READY` requires all required controls | `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_requires_all_required_negative_controls`; `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_missing_required_negative_control_through_gate` |
| `EVIDENCE_READY` blocks a `FAIL` control | `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_blocks_failed_negative_control_result` |
| `EVIDENCE_READY` blocks stale/mismatched control results | `tests/unit/governance/test_evidence_bundle.py::test_evidence_ready_gate_blocks_stale_negative_control_result` |
| Planted lookahead study is rejected by the real gate | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_planted_fake_alpha_canary_rejects_contaminated_study` |
| De-contaminating the planted fixture makes the canary fail | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_decontaminated_planted_fixture_fails_the_canary` |
| `canary_runner.py` registers random-target and planted expected-block scenarios | `tests/unit/discovery_rigor_floor/test_rigor_p04_canary_floor.py::test_canary_runner_registers_random_target_and_planted_fake_alpha` |

No real-data study, score, alpha, profitability, tradability, broker, paper,
live, production, or deployment claim is made by this evidence note.
