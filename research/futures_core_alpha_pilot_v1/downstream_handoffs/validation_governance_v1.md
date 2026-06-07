# Validation Governance V1 Failure-Mode Handoff

Target campaign: `ALPHA_VALIDATION_GOVERNANCE_V1`  
Source campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P29`  
Artifact type: value-free requirements handoff

## Boundary

This handoff writes requirements only. It does not implement Validation
Governance V1, rerun diagnostics, assign a new PromotionDecision, perform
Reference validation, or make any paper/live, broker, production,
capital-allocation, profitability, or tradability claim.

Fast path is not Reference truth. Diagnostics are not validation. Candidate is
not capital allocation. Handoff is not promotion.

## Observed Failure Modes

| ID | Observed failure mode | Risks addressed | Pilot artifact references |
| --- | --- | --- | --- |
| `VG-FM-01` | Cross-market ideas reached runtime input resolution but failed because aligned ES/NQ/RTY evidence was unavailable at the decision surface. | `R-015`, `R-007`, `R-008` | `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_c27b447c282967db390ff10d.json`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_9ed40aaf995f1f70f5f94cdf.json`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_20d88b59ce09f47d364fd529.json`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_fa471f1ddeaa066dc4a95feb.json` |
| `VG-FM-02` | Timing readiness stayed unresolved for multiple non-rejected diagnostic ideas: derived FeaturePack bindings, running/final aggregate boundaries, and the materialized `15m` LabelPack were not proven by locked references. | `R-006`, `R-007`, `R-008`, `R-017` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md` |
| `VG-FM-03` | Cost and session evidence was proxy-only in several places: BBO fallback markers, thin-session-only breakdowns, RTH comparator gaps, and zero-fill cross-market cost reports remained limitations. | `R-009`, `R-010`, `R-011`, `R-026` | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md` |
| `VG-FM-04` | Variant budgets were respected, but several pre-grid blocked reports lacked explicit observed-count fields, leaving evidence-format warnings for future anti-overfit governance. | `R-012`, `R-021` | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json`; `research/futures_core_alpha_pilot_v1/promotion/INDEX.md` |
| `VG-FM-05` | The rejection chain is the durable product: duplicate/revise/reject outcomes and failed diagnostics are recorded, but future governance needs stronger ResearchGraveyard lookup and duplicate-exposure enforcement. | `R-013`, `R-014`, `R-021` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/*.json`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md` |
| `VG-FM-06` | Independent statistical review kept all reviewed evidence-stage survivors inconclusive; no DSR/PBO/PSR or reference-grade statistical validation exists in the pilot evidence chain. | `R-017`, `R-018`, `R-019`, `R-021` | `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md` |

## Derived Requirements

| Requirement | Validation Governance V1 requirement | Failure mode / risk | Required trace inputs |
| --- | --- | --- | --- |
| `VG-REQ-01` | Define a full statistical validation gate that requires DSR, PBO, and PSR artifacts before any future research state can move beyond evidence packaging. The gate must fail closed when reviewer verdicts remain inconclusive or when timing flags are unresolved. | `VG-FM-02`, `VG-FM-06`; `R-017`, `R-018`, `R-021` | `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/decisions.json` |
| `VG-REQ-02` | Implement purged/embargo governance for every validation split. The governance artifact must name the partition, embargo rule, label horizon, feature availability rule, and whether any locked-test surface was touched. | `VG-FM-02`, `VG-FM-04`; `R-007`, `R-008`, `R-012` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md` |
| `VG-REQ-03` | Build a locked-test contamination ledger that records each trial, variant, reviewer touch, selection decision, and OOS exposure. Repeated selection on the same held-out surface must be machine-detectable and block downstream elevation. | `VG-FM-04`, `VG-FM-06`; `R-012`, `R-017`, `R-019` | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/records/*.json` |
| `VG-REQ-04` | Require field-level timing proofs for every feature and label dependency. Unlocked derived FeaturePacks, final-session aggregate ambiguity, missing materialized LabelPacks, or label-as-input ambiguity must be recorded as blocking flags. | `VG-FM-02`; `R-006`, `R-007`, `R-008` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`; `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` |
| `VG-REQ-05` | Add a cross-instrument availability gate for relative-value studies. The gate must verify aligned availability across required symbols at the primary decision timestamp before signal, cost, or statistical validation can continue. | `VG-FM-01`; `R-015`, `R-007` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**`; `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_c27b447c282967db390ff10d.json` |
| `VG-REQ-06` | Distinguish proxy cost/capacity evidence from validation evidence. A validation gate must require nonzero cost-profile coverage, BBO provenance, RTH comparator coverage, and explicit thin-session limitations before any cost/capacity conclusion can be used. | `VG-FM-03`; `R-009`, `R-010`, `R-011`, `R-026` | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` |
| `VG-REQ-07` | Harden ResearchGraveyard behavior so duplicate-exposure groups, rejection reason categories, source decisions, and linked trial ids are queryable before new research starts. A duplicate or near-duplicate without explicit override should block re-entry. | `VG-FM-05`; `R-013`, `R-014` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md` |
| `VG-REQ-08` | Require every validation-governance output to emit a machine-readable failure-mode map: requirement id, risk id, blocking artifact path, reviewer status, and unresolved flags. This prevents future closeout handoffs from being reconstructed from memory. | `VG-FM-01` through `VG-FM-06`; `R-021` | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`; `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md` |

## Non-Claims

Validation Governance V1 should treat the pilot as a failure-mode corpus, not as
validated research. The downstream campaign must not infer that any pilot
diagnostic, EvidenceDraft, FactorCard draft, ReferenceCandidateHandoff, reviewer
verdict, or PromotionDecision authorizes strategy validation, paper/live
readiness, broker operation, deployment, capital allocation, profitability, or
tradability.
