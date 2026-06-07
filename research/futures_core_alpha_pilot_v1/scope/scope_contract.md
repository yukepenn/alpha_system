# FUTCORE-P02 Scope Contract

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P02`  
Contract type: value-free bounded pilot scope  
Recorded on: 2026-06-07

This contract pins the pilot universe, session views, horizon policy, alpha
family budget, finite research budgets, and guardrails before AlphaSpec drafting
begins. It records constraints only. It does not draft AlphaSpecs, lock input
packs, define cost model numbers, run diagnostics, promote factors, validate a
strategy, or authorize paper/live/broker/order/deployment behavior.

`campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml` is the source of
truth. If this contract disagrees with that campaign file, the campaign file wins
and downstream execution should stop until the disagreement is repaired.

## Universe

In-scope universe:

- `ES`
- `NQ`
- `RTY`

Deferred universe:

- `MES`
- `MNQ`
- `M2K`
- `rates`
- `FX`
- `commodities`
- `vol products`
- `options`
- `equities`
- `L1 eventstream`
- `L2/L3`

The pilot must not expand the universe. Inputs remain registry-resolved and
provider/file access remains outside this phase.

## Session Views

Required session views:

- `full_session`
- `RTH_only`
- `ETH_only`
- `ETH_evening`
- `ETH_overnight`
- `pre_RTH`
- `RTH`
- `post_RTH`
- `RTH_with_ETH_context`

Downstream diagnostics must produce the session x horizon matrix required by the
campaign. `ETH`, `pre_RTH`, and `post_RTH` are thin-session views and carry
stricter later stress requirements. ETH evidence is research-in-scope, but it is
not trading-approved.

Session-context guardrails:

- final session high/low/VWAP cannot be used intraday before session completion;
- `RTH_with_ETH_context` may use completed ETH context;
- running session high-so-far may be used only with correct `available_ts`;
- no position crosses the exchange daily maintenance / trade-date break.

## Horizon Policy

| Horizon set | Policy |
| --- | --- |
| `1m` | Sampling only. |
| `1m`, `3m` | Execution-fragile diagnostics only; downstream phases must apply stricter spread, liquidity, and cost gates, and these horizons must not be presented as robust. |
| `5m`, `10m`, `15m`, `30m` | Primary pilot zone and primary label horizons. |
| `60m`, `120m`, `240m`, `session_close` | Valid extended intraday horizons with stronger sample, overlap, regime, and stability checks. |

Hard boundary: no position may cross the exchange daily maintenance /
trade-date break. Flat-before-maintenance is required.

## Alpha Family Budget

The family budget is finite and sums to `1.00`.

| Family | Budget |
| --- | ---: |
| Cross-market / relative-value | `0.40` |
| VWAP / session-auction | `0.20` |
| Regime momentum / reversion | `0.15` |
| Liquidity-sweep / failed-breakout | `0.15` |
| BBO-tradability / confirmation | `0.10` |
| **Total** | `1.00` |

Volume / activity / effort-vs-result is an overlay only. It has no standalone
family budget, may use only existing primitives, and must not introduce a new
volume feature zoo.

## Research Budgets

| Budget item | Cap or requirement |
| --- | --- |
| AlphaSpec drafts | `<=40` |
| Approved AlphaSpecs | `<=10` |
| New feature or label requests | `<=5` |
| Diagnostics survivors | `<=3` |
| `WATCH` or `CANDIDATE_RESEARCH` outcomes | `<=2` |
| Per-study variant budget | Required downstream |

Ideas may enter the pilot only through the bounded AlphaSpec and queue protocol
owned by later phases. This phase introduces no standalone idea-mining loop, no
continuous runner, and no additional budget category.

## Bounded-Pilot Guardrails

The following guardrails are pinned for downstream citation:

| Risk | Guardrail pinned in this contract |
| --- | --- |
| `R-001` scaled mining | The pilot is bounded, finite, and not a continuous or scaled mining loop. |
| `R-010` fragile horizons | `1m` and `3m` are diagnostics-only fragile horizons with stricter later gates. |
| `R-011` thin-session overclaim | ETH and other thin-session views are research-in-scope with stricter stress; ETH is not trading-approved. |
| `R-012` variant explosion | Every downstream study must carry a finite VariantBudget. |
| `R-022` underpowered pilot | Downstream drafting must remain large enough to exercise family coverage within the fixed caps. |
| `R-023` overexpanded pilot | Draft, approval, survivor, and watch/candidate caps must not be exceeded. |
| `R-025` family budget ignored | The 0.40 / 0.20 / 0.15 / 0.15 / 0.10 family split is required. |

This contract also preserves the campaign-wide safety boundary: no broker, live,
paper, order, account, deployment, production, capital-allocation, profitability,
or strategy-readiness claim is authorized.

## Downstream Binding

Downstream phases must cite this contract when they set quotas, bind StudySpecs,
run diagnostics, consolidate matrices, audit budgets, and decide research states:

- `FUTCORE-P05` / `FUTCORE-P07` through `FUTCORE-P11`: family quotas and
  AlphaSpec drafting limits;
- `FUTCORE-P12`: family budget and AlphaSpec approval audit;
- `FUTCORE-P14`: StudySpec binding to sessions, horizons, and VariantBudget;
- `FUTCORE-P16` through `FUTCORE-P20`: family diagnostics under the pinned scope;
- `FUTCORE-P21` / `FUTCORE-P22`: thin-session, cost-stress, and session x horizon
  consolidation;
- `FUTCORE-P24`: bounded-grid / VariantBudget audit;
- `FUTCORE-P28`: survivor and `WATCH` / `CANDIDATE_RESEARCH` caps.

## `campaign.yaml` Cross-Reference

| Recorded value | `campaign.yaml` source block |
| --- | --- |
| Research-only pilot with no paper/live/broker behavior | `project_profile`, `pilot_policy`, `phase_defaults.forbidden_global_changes` |
| In-scope universe `ES`, `NQ`, `RTY` | `data_policy.universe_in_scope` |
| Deferred universe `MES`, `MNQ`, `M2K`, rates, FX, commodities, vol products, options, equities, L1 eventstream, L2/L3 | `data_policy.universe_deferred` |
| Registry-resolved inputs and no provider/file access expansion | `data_policy.raw_provider_access_forbidden`, `data_policy.external_provider_calls_forbidden`, `runtime_policy.resolve_dataset_version_only` |
| Required session views | `horizon_session_policy.required_session_views` |
| Session x horizon matrix required | `horizon_session_policy.session_horizon_matrix_required` |
| Session split required | `horizon_session_policy.session_split_required` |
| Session-context guardrails | `horizon_session_policy.guardrails`, `feature_label_policy.session_context_allowed_if_point_in_time` |
| ETH research-in-scope but not trading-approved | `horizon_session_policy.guardrails` |
| `1m` sampling-only horizon | `horizon_session_policy.sampling_only_horizon` |
| `1m`, `3m` fragile horizons | `horizon_session_policy.fragile_horizons`, `feature_label_policy.fragile_label_horizons` |
| `5m`, `10m`, `15m`, `30m` primary horizons | `horizon_session_policy.primary_horizons`, `feature_label_policy.primary_label_horizons` |
| `60m`, `120m`, `240m`, `session_close` extended horizons | `feature_label_policy.optional_label_horizons`, `horizon_session_policy.extended_intraday_horizons_allowed` |
| Flat before maintenance / no trade-date-break crossing | `horizon_session_policy.flat_before_maintenance_break_required`, `horizon_session_policy.guardrails` |
| Thin-session stress requirement | `cost_policy.thin_session_stress_required` |
| Family budget required | `research_budget_policy.family_budget_required` |
| Cross-market / relative-value budget `0.40` | `research_budget_policy.family_budget.cross_market_relative_value` |
| VWAP / session-auction budget `0.20` | `research_budget_policy.family_budget.vwap_session_auction` |
| Regime momentum / reversion budget `0.15` | `research_budget_policy.family_budget.regime_momentum_reversion` |
| Liquidity-sweep / failed-breakout budget `0.15` | `research_budget_policy.family_budget.liquidity_sweep_failed_breakout` |
| BBO-tradability / confirmation budget `0.10` | `research_budget_policy.family_budget.bbo_tradability_confirmation` |
| Volume/activity overlay has no standalone budget and uses existing primitives only | `research_budget_policy.volume_activity_overlay` |
| AlphaSpec draft cap `<=40` | `research_budget_policy.max_alpha_spec_drafts` |
| Approved AlphaSpec cap `<=10` | `research_budget_policy.max_approved_alpha_specs` |
| New feature/label request cap `<=5` | `research_budget_policy.max_new_feature_or_label_requests` |
| Diagnostics survivor cap `<=3` | `research_budget_policy.max_diagnostics_survivors` |
| `WATCH` / `CANDIDATE_RESEARCH` cap `<=2` | `research_budget_policy.max_watch_or_candidate_research`, `pilot_policy.success_definition` |
| Per-study VariantBudget required | `research_budget_policy.variant_budget_required` |
| Scaled mining and continuous runner forbidden | `pilot_policy.scaled_mining_allowed`, `agent_policy.scaled_autonomous_mining_allowed`, `agent_policy.continuous_research_runner_allowed`, `phase_defaults.forbidden_global_changes` |
| Forbidden claim boundary | `promotion_policy.forbidden_states`, `phase_defaults.forbidden_global_changes` |

## Risk Cross-Reference

| Risk | Risk register source | Campaign policy anchor |
| --- | --- | --- |
| `R-001` scaled mining | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `pilot_policy.scaled_mining_allowed: false`, finite `research_budget_policy` caps |
| `R-010` fragile horizon overclaim | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `horizon_session_policy.fragile_horizons`, `feature_label_policy.fragile_label_horizons` |
| `R-011` ETH thin-session overclaim | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `horizon_session_policy.guardrails`, `cost_policy.thin_session_stress_required` |
| `R-012` variant explosion | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `research_budget_policy.variant_budget_required` |
| `R-022` underpowered pilot | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `research_budget_policy.max_alpha_spec_drafts`, `research_budget_policy.family_budget` |
| `R-023` overexpanded pilot | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `research_budget_policy` caps |
| `R-025` family budget ignored | `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md` | `research_budget_policy.family_budget_required`, `research_budget_policy.family_budget` |

## Non-Goals Confirmed

- No AlphaSpec is drafted here.
- No DatasetVersion, FeaturePack, or LabelPack is locked here.
- No cost model number or stress profile is defined here.
- No diagnostic, sample, data summary, feature value, label value, or provider
  response is run or committed here.
- No consumed `src/alpha_system/**` primitive is edited here.
- No universe, family, horizon, session, or budget expansion is introduced here.
