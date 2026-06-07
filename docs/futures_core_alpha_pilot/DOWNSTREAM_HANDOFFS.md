# Downstream Handoffs

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P29`  
Artifact type: durable index for failure-mode downstream requirements

## Handoff Set

| Target campaign | Handoff document | Purpose |
| --- | --- | --- |
| `ALPHA_VALIDATION_GOVERNANCE_V1` | `research/futures_core_alpha_pilot_v1/downstream_handoffs/validation_governance_v1.md` | Turns pilot timing, variant, statistical-review, cost, and ledger failures into validation-governance requirements. |
| `ALPHA_FACTOR_LIBRARY_V1` | `research/futures_core_alpha_pilot_v1/downstream_handoffs/factor_library_v1.md` | Defines FactorCard / EvidenceBundle ingestion requirements and records that P28 produced zero ingestible survivors. |
| `ALPHA_STRATEGY_REFERENCE_VALIDATION_V1` | `research/futures_core_alpha_pilot_v1/downstream_handoffs/strategy_reference_validation_v1.md` | Defines Reference-truth validation admission and boundary requirements and records that P28 produced zero reference-validation candidates. |

Directory index:
`research/futures_core_alpha_pilot_v1/downstream_handoffs/README.md`.

## Evidence-To-Handoff Traceability

| Upstream evidence | Failure-mode content used | Downstream handoffs |
| --- | --- | --- |
| `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md` | TrialLedger and RejectedIdeaLedger reconciliation, rejection counts, duplicate-exposure hints, failed diagnostics, and exact record paths. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json` | Trial ids, statuses, variant ids, locked-test flags, and evidence refs. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json` | Duplicate and failed-diagnostics rejection corpus for ResearchGraveyard requirements. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/evidence/INDEX.md` and `research/futures_core_alpha_pilot_v1/evidence/survivors.json` | P27 EvidenceDraft, FactorCard draft, and ReferenceCandidateHandoff packaging for six P25-inconclusive evidence-stage survivors. | FactorLibrary; Strategy Reference; Validation Governance |
| `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/*.json` | Value-free source manifests, unresolved timing flags, limitations, and non-claim framing. | FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/evidence/factor_cards/*.json` | Draft FactorCard schema shape, lineage refs, duplicate hints, and ingestion limitations. | FactorLibrary |
| `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/*.json` | ReferenceCandidateHandoff boundary language and `reference_validation_performed=false` state. | Strategy Reference |
| `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md` and `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md` | Six independent statistical reviewer judgements, all inconclusive with zero watch/candidate budget impact. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`, `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`, and `research/futures_core_alpha_pilot_v1/promotion/decisions.json` | P28 bounded state: 4 `REJECT`, 6 `INCONCLUSIVE`, 0 `WATCH`, 0 `CANDIDATE_RESEARCH`. | FactorLibrary; Strategy Reference; Validation Governance |
| `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md` | Lookahead, label-leakage, cross-instrument availability, same-bar optimism, final-aggregate, and `15m` LabelPack flags. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md` | Declared versus observed variant budget checks, locked-test and repeated-OOS checks, and future evidence-format warnings. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md` | Nonzero cost profile coverage, zero-cost boundary, BBO fallback, proxy-only cost/capacity, thin-session, and RTH comparator gaps. | Validation Governance; FactorLibrary; Strategy Reference |
| `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` | Session/horizon/regime matrix, fragile horizon limits, ETH research-only cells, unresolved `15m`, and source rejection summary. | Validation Governance; FactorLibrary; Strategy Reference |
| `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | Risk IDs `R-006` through `R-030`, especially `R-017`, `R-021`, and `R-029`. | Validation Governance; FactorLibrary; Strategy Reference |

## Carried State

The downstream state after P28 is:

- no FactorLibrary-ingestible survivors;
- no Strategy Reference validation candidates;
- failure-mode requirements only;
- all P27 evidence packages remain not validated, not promoted, not Reference
  truth, and not tradable.

## Boundary

This index does not close the campaign, perform the acceptance audit, update
`ACTIVE_CAMPAIGN.md`, create successor campaign contracts, or mark the phase
passed. Those actions remain outside P29 executor scope.
