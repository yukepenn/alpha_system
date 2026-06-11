# DISCOVERY_RIGOR_FLOOR_V1 — Acceptance

DONE when every line is deterministically checkable and true:

1. **All eight phases merged** (RIGOR-P00…P07), YELLOW phases with fresh
   Claude review artifacts under `reviews/DISCOVERY_RIGOR_FLOOR_V1/<phase>/`
   whose verdicts cite deterministic evidence (test output, canary runs,
   audit tables) — never prose alone.
2. **Fail-closed proven, not asserted**: every new gate (ledger presence,
   variant/family budget, holdout access/contamination, negative-control
   completeness, reason_code validation) has a committed bypass-canary test
   that FAILS when the gate is neutered. `python tools/hooks/canary_runner.py`
   green including the new canaries.
3. **Canary floor closed**: all 4 catalogued negative-control types
   executable; the end-to-end planted-fake-alpha canary proves a
   lookahead-contaminated study is REJECTED by the full pipeline, CI-runnable
   on synthetic fixtures.
4. **Surrogate-FDR measured**: calibration machinery merged; committed
   value-free report with run counts, gate pass-rate, and the declared
   zero-pass threshold; synthetic calibration green in CI; real-data
   calibration recorded as a runbook step if not executed in-campaign.
5. **reason_code live**: enum matches the 8 compass codes; INCONCLUSIVE
   without reason_code is a validation error everywhere verdicts are
   recorded; the 6 Core Pilot verdicts have additive annotations and
   `git diff` over `research/futures_core_alpha_pilot_v1/{reviewer_verdicts,
   study_specs,evidence,ledgers}` across the whole campaign is EMPTY.
6. **VariantLedger keystone**: platform-cumulative, family budgets enforced
   at study entry AND promotion; existing TrialLedger callers unchanged.
7. **Sealed holdout regime**: exactly one ACTIVE declared window; append-only
   access log wired; contamination/BREACH blocks promotion with no waiver
   path.
8. **Kill-shot readiness artifacts exist**: KILL_SHOT_READINESS.md (each item
   citing deterministic evidence), TRACK_B_PREREGISTRATION_TEMPLATE.md, and
   the executable FUTSUB_KILL_SHOT_RESUME.md handoff.
9. **Artifact policy clean**: no runs/, values, SQLite, or heavy artifacts
   committed; explicit staging only; `git ls-files runs` empty.

Failure handling: any open-by-default gate, any historical-evidence
mutation, or any impossible validation is BLOCKED — never a weakened gate,
never a silent TODO.
