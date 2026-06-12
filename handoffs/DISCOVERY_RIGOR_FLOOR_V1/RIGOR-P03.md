# RIGOR-P03 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P03` - Sealed Holdout Window + Access Log + Contamination Gating  
Lane: YELLOW  
Branch: `auto/discovery_rigor_floor_v1/rigor-p03-sealed-holdout-window-access-log-contamination-gating`  
Executor: Codex

## Scope Completed

- Added `src/alpha_system/governance/sealed_holdout.py` with:
  - `SealedHoldoutWindow` schema, stable `holdwin_` IDs, canonical JSON round
    trips, status validation, optional value-free provenance, and
    exactly-one-active declaration enforcement.
  - Terminal `BREACHED` transition enforcement via
    `transition_sealed_holdout_status()` with explicit audit metadata.
  - `HoldoutAccessLog` append-only JSONL persistence for `haccess_` records;
    no update/delete mutation surface is exposed.
  - Conservative access-window intersection logic and fail-closed logging for
    unauthorized `LOCKED_TEST` access.
- Added ID kinds/prefixes for `SealedHoldoutWindow` and `HoldoutAccessLog`.
- Wired sealed-holdout access logging into:
  - `label_leakage_guard.check_label_leakage()` using optional keyword-only
    parameters so existing callers remain unchanged.
  - `validate_variant_and_family_budget()` as the RIGOR-P02 study-entry hook;
    when armed, missing/unwritable access logs block before VariantLedger append.
- Wired `PromotionGateContext` and `validate_governance_transition()` so
  `DIAGNOSTICS_RUN -> EVIDENCE_READY` blocks on:
  - any `TrialLedgerRecord.locked_test_contamination_flag`;
  - a required-but-missing sealed holdout declaration;
  - a `BREACHED` sealed holdout window.
  No waiver parameter was added.
- Added optional `alpha governance build-evidence` plumbing for
  `--sealed-holdout-registry-path` and `--require-sealed-holdout`.
- Declared the initial value-free kill-shot sealed window under
  `research/discovery_rigor_floor_v1/sealed_holdout/`.
- Added governance and discovery-rigor bypass-canary tests.
- Updated the README snapshot for RIGOR-P03.

## Declared Window

- `window_id`: `holdwin_d5cba50af19976275ab26f34`
- `status`: `SEALED`
- `date_range`: `2025-01-01` through `2026-06-11`
- Declaration file:
  `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json`
- The declaration is value-free metadata only and cites
  `docs/OPERATING_COMPASS_V4.md` Stage B sealed-holdout doctrine.

## Curated File List For Ralph

