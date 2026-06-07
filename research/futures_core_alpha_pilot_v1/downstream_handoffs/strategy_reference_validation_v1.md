# Strategy Reference Validation V1 Failure-Mode Handoff

Target campaign: `ALPHA_STRATEGY_REFERENCE_VALIDATION_V1`  
Source campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P29`  
Artifact type: value-free requirements handoff

## Boundary

This handoff writes Strategy Reference validation requirements only. It does not
perform Reference validation, run a strategy, paper trade, live trade, contact a
broker, deploy code, allocate capital, or make profitability or tradability
claims.

Fast path is not Reference truth. Diagnostics are not validation. Candidate is
not capital allocation. Handoff is not promotion.

## Candidate State From P28

P27 produced ReferenceCandidateHandoff packages for the six P25
`INCONCLUSIVE` evidence-stage survivors:

- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_69c22ec5847395ac8e81b5b6.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_aff70fcbc4b7ff226fcc8149.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_267cc052e37668339c38d179.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_27bf1262b0bd23d27191cc86.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_02c400a561891171a33c0c66.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_9f6f741192a4b534f06e51c0.json`

P28 produced zero `WATCH` or `CANDIDATE_RESEARCH` outcomes:

- `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`
- `research/futures_core_alpha_pilot_v1/promotion/decisions.json`

Therefore this pilot hands off no Reference-validation candidates. The P27
ReferenceCandidateHandoff files are examples of handoff packaging and
failure-mode evidence; they are not validation inputs that may be run as
strategies without a later campaign explicitly admitting them.

## Observed Failure Modes

| ID | Observed failure mode | Risks addressed | Pilot artifact references |
| --- | --- | --- | --- |
| `SR-FM-01` | ReferenceCandidateHandoff artifacts can exist while the PromotionDecision layer still has no watch/candidate survivors. Handoff packaging is not Reference truth. | `R-017`, `R-018`, `R-030` | `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_267cc052e37668339c38d179.json`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md` |
| `SR-FM-02` | Fast-path diagnostics left temporal flags unresolved: feature timing, label timing, final-aggregate boundaries, and cross-instrument availability require reference-grade proof before any strategy validation. | `R-006`, `R-007`, `R-008`, `R-015`, `R-017` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_c27b447c282967db390ff10d.json` |
| `SR-FM-03` | Cost and session evidence carried proxy-only BBO/capacity markers, fragile horizon boundaries, thin-session research-only markers, and RTH comparator gaps. | `R-009`, `R-010`, `R-011`, `R-026`, `R-017` | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md` |
| `SR-FM-04` | The statistical reviewer record stayed inconclusive across all reviewed survivors and did not run full Reference validation statistics. | `R-017`, `R-018`, `R-019` | `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md` |
| `SR-FM-05` | Variant budgets and locked-test checks were clean for the pilot evidence surface, but they were audits of fast-path diagnostics, not proof that a Reference engine can reproduce or validate a strategy. | `R-012`, `R-017` | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json` |
| `SR-FM-06` | Rejected ideas and duplicate-exposure hints must follow any reference candidate so Strategy Reference does not retest known dead ends silently. | `R-013`, `R-014`, `R-017` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`; `research/futures_core_alpha_pilot_v1/evidence/survivors.json` |

## Derived Requirements

| Requirement | Strategy Reference Validation V1 requirement | Failure mode / risk | Required trace inputs |
| --- | --- | --- | --- |
| `SR-REQ-01` | Candidate admission must be keyed to a PromotionDecision state, not merely to a ReferenceCandidateHandoff file. Because P28 has zero watch/candidate states, this pilot admits no candidate to Strategy Reference validation. | `SR-FM-01`, `SR-FM-04`; `R-017`, `R-018` | `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`; `research/futures_core_alpha_pilot_v1/promotion/decisions.json`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md` |
| `SR-REQ-02` | Reference validation must rebuild the candidate through a reference pipeline from locked input packs and StudySpecs. It must not treat P16-P22 runtime diagnostic status, P27 handoff status, or P28 bounded state as reference-truth output. | `SR-FM-01`, `SR-FM-05`; `R-017` | `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/reference_candidate_handoff_sspec_267cc052e37668339c38d179.json`; `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`; `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md` |
| `SR-REQ-03` | Before any reference run, require temporal proof: field-level feature availability, label availability, no same-bar optimism, no final-session aggregate misuse, purged/embargo split policy, and no locked-test contamination. | `SR-FM-02`, `SR-FM-05`; `R-006`, `R-007`, `R-008`, `R-012` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` |
| `SR-REQ-04` | Cross-market candidates must pass an aligned-availability preflight across every required instrument at the primary decision timestamp before reference statistics or cost validation run. | `SR-FM-02`; `R-015`, `R-017` | `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/records/rej_c27b447c282967db390ff10d.json`; `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md` |
| `SR-REQ-05` | Reference validation must include full multiple-testing and overfit governance, including DSR, PBO, PSR, declared variant axes, observed variants, and repeated-OOS checks. Inconclusive P25 verdicts must not be upgraded by handoff language. | `SR-FM-04`, `SR-FM-05`; `R-012`, `R-017`, `R-019` | `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md` |
| `SR-REQ-06` | Reference cost/session validation must require nonzero cost profiles, BBO provenance, slippage/capacity model versioning, RTH comparator evidence, and explicit thin-session limitations. Proxy-only pilot evidence cannot satisfy this requirement. | `SR-FM-03`; `R-009`, `R-010`, `R-011`, `R-026` | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` |
| `SR-REQ-07` | Every reference-candidate package must carry RejectedIdea and duplicate-exposure context. Strategy Reference must consult ResearchGraveyard before running or admitting near-duplicate variants. | `SR-FM-06`; `R-013`, `R-014`, `R-017` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`; `research/futures_core_alpha_pilot_v1/evidence/survivors.json` |
| `SR-REQ-08` | Reference-validation outputs must preserve hard boundaries: reference research is not paper/live approval, not broker authorization, not deployment, and not capital allocation. Any later Red-lane or human-capital gate must be separate and explicit. | `SR-FM-01`, `SR-FM-03`; `R-018`, `R-030` | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md` |

## No-Candidate Reference-Validation Gaps

Because P28 produced zero watch/candidate states, Strategy Reference Validation
V1 should not schedule any pilot candidate for reference validation. The gaps to
carry forward are:

- no P28 state eligible for candidate admission;
- P27 handoff packages explicitly state that Reference validation was not
  performed;
- P23 timing and label flags remain unresolved;
- cross-market availability failures remain hard rejections;
- P21/P22 cost, BBO, RTH, thin-session, and fragile-horizon limitations remain
  reference blockers;
- P25 verdicts remain inconclusive;
- P24 anti-overfit audit is necessary context but not Reference validation.

## Non-Claims

No Strategy Reference candidate is validated by this pilot. No handoff package,
diagnostic report, reviewer verdict, evidence draft, FactorCard draft, or
PromotionDecision authorizes strategy use, paper/live trading, broker
operations, deployment, capital allocation, profitability, or tradability.
