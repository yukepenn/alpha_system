# RIGOR-P03 Sealed Holdout Gate Inventory

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P03`

## Declared Window

- `window_id`: `holdwin_d5cba50af19976275ab26f34`
- `status`: `SEALED`
- `date_range`: `2025-01-01` through `2026-06-11`
- `partition`: value-free metadata for the FUTSUB/Core Pilot kill-shot locked
  test partition.
- `compass_ref`: `docs/OPERATING_COMPASS_V4.md` Stage B sealed holdout doctrine.

No market data values, study values, feature values, label values, returns, or
diagnostic metric outputs are recorded in this declaration.

## Gate To Test Map

| Gate | Deterministic test |
|---|---|
| Exactly one active sealed holdout window | `tests/unit/governance/test_sealed_holdout.py::test_registry_enforces_exactly_one_active_window` |
| BREACHED is terminal | `tests/unit/governance/test_sealed_holdout.py::test_breached_status_is_terminal_and_monotonic` |
| Append-only access log blocks unwritable logging | `tests/unit/governance/test_sealed_holdout.py::test_holdout_access_log_unwritable_fails_closed` |
| Label leakage guard emits holdout access log | `tests/unit/governance/test_sealed_holdout.py::test_label_leakage_guard_emits_holdout_access_log` |
| Study-entry hook emits holdout access log | `tests/unit/governance/test_variant_ledger.py::test_entry_hook_emits_holdout_access_log_when_access_intersects` |
| `EVIDENCE_READY` blocks locked-test contamination with no waiver | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_locked_test_contamination_without_waiver` |
| `EVIDENCE_READY` blocks BREACHED holdout | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_breached_sealed_holdout_window` |

## Bypass Canaries

| Bypass class | Canary test |
|---|---|
| Silenced/unwritable access log treated as pass | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_access_log_canary_blocks_unwritable_log` |
| BREACHED window flipped back active | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_unbreach_canary_blocks_terminal_status_flip` |
| Contamination block neutered | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_contamination_canary_blocks_evidence_ready_even_with_metadata` |
| Second active window declaration accepted | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_second_active_window_canary_blocks_declaration` |