- `README.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P03.md`
- `research/discovery_rigor_floor_v1/sealed_holdout/GATE_INVENTORY.md`
- `research/discovery_rigor_floor_v1/sealed_holdout/kill_shot_sealed_holdout_window.json`
- `src/alpha_system/cli/governance.py`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/ids.py`
- `src/alpha_system/governance/label_leakage_guard.py`
- `src/alpha_system/governance/promotion_gate.py`
- `src/alpha_system/governance/sealed_holdout.py`
- `src/alpha_system/governance/variant_ledger.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py`
- `tests/unit/governance/test_ids.py`
- `tests/unit/governance/test_promotion_gate_state_machine.py`
- `tests/unit/governance/test_sealed_holdout.py`
- `tests/unit/governance/test_variant_ledger.py`

No files were staged by the executor.

## Gate To Bypass-Test Map

| Gate / fail-closed path | Test that fails if neutered |
|---|---|
| Exactly one active sealed holdout declaration | `tests/unit/governance/test_sealed_holdout.py::test_registry_enforces_exactly_one_active_window` |
| Second active window declaration rejected | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_second_active_window_canary_blocks_declaration` |
| `BREACHED` cannot become active again | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_unbreach_canary_blocks_terminal_status_flip` |
| Append-only access log blocks unwritable logging | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_access_log_canary_blocks_unwritable_log` |
| Label leakage guard emits access log when armed | `tests/unit/governance/test_sealed_holdout.py::test_label_leakage_guard_emits_holdout_access_log` |
| Study-entry hook emits access log when armed | `tests/unit/governance/test_variant_ledger.py::test_entry_hook_emits_holdout_access_log_when_access_intersects` |
| Unauthorized `LOCKED_TEST` access logs then blocks | `tests/unit/governance/test_sealed_holdout.py::test_unauthorized_locked_test_access_is_logged_then_blocks` |
| `EVIDENCE_READY` blocks contamination with no metadata waiver | `tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py::test_contamination_canary_blocks_evidence_ready_even_with_metadata` |
| `EVIDENCE_READY` blocks a BREACHED sealed window | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_breached_sealed_holdout_window` |
| Required holdout declaration missing blocks `EVIDENCE_READY` | `tests/unit/governance/test_promotion_gate_state_machine.py::test_evidence_ready_blocks_missing_required_holdout_declaration` |
| Initial declaration validates as exactly one active value-free window | `tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py::test_kill_shot_sealed_holdout_declaration_validates_value_free` |

## Validation Results

| Command | Result | Notes |
|---|---:|---|
| `git status --short` | NOT RUN | Executor prompt explicitly forbids `git status`. |
| `python -m py_compile src/alpha_system/governance/sealed_holdout.py src/alpha_system/governance/promotion_gate.py src/alpha_system/governance/variant_ledger.py src/alpha_system/governance/label_leakage_guard.py src/alpha_system/cli/governance.py tests/unit/governance/test_sealed_holdout.py tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py` | PASS | Exit 0. |
| `python -m pytest tests/unit/governance/test_sealed_holdout.py tests/unit/governance/test_promotion_gate_state_machine.py tests/unit/governance/test_variant_ledger.py tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py -q` | PASS | `60 passed in 0.12s`. |
| `python -m pytest tests/unit/governance -q` | PASS | `601 passed in 3.52s`. |
| `python -m pytest tests/unit/discovery_rigor_floor -q` | PASS | `11 passed in 0.05s`. |
| `python tools/verify.py --smoke` | PASS | Exit 0, no stdout/stderr. |
| `python tools/hooks/canary_runner.py` | PASS | All Frontier canaries passed. |
| `python -m ruff check src/alpha_system/governance/sealed_holdout.py src/alpha_system/governance/promotion_gate.py src/alpha_system/governance/variant_ledger.py src/alpha_system/governance/label_leakage_guard.py src/alpha_system/cli/governance.py tests/unit/governance/test_sealed_holdout.py tests/unit/governance/test_promotion_gate_state_machine.py tests/unit/governance/test_variant_ledger.py tests/unit/discovery_rigor_floor/test_rigor_p03_bypass_canaries.py tests/unit/discovery_rigor_floor/test_rigor_p03_sealed_holdout_declaration.py tests/unit/governance/test_ids.py` | PASS | `All checks passed!`. |
| `test -d research/discovery_rigor_floor_v1/sealed_holdout` | PASS | Directory exists. |
| `git diff --quiet -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | NOT RUN | Executor prompt explicitly forbids `git diff`. |
| `git ls-files -m -o --exclude-standard -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | PASS | Exit 0, no output; no tracked or untracked changes under historical evidence dirs. |
| `git ls-files runs` | PASS | Exit 0, no output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | Exit 0, no output. |
| `git ls-files -m -o --exclude-standard` | PASS | Output contained only the curated files listed above before this handoff was written; after handoff, add this handoff path to the same curated set. |

## Confirmations

- Historical Core Pilot evidence directories under `study_specs/`,
  `reviewer_verdicts/`, `evidence/`, and `ledgers/` were not edited by this
  executor; the allowed `git ls-files -m -o --exclude-standard -- ...` audit
  printed no output.
- `git ls-files runs` printed no output.
- Heavy tracked-artifact globs printed no output.
- The prompt-provided run artifact directory
  `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P03` was not
  present in this checkout; no run-local handoff was written.
- No `review.md`, `verdict.json`, or `reviews/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P03/**`
  artifact was created by the executor; Yellow-lane review is Ralph-owned.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.
- No PR, merge, reviewer call, live trading, paper trading, broker operation,
  order routing, deployment, destructive cleanup, FUTSUB run-state change,
  market-data materialization, registry mutation, or value computation was
  performed.

## Notes For Review

- `locked_test_contamination_metadata` remains present for legacy context
  compatibility, but `DIAGNOSTICS_RUN -> EVIDENCE_READY` now blocks any
  contaminated TrialLedger record before metadata can function as a waiver.
- Existing callers remain backward compatible unless they explicitly require a
  sealed holdout registry or arm holdout access logging.
- The optional `build-evidence` CLI holdout arguments are read/validation
  plumbing only; no holdout CLI write path was added.

## Next Step

Ralph should stage the curated files explicitly, run handoff validation and the
Yellow-lane fresh review, then proceed with PR/CI/merge-gate handling if review
passes.
