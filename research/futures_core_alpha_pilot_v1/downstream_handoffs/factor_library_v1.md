# FactorLibrary V1 Failure-Mode Handoff

Target campaign: `ALPHA_FACTOR_LIBRARY_V1`  
Source campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P29`  
Artifact type: value-free requirements handoff

## Boundary

This handoff writes FactorLibrary ingestion requirements only. It does not
create FactorLibrary V1, import any factor, promote any idea, rerun diagnostics,
or make paper/live, broker, production, capital-allocation, profitability, or
tradability claims.

Fast path is not Reference truth. Diagnostics are not validation. Candidate is
not capital allocation. Handoff is not promotion.

## Survivor State From P28

P27 produced six EvidenceDraft, FactorCard draft, and
ReferenceCandidateHandoff packages for StudySpecs with P25 `INCONCLUSIVE`
judgements:

- `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`
- `research/futures_core_alpha_pilot_v1/evidence/survivors.json`
- `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/*.json`
- `research/futures_core_alpha_pilot_v1/evidence/factor_cards/*.json`
- `research/futures_core_alpha_pilot_v1/evidence/reference_handoffs/*.json`

P28 then assigned `0` `WATCH` and `0` `CANDIDATE_RESEARCH` outcomes:

- `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`
- `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`
- `research/futures_core_alpha_pilot_v1/promotion/decisions.json`

Therefore there are no P28 survivors for FactorLibrary ingestion. The P27
FactorCard files are draft evidence inputs only and must not be ingested as
FactorLibrary entries by this pilot.

## Observed Failure Modes

| ID | Observed failure mode | Risks addressed | Pilot artifact references |
| --- | --- | --- | --- |
| `FL-FM-01` | EvidenceDraft and FactorCard draft packages can exist even when the later PromotionDecision set has zero ingestible survivor states. | `R-017`, `R-029` | `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`; `research/futures_core_alpha_pilot_v1/promotion/decisions.json` |
| `FL-FM-02` | The P27 evidence packages carry unresolved timing and label flags from P23, especially unlocked derived FeaturePack bindings and missing materialized `15m` LabelPack coverage. | `R-006`, `R-007`, `R-008`, `R-029` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_69c22ec5847395ac8e81b5b6.json`; `research/futures_core_alpha_pilot_v1/evidence/evidence_drafts/evidence_draft_sspec_9f6f741192a4b534f06e51c0.json` |
| `FL-FM-03` | Cost, capacity, session, and BBO evidence remained proxy-only or incomplete in ways that a FactorCard schema must preserve as limitations. | `R-009`, `R-010`, `R-011`, `R-026`, `R-029` | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`; `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_9f6f741192a4b534f06e51c0.json` |
| `FL-FM-04` | Duplicate-exposure information is split between exact rejected-idea links and broader hints; some P27 survivor packages have no exact rejected-idea link. | `R-013`, `R-014`, `R-029` | `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/evidence/survivors.json` |
| `FL-FM-05` | Variant-budget compliance alone is insufficient for ingestion readiness; future FactorCards need explicit observed-count, no locked-test touch, and no post-diagnostic expansion fields. | `R-012`, `R-029` | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json` |
| `FL-FM-06` | P25 independent review did not support watch/candidate states, and P28 preserved that boundary. FactorLibrary must be keyed to the promotion decision, not to P22 diagnostic-survivor wording. | `R-017`, `R-018`, `R-029` | `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md`; `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/FUTCORE-P25.md`; `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md` |

## Derived Requirements

| Requirement | FactorLibrary V1 requirement | Failure mode / risk | Required trace inputs |
| --- | --- | --- | --- |
| `FL-REQ-01` | Ingestion must be keyed to a bounded PromotionDecision record. Only future records explicitly assigned `WATCH` or `CANDIDATE_RESEARCH` may enter an ingestion queue; this pilot contributes no ingestible FactorCard entries because P28 has zero such states. | `FL-FM-01`, `FL-FM-06`; `R-017`, `R-029` | `research/futures_core_alpha_pilot_v1/promotion/PROMOTION_DECISIONS.md`; `research/futures_core_alpha_pilot_v1/promotion/decisions.json` |
| `FL-REQ-02` | A FactorCard ingestion payload must carry a complete source manifest: AlphaSpec, StudySpec, input pack, FeaturePack and LabelPack versions, diagnostics refs, cost refs, matrix refs, TrialLedger refs, RejectedIdea refs, reviewer verdict, and PromotionDecision ref. | `FL-FM-01`, `FL-FM-04`; `R-013`, `R-014`, `R-029` | `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_9f6f741192a4b534f06e51c0.json`; `research/futures_core_alpha_pilot_v1/ledgers/INDEX.md` |
| `FL-REQ-03` | Ingestion must fail closed when temporal readiness flags remain unresolved. Required fields include feature `available_ts` proof, label `label_available_ts` proof, final-aggregate boundary proof, same-bar optimism status, and cross-instrument availability status. | `FL-FM-02`; `R-006`, `R-007`, `R-008`, `R-015`, `R-029` | `research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`; `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`; `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` |
| `FL-REQ-04` | FactorCard cost and capacity sections must preserve proxy/fallback state instead of converting it into readiness. Required fields include nonzero cost-profile coverage, zero-cost diagnostic-only flag, BBO fallback flag, thin-session-only flag, and RTH comparator status. | `FL-FM-03`; `R-009`, `R-010`, `R-011`, `R-026`, `R-029` | `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`; `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` |
| `FL-REQ-05` | FactorLibrary must require anti-overfit metadata: declared variant budget, observed variant count, variant axes, post-diagnostic expansion flag, locked-test contamination flag, and OOS touch status. | `FL-FM-05`; `R-012`, `R-029` | `research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`; `research/futures_core_alpha_pilot_v1/ledgers/trial_ledger/trial_ledger.json` |
| `FL-REQ-06` | Duplicate-exposure metadata must be first-class. Ingestion payloads must distinguish exact linked RejectedIdea records from hint-only groups and must require a ResearchGraveyard lookup result before accepting a factor candidate. | `FL-FM-04`; `R-013`, `R-014`, `R-029` | `research/futures_core_alpha_pilot_v1/ledgers/rejected_idea_ledger/rejected_idea_ledger.json`; `research/futures_core_alpha_pilot_v1/evidence/survivors.json` |
| `FL-REQ-07` | When a campaign has zero ingestible survivors, FactorLibrary should store an ingestion-gap report rather than draft factor entries. The report must list why each EvidenceDraft failed ingestion readiness by reference. | `FL-FM-01` through `FL-FM-06`; `R-029` | `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `research/futures_core_alpha_pilot_v1/promotion/INDEX.md`; `research/futures_core_alpha_pilot_v1/reviewer_verdicts/INDEX.md` |
| `FL-REQ-08` | Non-claim framing must be preserved in any future import: draft evidence is not validated, not promoted, not Reference truth, not tradable, and not capital allocation. | `FL-FM-01`, `FL-FM-06`; `R-017`, `R-018`, `R-030` | `research/futures_core_alpha_pilot_v1/evidence/factor_cards/factor_card_sspec_9f6f741192a4b534f06e51c0.json`; `research/futures_core_alpha_pilot_v1/evidence/INDEX.md`; `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md` |

## No-Survivor Ingestion-Readiness Gaps

Because P28 produced zero `WATCH` / `CANDIDATE_RESEARCH` outcomes, FactorLibrary
V1 should treat the pilot output as a gap corpus. The specific readiness gaps to
model are:

- no PromotionDecision state eligible for ingestion;
- unresolved FeaturePack and LabelPack timing proofs carried by P23;
- all P25 survivor verdicts remain `INCONCLUSIVE`;
- cost/capacity evidence is proxy-only or incomplete in the carried limitations;
- duplicate-exposure evidence is partly exact-link and partly hint-only;
- some diagnostics surfaces need stricter observed-variant-count metadata;
- P27 FactorCard drafts are not finalized EvidenceBundles and are not validated
  FactorLibrary entries.

## Non-Claims

No FactorLibrary entry is produced by this pilot. No P27 EvidenceDraft,
FactorCard draft, ReferenceCandidateHandoff, P25 reviewer verdict, or P28
PromotionDecision authorizes production use, paper/live readiness, broker
activity, capital allocation, profitability, or tradability.
