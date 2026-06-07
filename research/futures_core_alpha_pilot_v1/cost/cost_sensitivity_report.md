# FUTCORE-P21 CostSensitivityReport

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P21`  
Report type: value-free cost-stress and thin-session-stress consolidation  
Cost contract: `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`

This report consolidates already-recorded runtime diagnostics from
`FUTCORE-P16` through `FUTCORE-P20`. It does not rerun diagnostics, read raw
rows, infer missing market values, promote any idea, or make any profitability,
tradability, production, paper/live, broker, or capital-allocation claim.

`zero_cost` is diagnostic-only policy context. It is never a survivor,
promotion, continuation, watch, candidate, or favorable-evidence basis.

## Inputs Consulted

| Source | Role |
| --- | --- |
| `research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md` | P04 profile ladder and thin-session stress contract. |
| `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md` | Ten accepted idea identities and StudySpec/AlphaSpec mapping. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**` | P16 cross-market runtime diagnostics reports. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**` | P17 VWAP/session runtime diagnostics reports. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**` | P18 regime runtime diagnostics reports. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**` | P19 liquidity/PA runtime diagnostics reports. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**` | P20 BBO tradability runtime diagnostics reports. |

## Consolidation Method

Each P14 `StudySpec` is treated as one idea. For reports that expose multiple
runtime cost arms under one StudySpec, such as the regime momentum and reversion
arms, the arms are retained as subreports under the same idea.

The nonzero profile coverage is read only from runtime cost report
`profile_summaries` for `base`, `stress_1`, `stress_2`, and `double_cost`.
No missing profile is synthesized. `zero_cost` is recorded from the P04 policy
and source-report policy notes only; it was not used as a survival basis.

