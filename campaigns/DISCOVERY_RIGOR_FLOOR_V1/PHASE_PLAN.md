# DISCOVERY_RIGOR_FLOOR_V1 — Phase Plan

DAG: P00 → P01 → P02 → P03 → {P04, P05} (parallel build, serial merge) and
P01 → P06 (parallel-eligible) → P07 (must-run-alone closeout, depends on
P04+P05+P06). P01/P02/P03 serialize via conflicts_with (all touch
promotion_gate.py). Lanes: P00 GREEN; rest YELLOW.

### RIGOR-P00 — Bootstrap + Boundary State Record (GREEN)
Bundle + evidence skeleton + truthful FUTSUB boundary-gate record. No code.

### RIGOR-P01 — Reason-Code Taxonomy + Ledger-Presence Gates + Annotations
VerdictReasonCode (8 compass codes); reason_code REQUIRED when INCONCLUSIVE
across ReviewerVerdict/EvidenceBundle/PromotionDecision; fail-closed
trial-ledger presence/writability gate at EVIDENCE_READY; 6 ADDITIVE Core
Pilot verdict annotations (originals untouched — forbidden paths enforce).

### RIGOR-P02 — First-Class VariantLedger + Family Budgets
VariantLedgerRecord platform-cumulative beside TrialLedger (extend
TrialLedgerAccounting, never fork); family_budget + FamilyBudgetCheck
roll-up; fail-closed entry hook at study execution; promotion-gate budget
check; bypass canaries.

### RIGOR-P03 — Sealed Holdout + Access Log + Contamination Gating
SealedHoldoutWindow (one ACTIVE window) + append-only HoldoutAccessLog wired
into label_leakage_guard/study execution; contamination or BREACH blocks
promotion, no waiver path; initial kill-shot window declared.

### RIGOR-P04 — Executable RANDOM_TARGET + Planted-Fake-Alpha Canary
4/4 catalogued negative controls executable; end-to-end synthetic study with
lookahead-contaminated labels must be REJECTED by the full pipeline
(CI-runnable); evidence gate requires all controls PASS; canary_runner
registration with expect_block.

### RIGOR-P05 — Surrogate-FDR Calibration
SurrogateStudyRun schema + runner (label-shuffled full-pipeline, isolated
namespace, seeded); calibration CLI + value-free report; declared zero-pass
threshold (any shuffled pass = measured leakage = LEAKAGE_BLOCKED, diagnose
before kill-shot). Kill-shot AND future-ML hard precondition.

### RIGOR-P06 — Evidence-Accrual Requeue Scan
RequeuedVerdictRecord + planning-prior power estimator (heuristic, never a
gate) + deterministic `requeue-scan` CLI/just recipe over
UNDERPOWERED-annotated verdicts. No daemon.

### RIGOR-P07 — Integration Audit + Kill-Shot Readiness + Resume Handoff
Synthetic study through the FULL gated path (every gate engages, each cites
its bypass canary); KILL_SHOT_READINESS.md checklist; Track-B
pre-registration TEMPLATE; FUTSUB_KILL_SHOT_RESUME.md coordinator steps;
compass Stage B status note; lessons.

## After this campaign (coordinator)
Repoint to FUTSUB → complete Track-B registration → real-data surrogate
calibration if pending → clear boundary STOP → resume run → P28 kill-shot.
