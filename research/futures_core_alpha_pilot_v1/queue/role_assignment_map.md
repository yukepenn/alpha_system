# FUTCORE-P06 Role Assignment Map

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P06`  
Contract type: value-free role assignment map  
Recorded on: 2026-06-07

This map binds each queue task to exactly one owning Agent Factory role and
records the forbidden-role bindings that downstream phases must preserve. It
consumes the existing Agent Factory contracts and does not change them.

## Role Roster

The owning roles are the ten roles required by
`campaign.yaml > agent_policy.required_roles` and by
`permissions.matrix.ROSTER_ROLE_IDS`.

| Role id | Display role | Queue responsibility in this pilot |
| --- | --- | --- |
| `research_director` | Research Director | Scope tasks, bind StudySpec pack ownership, audit VariantBudget, and write follow-on/closeout contracts. |
| `hypothesis_scout` | Hypothesis Scout | Draft family AlphaSpecs only. |
| `alpha_spec_critic` | AlphaSpec Critic | Independently critique/reject/request revision for AlphaSpec drafts and audit family quotas. |
| `data_contract_auditor` | Data Contract Auditor | Audit accepted DatasetVersion, FeaturePack, LabelPack, and admissibility references. |
| `feature_engineer` | Feature Engineer | Draft or validate minimal FeatureRequests only when approved gaps exist. |
| `label_engineer` | Label Engineer | Draft or validate minimal LabelSpecs only when approved gaps exist. |
| `no_lookahead_auditor` | No-Lookahead Auditor | Audit lookahead, leakage, same-bar optimism, and timestamp availability. |
| `diagnostics_runner` | Diagnostics Runner | Execute and summarize runtime diagnostics through sanctioned runtime tools only. |
| `statistical_reviewer` | Statistical Reviewer | Issue independent statistical reviewer verdicts. |
| `librarian` | Librarian | Record ledgers, evidence drafts, reference handoffs, and allowed research-state decisions after required verdict gates. |

No Agent Factory role receives a promotion grant. Human-reserved actions remain
outside this queue.

## Task Owner Bindings

| Task id | Owning role id | Assignment scope ref |
| --- | --- | --- |
| `rq.p07.cross_market_drafting` | `hypothesis_scout` | `phase:FUTCORE-P07` |
| `rq.p08.vwap_session_drafting` | `hypothesis_scout` | `phase:FUTCORE-P08` |
| `rq.p09.regime_drafting` | `hypothesis_scout` | `phase:FUTCORE-P09` |
| `rq.p10.liquidity_pa_drafting` | `hypothesis_scout` | `phase:FUTCORE-P10` |
| `rq.p11.bbo_tradability_drafting` | `hypothesis_scout` | `phase:FUTCORE-P11` |
| `rq.p12.alphaspec_critique_budget_audit` | `alpha_spec_critic` | `phase:FUTCORE-P12` |
| `rq.p13.data_contract_audit` | `data_contract_auditor` | `phase:FUTCORE-P13` |
| `rq.p14.studyspec_pack_authoring` | `research_director` | `phase:FUTCORE-P14` |
| `rq.p15.feature_request_additions` | `feature_engineer` | `phase:FUTCORE-P15` |
| `rq.p15.label_spec_additions` | `label_engineer` | `phase:FUTCORE-P15` |
| `rq.p16.cross_market_diagnostics` | `diagnostics_runner` | `phase:FUTCORE-P16` |
| `rq.p17.vwap_session_diagnostics` | `diagnostics_runner` | `phase:FUTCORE-P17` |
| `rq.p18.regime_diagnostics` | `diagnostics_runner` | `phase:FUTCORE-P18` |
| `rq.p19.liquidity_pa_diagnostics` | `diagnostics_runner` | `phase:FUTCORE-P19` |
| `rq.p20.bbo_tradability_diagnostics` | `diagnostics_runner` | `phase:FUTCORE-P20` |
| `rq.p21.cost_thin_session_consolidation` | `diagnostics_runner` | `phase:FUTCORE-P21` |
| `rq.p22.session_horizon_regime_matrix` | `diagnostics_runner` | `phase:FUTCORE-P22` |
| `rq.p23.no_lookahead_audit` | `no_lookahead_auditor` | `phase:FUTCORE-P23` |
| `rq.p24.variant_budget_audit` | `research_director` | `phase:FUTCORE-P24` |
| `rq.p25.statistical_reviewer_verdicts` | `statistical_reviewer` | `phase:FUTCORE-P25` |
| `rq.p26.ledger_recording` | `librarian` | `phase:FUTCORE-P26` |
| `rq.p27.evidence_and_reference_handoffs` | `librarian` | `phase:FUTCORE-P27` |
| `rq.p28.promotion_decision_recording` | `librarian` | `phase:FUTCORE-P28` |
| `rq.p29.failure_mode_handoffs` | `research_director` | `phase:FUTCORE-P29` |
| `rq.p30.acceptance_closeout` | `research_director` | `phase:FUTCORE-P30` |

## Forbidden-Role Bindings

| Task class | Applies to task ids | Forbidden role bindings |
| --- | --- | --- |
| AlphaSpec drafting | `rq.p07.*`, `rq.p08.*`, `rq.p09.*`, `rq.p10.*`, `rq.p11.*` | `alpha_spec_critic` cannot draft a spec it will critique; `statistical_reviewer`, `diagnostics_runner`, `librarian`, and any promoter role cannot draft. |
| AlphaSpec critique | `rq.p12.alphaspec_critique_budget_audit` | `hypothesis_scout` cannot critique or approve its own drafts; `diagnostics_runner` cannot approve specs; any promoter role cannot critique. |
| Data contract audit | `rq.p13.data_contract_audit` | `hypothesis_scout`, `alpha_spec_critic`, `feature_engineer`, `label_engineer`, `diagnostics_runner`, and `librarian` cannot bypass accepted-DatasetVersion policy or raw/provider boundaries. |
| StudySpec authoring | `rq.p14.studyspec_pack_authoring` | `hypothesis_scout` cannot approve its own draft through a StudySpec; `diagnostics_runner` cannot author the binding it later executes; `statistical_reviewer` cannot author evidence it later reviews. |
| Feature additions | `rq.p15.feature_request_additions` | `feature_engineer` cannot review its own implementation; `label_engineer` cannot substitute as feature reviewer; `statistical_reviewer` cannot implement evidence it later reviews. |
| Label additions | `rq.p15.label_spec_additions` | `label_engineer` cannot review its own implementation; `feature_engineer` cannot substitute as label reviewer; `statistical_reviewer` cannot implement evidence it later reviews. |
| Runtime diagnostics | `rq.p16.*`, `rq.p17.*`, `rq.p18.*`, `rq.p19.*`, `rq.p20.*`, `rq.p21.*`, `rq.p22.*` | `diagnostics_runner` cannot promote, issue statistical verdicts, approve AlphaSpecs, or self-review runtime evidence. |
| No-lookahead audit | `rq.p23.no_lookahead_audit` | `hypothesis_scout` cannot audit its own draft; `feature_engineer` and `label_engineer` cannot review their own additions; `diagnostics_runner` cannot replace the independent lookahead audit. |
| Variant budget audit | `rq.p24.variant_budget_audit` | `hypothesis_scout` cannot expand draft quotas; `diagnostics_runner` cannot expand grids after execution; any promoter role cannot override finite budget caps. |
| Statistical review | `rq.p25.statistical_reviewer_verdicts` | `hypothesis_scout`, `alpha_spec_critic`, `feature_engineer`, `label_engineer`, and `diagnostics_runner` cannot review their own drafting, implementation, or runtime evidence. |
| Ledger recording | `rq.p26.ledger_recording` | `librarian` cannot record verdict-gated memory or decision entries without the required reviewer verdict; `hypothesis_scout` cannot hide rejections. |
| Evidence/reference handoffs | `rq.p27.evidence_and_reference_handoffs` | `librarian` cannot produce survivor handoffs without required verdict refs; `statistical_reviewer` cannot turn a verdict into paper/live approval; any promoter role cannot treat handoff as validation. |
| Research-state decision recording | `rq.p28.promotion_decision_recording` | No Agent Factory role can hold a promotion grant; `diagnostics_runner` cannot promote; `statistical_reviewer` cannot promote its own verdict; `librarian` can only record allowed states after verdict gates. |
| Failure-mode handoffs and closeout | `rq.p29.failure_mode_handoffs`, `rq.p30.acceptance_closeout` | No role can convert closeout into FactorLibrary promotion, Strategy Reference validation, paper/live readiness, production readiness, or capital allocation. |

## Review Requirements By Task Family

| Work item class | Implementer / drafter role | Required independent review role | Required before |
| --- | --- | --- | --- |
| `alphaspec_draft` | `hypothesis_scout` | `alpha_spec_critic` | Approval into StudySpec pack and any budget audit pass. |
| `feature_request` | `feature_engineer` | `no_lookahead_auditor` | Evidence use or downstream acceptance of the addition. |
| `label_spec` | `label_engineer` | `no_lookahead_auditor` | Evidence use or downstream acceptance of the addition. |
| `runtime_evidence` | `diagnostics_runner` | `statistical_reviewer` | Survivor verdict, ledger decision, evidence draft, or research-state decision. |

## Human-Reserved Actions

The following actions are not queue tasks and are not assigned to an Agent
Factory role:

- `risk_judgment`
- `capital_allocation`
- `factor_promotion`
- `paper_trading`
- `live_trading`
- `broker_operation`
- `order_routing`
- `production_deployment`

Any downstream artifact that attempts to route those actions to an Agent Factory
role is a mismatch against the permission matrix and must stop for repair.