Thin-session stress is consolidated from P04's required thin views:
`ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and `post_RTH`.
The runtime reports map ETH-family views to the `ETH` penalty label and
`pre_RTH`/`post_RTH` to the `ILLIQUID` penalty label where detailed session-view
reports are present. These are stricter spread/slippage/capacity proxy overlays
for nonzero profiles only.

Flag rules:

| Flag | Rule |
| --- | --- |
| `COST_COVERAGE_GAP` | A required nonzero profile is missing, or all nonzero profiles are present but the runtime cost report is zero-fill or incomplete. |
| `ZERO_COST_ONLY_SURVIVOR` | A source runtime report records a favorable survivor state only under `zero_cost`. |
| `UNDER_STRESSED_ONLY` | `base` or `stress_1` is available while `stress_2` or `double_cost` is missing or incomplete for a survivor state. |
| `MATERIAL_COST_STRESS_GRADIENT` | Nonzero modeled cost/slippage proxy is monotonic from `base` to `double_cost` and the reported `double_cost`/`base` ratio is at least `2`. This is cost-burden metadata, not performance degradation. |
| `THIN_SESSION_ONLY_COST_BREAKDOWN` | The cost report's completed session labels are only thin-session penalty labels and no RTH comparator appears in that cost report. |
| `THIN_SESSION_RTH_GAP` | Detailed thin-session views are complete while comparable RTH views are zero-fill or inconclusive. |
| `BBO_PROXY_FALLBACK` | The report uses BBO-unavailable fallback and slippage/capacity proxy language. |

No `ZERO_COST_ONLY_SURVIVOR` or `UNDER_STRESSED_ONLY` flag is set in this
consolidation because the source diagnostics record no survivor/promotion state
by profile and no favorable result is based on `zero_cost`.

## Per-Idea Cost Profile Coverage

Legend: `policy-only` means `zero_cost` is recorded only as diagnostic policy
context. `present` means the runtime report contains that nonzero profile in
`profile_summaries`.

| Idea | Runtime status | zero_cost | base | stress_1 | stress_2 | double_cost | Cost report status | Cost fill | Stress gradient | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` / `FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | policy-only | present | present | present | present | `INCONCLUSIVE` / `dreport_eb8228deef35c66859e1340f` | 0 | not assessable from zero-fill report | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_c671fbeeb143512cbc03bc5b` / `FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | policy-only | present | present | present | present | `INCONCLUSIVE` / `dreport_d307c711b81f2acdc51b0685` | 0 | not assessable from zero-fill report | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_90b28233d828128664588a9a` / `FUTCORE-P07_cross_market_10_rty_catchup_rotation_context` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | policy-only | present | present | present | present | `INCONCLUSIVE` / `dreport_38dd51e2402932d491bde6b7` | 0 | not assessable from zero-fill report | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_7c8fb13628843890c171b122` / `FUTCORE-P07_cross_market_14_nq_es_divergence_context` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | policy-only | present | present | present | present | `INCONCLUSIVE` / `dreport_aaa40f6c751a15fdffa514ae` | 0 | not assessable from zero-fill report | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_69c22ec5847395ac8e81b5b6` / `FUTCORE-P08_vwap_session_01` | `INCONCLUSIVE` | policy-only | present | present | present | present | `DIAGNOSTICS_COMPLETE` / `dreport_f8344cf7fd0b8e7b262402f2` | 9 | monotonic, `double_cost`/`base` = `2` | `MATERIAL_COST_STRESS_GRADIENT`, `BBO_PROXY_FALLBACK` |
| `sspec_aff70fcbc4b7ff226fcc8149` / `FUTCORE-P08_vwap_session_07` | `INCONCLUSIVE` | policy-only | present | present | present | present | `DIAGNOSTICS_COMPLETE` / `dreport_3386524bdd142b97b717c374` | 9 | monotonic, `double_cost`/`base` = `2` | `MATERIAL_COST_STRESS_GRADIENT`, `BBO_PROXY_FALLBACK` |
| `sspec_267cc052e37668339c38d179` / `FUTCORE-P09_regime_01` | `INCONCLUSIVE` | policy-only | present | present | present | present | `DIAGNOSTICS_COMPLETE` for momentum and reversion arms / `dreport_eb463dda326e36b3178c46f7`, `dreport_71d5293a045bf5c96f60c9f8` | 4,403 per arm | monotonic, `double_cost`/`base` = `2` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_27bf1262b0bd23d27191cc86` / `FUTCORE-P10_liquidity_pa_02` | `INCONCLUSIVE` | policy-only | present | present | present | present | `DIAGNOSTICS_COMPLETE` / `dreport_71bb7c4686dbd22713a0b519` | 4,409 | monotonic, `double_cost`/`base` = `2` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_02c400a561891171a33c0c66` / `FUTCORE-P10_liquidity_pa_06` | `INCONCLUSIVE` | policy-only | present | present | present | present | `DIAGNOSTICS_COMPLETE` / `dreport_f9c588d4d7388f2c621c8964` | 4,403 | monotonic, `double_cost`/`base` = `2` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_9f6f741192a4b534f06e51c0` / `FUTCORE-P11_bbo_tradability_01` | `INCONCLUSIVE` | policy-only | present | present | present | present | `DIAGNOSTICS_COMPLETE` aggregate / `dreport_d6c3bf1dfb2e8cc185328cd6` | 20,406 | monotonic, `double_cost`/`base` = `2` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_RTH_GAP`, `BBO_PROXY_FALLBACK` |

## Thin-Session Consolidation

| Family / idea group | Thin-session coverage observed | RTH comparator observed | Consolidated flag |
| --- | --- | --- | --- |
| `cross_market` P16 ideas | No session cost fill; cross-market legs missing before cost stress could produce populated session cells. | No populated RTH comparator. | `COST_COVERAGE_GAP`; no thin-session survivor claim. |
| `vwap_session` P17 ideas | Aggregate cost reports include `ETH` and `ILLIQUID` penalty labels alongside `RTH`. | Present in aggregate session labels, but signal-probe remains inconclusive because no locked VWAP trigger FeaturePack resolved. | Thin-session evidence remains diagnostic-only; no thin-session survivor claim. |
| `regime` P18 idea | Momentum and reversion cost arms complete under the `ETH` penalty label. | No RTH comparator in the cost report. | `THIN_SESSION_ONLY_COST_BREAKDOWN`; no thin-session survivor claim. |
| `liquidity_pa` P19 ideas | Cost reports complete under the `ETH` penalty label. | No RTH comparator in the cost reports. | `THIN_SESSION_ONLY_COST_BREAKDOWN`; no thin-session survivor claim. |
| `bbo_tradability` P20 idea | Detailed `5m` session-view cost reports complete for `ETH_evening`, `ETH_only`, `ETH_overnight`, `pre_RTH`, and `post_RTH`; `pre_RTH` and `post_RTH` use the `ILLIQUID` penalty label. | `RTH`, `RTH_only`, and `RTH_with_ETH_context` are zero-fill/inconclusive in the detailed session-view reports. | `THIN_SESSION_RTH_GAP`; no thin-session survivor claim. |

