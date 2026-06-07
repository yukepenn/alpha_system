# FUTCORE-P06 Separation Of Duties

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P06`  
Contract type: value-free separation-of-duties contract  
Recorded on: 2026-06-07

This contract records the separation invariants that bind the P06 queue and the
downstream P07-P30 phases. It references the existing Agent Factory separation
and permission primitives; it does not alter those primitives.

## Agent Factory Rule Sources

| Rule source | Contract reference | Queue meaning |
| --- | --- | --- |
| `permissions.matrix.ROSTER_ROLE_IDS` | Ten role ids only | Every queue task owner must be one of the ten Agent Factory roles. |
| `permissions.matrix.REVIEW_ROLE_IDS` | `alpha_spec_critic`, `statistical_reviewer` | Only these roles issue critique/statistical verdicts. |
| `separation.wiring.GENERATOR_APPROVAL_ASSIGNMENTS` | `alphaspec_draft`: `hypothesis_scout` -> `alpha_spec_critic` | Drafter and approver/critic must differ. |
| `separation.wiring.IMPLEMENTER_REVIEW_ASSIGNMENTS` | `feature_request`, `label_spec`, `runtime_evidence` | Implementer/runner and reviewer must differ. |
| `separation.wiring.REVIEWER_ASSIGNMENTS` | AlphaSpec and runtime evidence reviewer assignments | Reviewer assignment must be independent of implementer. |
| `separation.enforcement.PROMOTION_PERMISSION_RULE` | `promotion_permission_denied` | No Agent Factory role can receive a promotion grant. |
| `separation.enforcement.LIBRARIAN_VERDICT_RULE` | `librarian_verdict_required` | Librarian write paths require a bound reviewer verdict where verdict-gated. |
| `separation.enforcement.HUMAN_RESERVED_FLAGS_RULE` | `human_reserved_flags_preserved` | Human approval and Red-lane reserved actions remain reserved. |

## Required Invariants

| Invariant | Binding |
| --- | --- |
| Drafter != critic | `hypothesis_scout` drafts AlphaSpecs; `alpha_spec_critic` critiques them. |
| Critic != statistical reviewer | `alpha_spec_critic` critiques drafts; `statistical_reviewer` reviews runtime evidence later. |
| Reviewer != promoter | No Agent Factory role receives promotion permission; allowed research-state recording is verdict-gated and not factor/live promotion. |
| Implementer != self-reviewer | `feature_engineer`, `label_engineer`, and `diagnostics_runner` cannot review their own outputs. |
| Diagnostics Runner != promoter | `diagnostics_runner` executes/summarizes runtime tasks only and cannot approve, review, or promote. |
| Librarian cannot record without verdict | `librarian` records ledgers, memory, evidence, and allowed research-state decisions only after the required reviewer verdict references exist. |
| Human owns capital/live judgment | Capital allocation, factor promotion, paper/live trading, broker operation, order routing, production deployment, and risk/capital/live judgment remain outside Agent Factory task ownership. |

## Phase Boundary Map

| Phase group | Producing role | Independent downstream role | Forbidden collapse |
| --- | --- | --- | --- |
| `FUTCORE-P07`-`FUTCORE-P11` AlphaSpec batches | `hypothesis_scout` | `alpha_spec_critic` in `FUTCORE-P12` | A drafter cannot approve, critique, or promote its own draft. |
| `FUTCORE-P12` critique and budget audit | `alpha_spec_critic` | `data_contract_auditor`, `research_director`, `statistical_reviewer` downstream | A critic cannot implement, run, statistically review, or promote a spec it critiques. |
| `FUTCORE-P13` data-contract audit | `data_contract_auditor` | `research_director` and later auditors | No role may bypass accepted-DatasetVersion or raw/provider prohibitions. |
| `FUTCORE-P14` StudySpec pack | `research_director` | `diagnostics_runner` executes; `statistical_reviewer` reviews evidence | The runner cannot author the StudySpec binding it executes. |
| `FUTCORE-P15` feature/label additions | `feature_engineer`, `label_engineer` | `no_lookahead_auditor` | Implementers cannot review their own FeatureRequest or LabelSpec work. |
| `FUTCORE-P16`-`FUTCORE-P22` diagnostics and consolidations | `diagnostics_runner` | `no_lookahead_auditor`, `research_director`, `statistical_reviewer` | The diagnostics runner cannot review or promote its own runtime evidence. |
| `FUTCORE-P23` no-lookahead audit | `no_lookahead_auditor` | `statistical_reviewer` | Implementers and runners cannot replace the independent lookahead audit. |
| `FUTCORE-P24` variant budget audit | `research_director` | `statistical_reviewer` | Budget audit cannot expand the fixed caps or convert diagnostics into promotion. |
| `FUTCORE-P25` reviewer verdicts | `statistical_reviewer` | `librarian` records after verdict | Reviewer verdicts cannot become paper/live/factor promotion. |
| `FUTCORE-P26`-`FUTCORE-P28` ledgers, evidence, decisions | `librarian` | Reviewer verdict refs gate records | Librarian cannot create verdicts, bypass verdicts, or grant promotion. |
| `FUTCORE-P29`-`FUTCORE-P30` handoffs and closeout | `research_director` | Ralph/semantic review/done-check outside in-product queue | Closeout cannot mark paper/live/readiness or capital allocation. |

## Allowed Research States

The only research-state outcomes downstream may record are:

- `REJECT`
- `INCONCLUSIVE`
- `WATCH`
- `CANDIDATE_RESEARCH`

`WATCH` and `CANDIDATE_RESEARCH` require reviewer verdict references and remain
bounded by the `<=2` cap. They are research states only. They are not paper
approval, live approval, factor promotion, Strategy Reference validation,
production readiness, or capital allocation.

## Forbidden States And Claims

Downstream artifacts must not use forbidden promotion states or claims including:

- `VALIDATED_RESEARCH`
- `LIVE_APPROVED`
- `PAPER_APPROVED`
- `PRODUCTION_READY`
- `CAPITAL_ALLOCATED`
- `PROFITABLE`
- `TRADABLE`
- `STRATEGY_READY`
- `PORTFOLIO_READY`

The queue is therefore fail-closed: any downstream task that requires a forbidden
state, self-review, self-promotion, raw/provider access, live/paper/broker/order
behavior, or an unbounded runner is outside this queue and should be blocked.
