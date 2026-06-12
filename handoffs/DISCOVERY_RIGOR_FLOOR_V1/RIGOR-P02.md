# RIGOR-P02 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`  
Phase: `RIGOR-P02`  
Branch: `auto/discovery_rigor_floor_v1/rigor-p02-first-class-variantledger-family-budgets-fail-closed-entry-hook`  
Commits: none created by executor; changes left unstaged for Ralph.

## Repair Attempt Summary

- REWORK repair: restored the five P01 promotion-gate regressions that were lost
  from `tests/unit/governance/test_promotion_gate_state_machine.py` when the
  stale P00 worktree was extended for P02. The restored tests cover missing
  trial-ledger files, unwritable trial-ledger files, non-destructive presence
  probing, unparseable trial-ledger JSON, and reason-coded non-advancing
  `REVIEWED -> INCONCLUSIVE`.
- REWORK repair: restored the P01 `PromotionDecision` / `ReviewerVerdict`
  reason-code support in this stale checkout so the restored P01 tests execute
  locally. These are dependency-surface restorations from `origin/main`, not new
  P02 behavior; after Ralph rebuilds the branch on `origin/main`, they should
  collapse to no P02 diff except where P02 composes with them.
- Composed the P02 `DIAGNOSTICS_RUN -> EVIDENCE_READY` budget gate with P01's
  `require_trial_ledger_present()` gate. The trial-ledger presence/writability
  check now runs before the VariantLedger recorded-budget check.
- Reconciled `alpha governance build-evidence` so it passes both
  `--trial-ledger-path` and `--variant-ledger-path` into one
  `PromotionGateContext`.
- Removed the independent `ALPHA_VARIANT_LEDGER_PATH` environment fallback;
  VariantLedger budget enforcement now requires an explicit ledger path, matching
  the P01 fail-closed CLI/path-plumbing style.
- Fixed the family roll-up undercount: family exposure is counted by
  `(study_spec_id, variant_id)`, not by raw local `variant_id` alone. Added the
  cross-study same-label regression.
- Added the P01 `verdict_reason_code.py` module to this stale worktree so the
  dependency surface is present for local imports. The branch pointer itself
  remains at the stale P00 base; see caveats.

## Scope Delivered

- Added first-class `VariantLedgerRecord` and append-friendly JSONL `VariantLedger` persistence in `src/alpha_system/governance/variant_ledger.py`.
- Added `FamilyBudgetCheck`, family roll-up, budget amendment records with deterministic `bamend_` IDs, and `validate_variant_and_family_budget()`.
- Extended `TrialLedgerAccounting` with `TrialLedgerVariantSummary` / `summarize_trial_ledger_variants()` so VariantLedger records derive from the existing trial-ledger accounting surface.
- Added optional validated `StudySpec.family_budget`; legacy StudySpec payloads remain valid and omit the optional field from `to_dict()`.
- Wired variant/family budget enforcement into `DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN` and recorded-ledger budget enforcement into `DIAGNOSTICS_RUN -> EVIDENCE_READY`.
- Added read-only `alpha governance variant-ledger-summary`.
- Added governance tests and P02 bypass-canary unit tests.
- Added value-free gate inventory and README snapshot update.

## Files Created Or Modified

- `src/alpha_system/governance/variant_ledger.py`
- `src/alpha_system/governance/promotion.py` (P01 reason-code dependency surface restored in this stale worktree)
- `src/alpha_system/governance/reviewer_verdict.py` (P01 reason-code dependency surface restored in this stale worktree)
- `src/alpha_system/governance/study_spec.py`
- `src/alpha_system/governance/trial_ledger.py`
- `src/alpha_system/governance/promotion_gate.py`
- `src/alpha_system/governance/ids.py`
- `src/alpha_system/governance/__init__.py`
- `src/alpha_system/governance/verdict_reason_code.py` (P01 dependency surface restored in this stale worktree)
- `src/alpha_system/cli/governance.py`
- `tests/unit/governance/test_variant_ledger.py`
- `tests/unit/governance/test_study_spec.py`
- `tests/unit/governance/test_trial_ledger.py`
- `tests/unit/governance/test_promotion_gate_state_machine.py`
- `tests/unit/governance/test_cli.py`
- `tests/unit/governance/test_ids.py`
- `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py`
- `research/discovery_rigor_floor_v1/RIGOR_P02_GATE_INVENTORY.md`
- `README.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P02.md`

## Validation