Detailed BBO thin-session session-view coverage:

| Session view | Runtime penalty label | Status | Fill count | Nonzero profiles |
| --- | --- | --- | ---: | --- |
| `ETH_evening` | `ETH` | `DIAGNOSTICS_COMPLETE` | 1,783 | `base`, `stress_1`, `stress_2`, `double_cost` |
| `ETH_only` | `ETH` | `DIAGNOSTICS_COMPLETE` | 6,862 | `base`, `stress_1`, `stress_2`, `double_cost` |
| `ETH_overnight` | `ETH` | `DIAGNOSTICS_COMPLETE` | 2,399 | `base`, `stress_1`, `stress_2`, `double_cost` |
| `pre_RTH` | `ILLIQUID` | `DIAGNOSTICS_COMPLETE` | 450 | `base`, `stress_1`, `stress_2`, `double_cost` |
| `post_RTH` | `ILLIQUID` | `DIAGNOSTICS_COMPLETE` | 280 | `base`, `stress_1`, `stress_2`, `double_cost` |
| `RTH` | none populated | `INCONCLUSIVE` | 0 | `base`, `stress_1`, `stress_2`, `double_cost` present but zero-fill |
| `RTH_only` | none populated | `INCONCLUSIVE` | 0 | `base`, `stress_1`, `stress_2`, `double_cost` present but zero-fill |
| `RTH_with_ETH_context` | none populated | `INCONCLUSIVE` | 0 | `base`, `stress_1`, `stress_2`, `double_cost` present but zero-fill |

## Coverage And Gaps

- Required nonzero profile names are present for all ten StudySpecs:
  `base`, `stress_1`, `stress_2`, and `double_cost`.
- `zero_cost` is policy-only diagnostic context in this consolidation. It is
  not an executed survivor profile and is not a promotion basis.
- The four cross-market ideas have zero-fill cost-stress reports because the
  P16 runtime rejected cross-market diagnostics for missing NQ/RTY legs. This
  is a cost coverage gap and must not be treated as nonzero cost survival.
- All completed cost reports use BBO-unavailable fallback markers and
  slippage/capacity proxy language. This is proxy-only evidence under R-026 and
  cannot support proven capacity or tradability language.
- P20's BBO StudySpec remains `INCONCLUSIVE` because no locked BBO FeaturePack
  resolves; the BBO cost reports therefore preserve missing-BBO fallback cells.
- Several completed cost reports expose only `ETH` or `ILLIQUID` penalty labels
  without an RTH comparator. They are flagged as thin-session cost-breakdown
  limitations, not as favorable thin-session results.
- The runtime cost report objects carry the internal hashed cost model id
  `cmv_15b7668a13c0da9182400fcb`; the governing P04 policy contract remains
  `cmv_futcore_pilot_three_layer_session_stress_v1`. This consolidation binds
  the method and profile ladder to P04 and records the runtime id as source
  lineage to be reviewed by later evidence phases if exact id parity is needed.
- The known unresolved `15m` LabelPack limitation from P17/P20 is carried as an
  input diagnostics limitation for later matrix work. This report does not
  synthesize 15m cost outcomes.

## Standing Boundaries

This report is research evidence only. It contains source ids, statuses,
profile coverage, cost-stress metadata, session penalty metadata, and gap flags
only. It does not contain row-level feature values, label values, market values,
provider payloads, raw/canonical data, Parquet payloads, local databases, model
binaries, reviewer verdicts, PR state, merge state, or any promotion decision.

