# FUTCORE-P06 Research Queue

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P06`  
Contract type: value-free bounded ResearchTask queue  
Recorded on: 2026-06-07

This queue seeds the finite pilot work list for `FUTCORE-P07` through
`FUTCORE-P30`. It records task ids, descriptions, owning roles, phase bindings,
and budget references only. It does not instantiate agents, start a runner,
draft AlphaSpecs, run diagnostics, read data, promote factors, or authorize
paper/live/broker/order/deployment behavior.

The queue consumes the Agent Factory contracts under
`src/alpha_system/agent_factory/**`, especially:

- `queue.models.ResearchTask`, `AgentAssignment`, `ResearchBudget`, and
  `ReviewRequirement`;
- `permissions.matrix.ROSTER_ROLE_IDS`, `REVIEW_ROLE_IDS`,
  `HUMAN_APPROVAL_ACTIONS`, and `RED_LANE_ACTIONS`;
- `separation.wiring.assemble_validated_bundle`;
- `separation.enforcement` rule ids for generator/approver,
  implementer/reviewer, reviewer assignment, promotion denial, librarian
  verdict gating, permission coverage, and human-reserved flags.

If this queue disagrees with `campaign.yaml`, the campaign file and Agent
Factory primitives win, and downstream execution should stop until the mismatch
is repaired.

## Queue Bounds

Queue id: `futcore_pilot_v1_bounded_research_queue`

The queue contains `25` finite task entries. There is no wildcard task, no
global all-family task, no auto-enqueue behavior, and no continuous research
runner.

| Bound | Source |
| --- | --- |
| `<=40` AlphaSpec drafts | `research_budget_policy.max_alpha_spec_drafts`; P05 family quotas |
| `<=10` approved AlphaSpecs | `research_budget_policy.max_approved_alpha_specs` |
| `<=5` new feature or label requests | `research_budget_policy.max_new_feature_or_label_requests` |
| `<=3` diagnostics survivors | `research_budget_policy.max_diagnostics_survivors` |
| `<=2` `WATCH` or `CANDIDATE_RESEARCH` outcomes | `research_budget_policy.max_watch_or_candidate_research` |
| Per-study variant budget required | `research_budget_policy.variant_budget_required` |
| Family budget required | `research_budget_policy.family_budget_required` |
| No scaled mining or continuous runner | `agent_policy.scaled_autonomous_mining_allowed: false`; `agent_policy.continuous_research_runner_allowed: false` |

## Family Draft Tasks

These are the only AlphaSpec drafting tasks. They are owned by
`hypothesis_scout` and remain unapproved until independent critique in
`FUTCORE-P12`.

| Task id | Description | Owning role id | Phase(s) | Finite budget reference |
| --- | --- | --- | --- | --- |
| `rq.p07.cross_market_drafting` | Draft cross-market / relative-value AlphaSpecs with lead-lag, beta-residual, rotation, and confirmation/divergence hypotheses. | `hypothesis_scout` | `FUTCORE-P07` | Family budget `0.40`; P05 quota min `12`, target/max `16`; global draft cap `<=40`. |
| `rq.p08.vwap_session_drafting` | Draft VWAP / session-auction AlphaSpecs with running-vs-final VWAP and session transition assumptions. | `hypothesis_scout` | `FUTCORE-P08` | Family budget `0.20`; P05 quota min `6`, target/max `8`; global draft cap `<=40`. |
| `rq.p09.regime_drafting` | Draft regime-gated momentum/reversion AlphaSpecs with computable activation logic. | `hypothesis_scout` | `FUTCORE-P09` | Family budget `0.15`; P05 quota min `4`, target/max `6`; global draft cap `<=40`. |
| `rq.p10.liquidity_pa_drafting` | Draft liquidity sweep, failed breakout, and objective price-action AlphaSpecs using computable rules only. | `hypothesis_scout` | `FUTCORE-P10` | Family budget `0.15`; P05 quota min `4`, target/max `6`; global draft cap `<=40`. |
| `rq.p11.bbo_tradability_drafting` | Draft BBO tradability / top-book confirmation AlphaSpecs framed as risk/confirmation evidence. | `hypothesis_scout` | `FUTCORE-P11` | Family budget `0.10`; P05 quota min `3`, target/max `4`; global draft cap `<=40`. |

## Audit And StudySpec Tasks

| Task id | Description | Owning role id | Phase(s) | Finite budget reference |
| --- | --- | --- | --- | --- |
| `rq.p12.alphaspec_critique_budget_audit` | Independently critique all drafted AlphaSpecs, reject or request revision where needed, and audit family quota adherence. | `alpha_spec_critic` | `FUTCORE-P12` | Critique universe is bounded by `<=40` drafts; approval cap `<=10`; family budget must remain `0.40/0.20/0.15/0.15/0.10`. |
| `rq.p13.data_contract_audit` | Audit accepted DatasetVersion, FeaturePack, LabelPack, registry references, admissibility, and minimal gap list for accepted specs. | `data_contract_auditor` | `FUTCORE-P13` | Audit universe is bounded by `<=10` approved AlphaSpecs and locked P03 input-pack references. |
| `rq.p14.studyspec_pack_authoring` | Author the approved StudySpec pack by reference, binding packs, sessions, horizons, cost profiles, and finite VariantBudget. | `research_director` | `FUTCORE-P14` | One StudySpec per accepted AlphaSpec; approval cap `<=10`; per-study VariantBudget required. |
| `rq.p15.feature_request_additions` | Draft or validate minimal FeatureRequest additions only when P13/P14 prove an approved gap. | `feature_engineer` | `FUTCORE-P15` | Shared feature/label request cap `<=5`; only minimal additions authorized by reviewed FeatureRequest. |
| `rq.p15.label_spec_additions` | Draft or validate minimal LabelSpec additions only when P13/P14 prove an approved gap. | `label_engineer` | `FUTCORE-P15` | Shared feature/label request cap `<=5`; true forward-looking labels remain blocked. |

## Diagnostics Tasks

Diagnostics tasks consume approved StudySpecs through the Research Runtime tool
surface. They do not reimplement diagnostics and do not promote results.

| Task id | Description | Owning role id | Phase(s) | Finite budget reference |
| --- | --- | --- | --- | --- |
| `rq.p16.cross_market_diagnostics` | Run and summarize cross-market diagnostics through runtime tools over locked packs. | `diagnostics_runner` | `FUTCORE-P16` | Bounded by approved cross-market StudySpecs; global survivor cap `<=3`; no value data committed. |
| `rq.p17.vwap_session_diagnostics` | Run and summarize VWAP / session diagnostics through runtime tools over locked packs. | `diagnostics_runner` | `FUTCORE-P17` | Bounded by approved VWAP/session StudySpecs; global survivor cap `<=3`; no value data committed. |
| `rq.p18.regime_diagnostics` | Run and summarize regime momentum/reversion diagnostics through runtime tools over locked packs. | `diagnostics_runner` | `FUTCORE-P18` | Bounded by approved regime StudySpecs; global survivor cap `<=3`; no value data committed. |
| `rq.p19.liquidity_pa_diagnostics` | Run and summarize liquidity sweep / objective PA diagnostics through runtime tools over locked packs. | `diagnostics_runner` | `FUTCORE-P19` | Bounded by approved liquidity/PA StudySpecs; global survivor cap `<=3`; no value data committed. |
| `rq.p20.bbo_tradability_diagnostics` | Run and summarize BBO tradability / top-book diagnostics through runtime tools over locked packs. | `diagnostics_runner` | `FUTCORE-P20` | Bounded by approved BBO StudySpecs; global survivor cap `<=3`; no value data committed. |

## Consolidation And Audit Tasks

| Task id | Description | Owning role id | Phase(s) | Finite budget reference |
| --- | --- | --- | --- | --- |
| `rq.p21.cost_thin_session_consolidation` | Consolidate cost stress and thin-session stress evidence by reference. | `diagnostics_runner` | `FUTCORE-P21` | Applies `zero_cost`, `base`, `stress_1`, `stress_2`, and `double_cost`; zero-cost is diagnostic-only; survivor cap `<=3`. |
| `rq.p22.session_horizon_regime_matrix` | Consolidate session, horizon, and regime matrices by reference. | `diagnostics_runner` | `FUTCORE-P22` | Matrix is bounded by approved StudySpecs and P02 session/horizon policy; survivor cap `<=3`. |
| `rq.p23.no_lookahead_audit` | Audit available timestamps, label availability, same-bar optimism, cross-instrument alignment, and leakage risk. | `no_lookahead_auditor` | `FUTCORE-P23` | Audit universe is bounded by approved studies and diagnostics summaries; no raw/provider/value reads. |
| `rq.p24.variant_budget_audit` | Audit bounded grids, declared VariantBudgets, locked-test avoidance, and repeated-selection risk. | `research_director` | `FUTCORE-P24` | Per-study VariantBudget required; no grid expansion; approved StudySpec cap `<=10`. |

## Evidence, Ledger, Promotion-State, And Closeout Tasks

| Task id | Description | Owning role id | Phase(s) | Finite budget reference |
| --- | --- | --- | --- | --- |
| `rq.p25.statistical_reviewer_verdicts` | Issue independent Statistical Reviewer verdicts for surviving ideas. | `statistical_reviewer` | `FUTCORE-P25` | Verdict universe bounded by diagnostics survivors `<=3`; reviewer independence required. |
| `rq.p26.ledger_recording` | Record TrialLedger and RejectedIdeaLedger entries with reasons and duplicate-exposure hints. | `librarian` | `FUTCORE-P26` | Records all studies/rejections from the bounded queue; Librarian writes only after reviewer verdict where required. |
| `rq.p27.evidence_and_reference_handoffs` | Assemble EvidenceDrafts, FactorCard drafts, and ReferenceCandidateHandoffs for survivors only. | `librarian` | `FUTCORE-P27` | Survivor cap `<=3`; EvidenceDraft is not Reference validation and not a candidate by itself. |
| `rq.p28.promotion_decision_recording` | Record allowed research-state decisions: `REJECT`, `INCONCLUSIVE`, `WATCH`, or `CANDIDATE_RESEARCH`. | `librarian` | `FUTCORE-P28` | `WATCH`/`CANDIDATE_RESEARCH` cap `<=2`; reviewer verdict required; no factor, paper, live, capital, or production promotion grant. |
| `rq.p29.failure_mode_handoffs` | Produce failure-mode handoffs to Validation Governance, FactorLibrary, and Strategy Reference follow-on campaigns. | `research_director` | `FUTCORE-P29` | At most three downstream handoff classes; handoffs are requirements only, not validation or promotion. |
| `rq.p30.acceptance_closeout` | Produce acceptance audit and closeout summary for the campaign. | `research_director` | `FUTCORE-P30` | One campaign closeout; final verdict limited to `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or `BLOCKED`. |

## Queue-Level Assignment Rules

- Every task above has exactly one owning Agent Factory role id.
- No task owner is outside `permissions.matrix.ROSTER_ROLE_IDS`.
- AlphaSpec drafting tasks are owned only by `hypothesis_scout`.
- Critique and statistical review tasks are owned only by roles in
  `permissions.matrix.REVIEW_ROLE_IDS`.
- Diagnostic execution tasks are owned by `diagnostics_runner` and cannot
  approve, critique, statistically review, or promote.
- Feature and label additions are split into separate tasks so neither engineer
  reviews its own work.
- Promotion grants are not assigned to any Agent Factory role. The P28 task is
  a value-free record-keeping task gated by reviewer verdicts and allowed
  research states only.
- Human-only actions remain outside the queue: capital allocation,
  factor promotion, paper trading, live trading, broker operation, order
  routing, production deployment, and risk/capital/live judgment.

## Source Cross-Reference

| Queue item | Source contract |
| --- | --- |
| Role ids and permissions | `src/alpha_system/agent_factory/permissions/matrix.py` |
| ResearchTask / AgentAssignment fields | `src/alpha_system/agent_factory/queue/models.py` |
| Separation bundle | `src/alpha_system/agent_factory/separation/wiring.py` |
| Required in-product roles | `campaign.yaml > agent_policy.required_roles` |
| Family quotas and AlphaSpec drafting protocol | `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md` |
| Scope, family budget, survivor caps | `research/futures_core_alpha_pilot_v1/scope/scope_contract.md` |
| Cost profiles and zero-cost boundary | `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md` |
| Input-pack lock by reference | `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md` |

## Non-Goals Confirmed

- No Agent Factory primitive is edited here.
- No role object, queue runner, dry-run harness, continuous runner, or worker is
  instantiated here.
- No AlphaSpec, StudySpec, diagnostic, reviewer verdict, ledger record,
  evidence draft, promotion decision, or closeout output is produced here.
- No raw/canonical data, provider response, feature value, label value,
  diagnostics value, Parquet, SQLite, DBN, Zstd, log, cache, or local DB artifact
  is committed here.
- No profitability, tradability, production, paper/live, broker/order, or
  capital-allocation claim is made here.
