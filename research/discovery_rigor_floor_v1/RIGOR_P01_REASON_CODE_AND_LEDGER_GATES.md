# RIGOR-P01 Reason-Code And Ledger Gates

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P01`

## Landed Taxonomy

`src/alpha_system/governance/verdict_reason_code.py` defines exactly:

| reason_code |
|---|
| `UNDERPOWERED` |
| `SUBSTRATE_GAP` |
| `COST_FRAGILE` |
| `DATA_QUALITY` |
| `LEAKAGE_BLOCKED` |
| `DUPLICATE_EXPOSURE` |
| `REGIME_UNSTABLE` |
| `BBO_PROXY_LIMITATION` |

Validation accepts only enum instances or exact string values. Free text,
near-misses, lowercase variants, empty strings, and placeholders are rejected.

## Reason-Code Coupling

| record type | INCONCLUSIVE surface | reason_code rule |
|---|---|---|
| `ReviewerVerdict` | `verdict == INCONCLUSIVE` | required and taxonomy-valid |
| `PromotionDecision` | `decision == INCONCLUSIVE`, with `next_state == INCONCLUSIVE` | required and taxonomy-valid |
| `EvidenceBundle` | `diagnostics_summary.diagnostics_status == INCONCLUSIVE` | required and taxonomy-valid |

When `reason_code` is present on a non-INCONCLUSIVE record, it is still
taxonomy-validated. Existing records without `reason_code` keep absent-field
serialization and stable IDs. New records include `reason_code` in deterministic
ID components only when the field is present.

## Ledger-Presence Gate

`require_trial_ledger_present()` is invoked on the
`DIAGNOSTICS_RUN -> EVIDENCE_READY` promotion-gate path. The ledger location is
sourced from `PromotionGateContext.trial_ledger_path`.

Fail-closed modes:

| failure mode | gate issue code |
|---|---|
| missing path | `missing_trial_ledger_path` |
| missing file | `missing_trial_ledger` |
| unreadable file | `unreadable_trial_ledger` |
| unparseable JSON | `unparseable_trial_ledger` |
| unwritable file | `unwritable_trial_ledger` |

The writability probe opens the existing ledger in `r+` mode without writing.
Tests compare bytes before and after the probe.

## Gate To Bypass-Test Map

| enforcement path | bypass/regression test |
|---|---|
| Exact 8-code taxonomy; free text rejected | `tests/unit/governance/test_verdict_reason_code.py::test_verdict_reason_code_taxonomy_is_exactly_the_compass_set`; `test_verdict_reason_code_rejects_free_text_near_misses_and_placeholders` |
| `ReviewerVerdict` INCONCLUSIVE requires `reason_code` | `tests/unit/governance/test_reviewer_verdict.py::test_reviewer_verdict_inconclusive_requires_reason_code`; `test_reviewer_verdict_rejects_free_text_reason_code` |
| `ReviewerVerdict` INCONCLUSIVE is not merge-eligible | `tests/unit/governance/test_reviewer_verdict.py::test_reviewer_verdict_inconclusive_reason_code_is_not_merge_eligible` |
| `PromotionDecision` INCONCLUSIVE requires `reason_code` | `tests/unit/governance/test_promotion.py::test_promotion_decision_inconclusive_requires_reason_code`; `test_promotion_decision_rejects_free_text_reason_code` |
| `PromotionDecision` INCONCLUSIVE is non-advancing | `tests/unit/governance/test_promotion.py::test_promotion_decision_inconclusive_is_non_advancing_and_reason_coded`; `tests/unit/governance/test_promotion_gate_state_machine.py::test_reviewed_to_inconclusive_is_non_advancing_and_reason_coded` |
| `EvidenceBundle` INCONCLUSIVE diagnostics require `reason_code` | `tests/unit/governance/test_evidence_bundle.py::test_evidence_bundle_diagnostics_inconclusive_requires_reason_code`; `test_evidence_bundle_rejects_free_text_reason_code` |
| Missing trial ledger blocks EVIDENCE_READY | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_transition_blocks_missing_trial_ledger` |
| Unwritable trial ledger blocks EVIDENCE_READY | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_transition_blocks_unwritable_trial_ledger` |
| Unparseable trial ledger blocks EVIDENCE_READY | `tests/unit/governance/test_promotion_gate_state_machine.py::test_trial_ledger_presence_probe_blocks_unparseable_json` |
| Ledger probe is non-destructive | `tests/unit/governance/test_promotion_gate_state_machine.py::test_trial_ledger_presence_probe_is_non_destructive` |
| Six annotation content refs bind to originals | `tests/unit/discovery_rigor_floor/test_verdict_annotations.py::test_core_pilot_verdict_annotations_bind_to_original_inconclusive_verdicts` |

## Annotation Table

| study_spec_id | reason_code | basis citation | original sha256 | hash checked |
|---|---|---|---|---|
| `sspec_02c400a561891171a33c0c66` | `SUBSTRATE_GAP` | `judgement.basis`: objective trigger counts unresolved without locked structure FeaturePack; thin-session subsegments unresolved | `b5089ce28bdeb48e3fac9f034910abb620331cf5bea1f4835ef88b0b1cc334bf` | true |
| `sspec_267cc052e37668339c38d179` | `SUBSTRATE_GAP` | `judgement.basis`: locked trendiness and activation binding missing; source probe arms rejected | `a44718e28be05fedfddb5792a573580bf822b809e1b685412d72fa9cfa0ce25e` | true |
| `sspec_27bf1262b0bd23d27191cc86` | `SUBSTRATE_GAP` | `judgement.basis`: objective trigger counts unresolved without locked structure FeaturePack; thin-session subsegments unresolved | `9e35cfb38126d4f42ffb756ca02f313a1e254c4eeea59bf5f8eb11f1eb7ca590` | true |
| `sspec_69c22ec5847395ac8e81b5b6` | `SUBSTRATE_GAP` | `judgement.basis`: VWAP/session trigger FeaturePack not locked; 15m label pack unresolved | `1025459249320d297a850ff4b660b3e5912911de6ab35c31a9fb42c1ad374fda` | true |
| `sspec_9f6f741192a4b534f06e51c0` | `BBO_PROXY_LIMITATION` | `judgement.basis`: no locked BBO FeaturePack resolves; RTH session cost cells zero-fill or inconclusive | `011501dbfd9685bfd2c802026636aa5fad9882c68f2897ab6fb9a97c16ac9523` | true |
| `sspec_aff70fcbc4b7ff226fcc8149` | `SUBSTRATE_GAP` | `judgement.basis`: VWAP FeaturePack binding not locked; active-session final aggregates unproven | `77537504219f3d07dfdcd50690e771db4d0b08dc6217c8d3c1a2b9e95e7b6eba` | true |

## Validation Snapshot

Executor-scoped checks completed:

| command | result |
|---|---|
| `python -m pytest tests/unit/governance -q` | PASS, 556 tests |
| `python -m pytest tests/unit/discovery_rigor_floor -q` | PASS, 1 test |