- `python tools/frontier/status_doctor.py` - exited 0 with `VERDICT: WARN`; warning: no run dir with `state.json` found for `DISCOVERY_RIGOR_FLOOR_V1`.
- `git status --short --branch` - confirmed branch head remains `auto/discovery_rigor_floor_v1/rigor-p02-first-class-variantledger-family-budgets-fail-closed-entry-hook` with unstaged allowed-path changes; no staged files.
- `python -m pytest tests/unit/governance/test_promotion_gate_state_machine.py -q` - passed after the REWORK repair: `34 passed in 0.08s`.
- `python -m pytest tests/unit/governance -q` - passed after the REWORK repair and final style fixes: `550 passed in 2.69s`.
- `python -m pytest tests/unit/discovery_rigor_floor -q` - passed after the REWORK repair: `5 passed in 0.03s`.
- `python tools/verify.py --smoke` - passed after the REWORK repair, exit code 0, no stdout/stderr.
- `python tools/hooks/canary_runner.py` - passed after the REWORK repair: all Frontier canaries passed.
- `python -m ruff check src/alpha_system/governance/promotion.py src/alpha_system/governance/reviewer_verdict.py tests/unit/governance/test_promotion_gate_state_machine.py` - passed after fixing two long lines and import ordering: `All checks passed!`.
- `git diff --cached --name-only` - passed after the REWORK repair, no output; no staged set exists and no `runs/` path is staged.
- `git ls-files runs` - passed after the REWORK repair, no output.
- `git diff --name-only -- research/futures_core_alpha_pilot_v1 research/futures_substrate_scaleout_v1` - passed after the REWORK repair, no output.
- `python tools/frontier/status_doctor.py` - exited 0 with `VERDICT: WARN`; warning: no run dir with `state.json` found for `DISCOVERY_RIGOR_FLOOR_V1`.
- `git stash push -u -m rigor-p02-repair-pre-p01-rebase` - failed with exit code 1 and no stdout/stderr. `git stash create "rigor-p02-probe"` also failed with exit code 1 and no stdout/stderr.
- `git write-tree` - failed with exit code 128: `fatal: Unable to create '/home/yuke_zhang/projects/alpha_system/.git/worktrees/alpha_system-discovery_rigor_floor_v1-rigor-p02/index.lock': Read-only file system`. This confirms the executor cannot mutate git metadata to rebase/fast-forward/commit.
- `python -m pytest tests/unit/governance/test_variant_ledger.py tests/unit/governance/test_promotion_gate_state_machine.py tests/unit/governance/test_cli.py -q` - passed: `49 passed in 2.30s`.
- `python -m pytest tests/unit/discovery_rigor_floor -q` - first repair run failed: `test_promotion_gate_canary_blocks_unrecorded_variant_ledger` expected `variant_ledger_missing_records` but P01 correctly blocked first with `missing_trial_ledger_path`. The canary was repaired to supply a valid trial-ledger path.
- `python -m pytest tests/unit/discovery_rigor_floor -q` - passed after repair: `5 passed in 0.03s`.
- `python -m pytest tests/unit/governance -q` - passed: `545 passed in 2.74s`.
- `python tools/verify.py --smoke` - passed, exit code 0, no stdout.
- `python tools/hooks/canary_runner.py` - passed: all Frontier canaries passed.
- `git ls-files runs` - passed, exit code 0, no output.
- `git diff --name-only -- research/futures_core_alpha_pilot_v1 research/futures_substrate_scaleout_v1` - passed, no output.
- `git diff --cached --name-only` - passed, no output; no staged set exists and no `runs/` path is staged.

## Bypass-Canary Inventory

- Entry hook neutered / overrun allowed: `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_entry_hook_canary_blocks_variant_budget_overrun`.
- Promotion budget check removed / unrecorded ledger accepted: `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_promotion_gate_canary_blocks_unrecorded_variant_ledger`.
- Recorded budget tampered after content-addressing: `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_recorded_budget_canary_detects_study_spec_budget_tampering`.
- Amendment tampered after declaration: `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_budget_amendment_canary_detects_tampering`.
- Ledger writability ignored: `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py::test_unwritable_ledger_canary_blocks_entry_hook`.

## Caveats And Deviations

- The repair code composes with the P01 ledger-presence gate, but the local branch pointer still resolves to `ddfa9f5` (P00) while `origin/main` is `4e7c21e` (P01); merge base is `ddfa9f5`. Because the shared git index is read-only in this executor, I did not perform the actual branch fast-forward/rebase. Ralph must fast-forward/rebuild the branch from `origin/main` before staging/committing; otherwise `git diff origin/main` will continue to show P01-only files as deletions due to the stale base.
- The REWORK repair restored P01 reason-code production surfaces in this stale checkout to make the restored P01 tests executable locally. On a rebuilt `origin/main`-based branch, Ralph should verify `src/alpha_system/governance/promotion.py`, `src/alpha_system/governance/reviewer_verdict.py`, and `src/alpha_system/governance/verdict_reason_code.py` are not staged as novel P02 changes unless the rebase mechanics require carrying an identical dependency-surface restoration.
- Working-tree diff over historical Core Pilot/FUTSUB directories is empty. Diff against `origin/main` is not meaningful until the branch pointer is moved to the P01 base; it currently reports P01 verdict-annotation files as deleted because the branch base is stale, not because this repair edited those paths.
- No run-local `handoff.md`, `review.md`, or `verdict.json` was created.
- No Claude/reviewer/PR/merge/staging operation was run.

## Artifact And Boundary Confirmation

- No `runs/` path was created or staged by the executor; `git ls-files runs` printed nothing.
- No raw/canonical data, values, SQLite/DB/journal/WAL, parquet/arrow/feather, model, cache, log, provider response, broker, paper/live, or deployment artifact was created intentionally.
- No historical Core Pilot artifact, FUTSUB run state, registry, value file, or worktree was touched intentionally.
- No feature, label, reference-engine, broker, execution, live, strategy, portfolio, or PnL/value surface was changed.

## Review Request Focus

- Confirm `VariantLedgerRecord` derives from `TrialLedgerAccounting` and does not fork counting.
- Confirm entry and `EVIDENCE_READY` gates fail closed on missing/unwritable/unrecorded ledgers and overrun without valid amendment.
- Confirm family-budget and amendment validation are deterministic and tamper-detecting.
- Confirm legacy StudySpec behavior remains backward compatible when `family_budget` is absent.
- Confirm CLI addition is read-only.

## Next Step

Ralph should stage the curated files explicitly, run its handoff validation and YELLOW-lane review routing, then proceed to fresh review before any PR/merge action.
