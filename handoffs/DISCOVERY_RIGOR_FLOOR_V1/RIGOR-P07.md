# RIGOR-P07 Handoff

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
Phase: `RIGOR-P07` - Integration Audit + Kill-Shot Readiness Gate + FUTSUB Resume Handoff
Lane: YELLOW
Executor: Codex

## Scope Completed

- Added the full-gated-path integration audit test:
  `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py`.
  It drives one synthetic study through the real VariantLedger/family-budget
  hook, tmp trial ledger, tmp sealed holdout and access log, 4/4 negative
  controls plus planted-fake-alpha outcome, reason-code validation,
  `DIAGNOSTICS_RUN -> EVIDENCE_READY`, and `REVIEWED -> CANDIDATE`.
- Added the value-free gate audit table:
  `research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`.
- Added the fail-closed kill-shot readiness checklist:
  `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md`.
- Added the Track-B pre-registration template:
  `docs/discovery_rigor_floor/TRACK_B_PREREGISTRATION_TEMPLATE.md`.
- Added the coordinator-only FUTSUB resume handoff:
  `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md`.
- Added the compact Stage B status note to `docs/OPERATING_COMPASS_V4.md`.
- Updated the README snapshot for P07 closeout state and safety boundaries.

No production governance code, CLI, justfile, canary runner, eval canary
fixtures, FUTSUB state, historical Core Pilot evidence, or project-skill files
were changed by this executor.

## Curated File List For Ralph

Executor staged nothing. Ralph should explicitly stage only:

- `README.md`
- `docs/OPERATING_COMPASS_V4.md`
- `docs/discovery_rigor_floor/TRACK_B_PREREGISTRATION_TEMPLATE.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md`
- `handoffs/DISCOVERY_RIGOR_FLOOR_V1/RIGOR-P07.md`
- `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md`
- `research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`
- `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py`

## Gate Audit Summary

Detailed table:
`research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`.

Rows covered:

1. Variant/family budget entry hook: engaged and blocked with
   `variant_budget_overrun`.
2. Trial-ledger presence/writability gate: engaged and blocked with
   `missing_trial_ledger` / `unwritable_trial_ledger`.
3. Holdout access-log and contamination gate: engaged and blocked with
   `unauthorized_locked_test_holdout_access` /
   `locked_test_contamination_blocks_evidence_ready`.
4. Negative-control floor: 4/4 controls plus planted fake-alpha outcome
   engaged; missing control blocked with
   `missing_required_negative_control_result`.
5. Reason-coded verdict: `INCONCLUSIVE + UNDERPOWERED` accepted; missing
   reason code blocked with `missing_reason_code_for_inconclusive`.
6. Promotion gate composition: evidence-ready and candidate gates engaged;
   unrecorded VariantLedger blocked with `variant_ledger_missing_records`.

## Readiness Roll-Up

Checklist:
`research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md`.

- `MET`: 9
- `PENDING-coordinator`: 4
- Kill-shot fire condition: every row must be `MET`.

Pending coordinator items and closing steps:

1. Surrogate calibration v4.4 section 7.2 statistical floor:
   `FUTSUB_KILL_SHOT_RESUME.md` step 5.
2. Track-B mandatory minimum actual registration:
   `FUTSUB_KILL_SHOT_RESUME.md` step 4.
3. VariantLedger reconciliation audit over six rerun candidates:
   `FUTSUB_KILL_SHOT_RESUME.md` step 6.
4. Live substrate-invariant audit:
   `FUTSUB_KILL_SHOT_RESUME.md` step 7.

The P05 synthetic `K=2` calibration is cited as machinery evidence only and is
not used to satisfy the real-data section 7.2 floor.

## Validation Results

| Command | Result | Notes |
|---|---:|---|
| `git status --short` | NOT RUN | Executor prompt explicitly forbids `git status`. |
| `python -m ruff check tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py` | PASS | `All checks passed!` |
| `python -m pytest tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py -q` | PASS | `1 passed in 0.06s`. |
| `python -m pytest tests/unit/governance tests/unit/discovery_rigor_floor -q` | PASS | `662 passed in 4.02s`. |
| `python tools/hooks/canary_runner.py` | PASS | 25 `PASS` lines; `All Frontier canaries passed.` |
| `test -f research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md && test -f handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md && test -f docs/discovery_rigor_floor/TRACK_B_PREREGISTRATION_TEMPLATE.md` | PASS | Exit 0. |
| `python tools/verify.py --smoke` | PASS | Exit 0, no stdout/stderr. |
| `python -m pytest tests/unit/runtime/cost/test_real_fee_schedule.py tests/unit/runtime/cost/test_cost_model_version.py -q` | PASS | `13 passed in 0.06s`; supports readiness row 13. |
| `git diff --quiet -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers` | NOT RUN | Executor prompt explicitly forbids `git diff`. |
| `git ls-files -m -o --exclude-standard -- research/futures_core_alpha_pilot_v1/study_specs research/futures_core_alpha_pilot_v1/reviewer_verdicts research/futures_core_alpha_pilot_v1/evidence research/futures_core_alpha_pilot_v1/ledgers research/futures_substrate_scaleout_v1` | PASS | Exit 0, no output; no tracked or untracked changes under historical evidence or FUTSUB research dirs. |
| `git ls-files runs` | PASS | Exit 0, no output. |
| `git ls-files '**/*.parquet' '**/*.sqlite' '**/*.db' '**/*.arrow' '**/*.feather' '**/*.dbn' '**/*.zst' '**/*.log'` | PASS | Exit 0, no output. |
| `git ls-files -m -o --exclude-standard` | PASS | Output contained only the eight curated files listed above, including this handoff. |

## Isolation And Boundary Confirmations

- All synthetic-study writes from the integration audit stayed in pytest tmp
  namespaces: trial ledger JSON, VariantLedger JSONL, sealed-holdout JSON,
  HoldoutAccessLog JSONL, and planted-fake-alpha workspace output.
- FUTSUB run state, boundary STOP, RUN.lock, registries, values, and worktrees
  were not touched.
- `ACTIVE_CAMPAIGN.md` was not edited.
- `tools/hooks/canary_runner.py`, `src/alpha_system/cli/governance.py`,
  `justfile`, and `evals/canaries/**` were not edited.
- Historical Core Pilot evidence dirs and `research/futures_substrate_scaleout_v1/**`
  were not edited; the allowed `git ls-files -m -o --exclude-standard -- ...`
  audit printed no output.
- `git ls-files runs` and heavy tracked-artifact globs printed no output.
- No raw/canonical data, feature/label values, SQLite/DB/journal/WAL,
  parquet/arrow/feather, logs, caches, provider responses, model binaries,
  secrets, or local environment files were created for commit.
- No live trading, paper trading, broker operation, order routing, deployment,
  PR creation, merge, review call, `review.md`, or `verdict.json` was created
  by this executor.
- No `git add`, `git commit`, `git push`, `git status`, or `git diff` was run.

## Project-Skill Lessons

No durable project-skill lesson was added. This phase produced closeout
artifacts and a composition audit, but no new campaign-level operating pattern
was validated beyond lessons already recorded for coordinator-owned git and
pending real-data calibration boundaries.
