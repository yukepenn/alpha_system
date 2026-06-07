# AlphaSpec Critique Budget Audit

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P12`  
Audit type: value-free family budget and finite quota reconciliation  
Critic role: `AlphaSpec Critic:FUTCORE-P12`

This audit reconciles the `FUTCORE-P07` through `FUTCORE-P11` draft set against
the campaign research budget. It records specification decisions only. It does
not run diagnostics, author StudySpecs, create FeatureRequests or LabelSpecs,
promote ideas, or make alpha, profitability, tradability, paper/live, broker,
production, or capital-allocation claims.

## Source Budget

From `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml >
research_budget_policy`:

| Cap or budget | Contract |
| --- | ---: |
| Max AlphaSpec drafts | 40 |
| Max approved AlphaSpecs | 10 |
| Max new FeatureRequest or LabelSpec records | 5 |
| Max diagnostics survivors | 3 |
| Max `WATCH` or `CANDIDATE_RESEARCH` records | 2 |
| Cross-market / relative value | 40% |
| VWAP / session auction | 20% |
| Regime momentum/reversion | 15% |
| Liquidity sweep / failed breakout / objective PA | 15% |
| BBO tradability / top-book confirmation | 10% |
| Volume/activity | Overlay-only, no standalone budget |

## Draft Count Reconciliation

| Family | Draft cap / target from P05 | Drafts found | Verdict |
| --- | ---: | ---: | --- |
| `cross_market` | 16 | 16 | PASS |
| `vwap_session` | 8 | 8 | PASS |
| `regime` | 6 | 6 | PASS |
| `liquidity_pa` | 6 | 6 | PASS |
| `bbo_tradability` | 4 | 4 | PASS |
| **Total** | **40** | **40** | **PASS** |

The draft set exactly equals `max_alpha_spec_drafts: 40`; no additional
AlphaSpec draft capacity remains in this campaign budget.

## Accepted Set Reconciliation

The accepted set uses the full `max_approved_alpha_specs: 10` cap.

| Family | Budget share | Exact seats at 10 | Accepted | Accepted share | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| `cross_market` | 40% | 4.0 | 4 | 40% | PASS |
| `vwap_session` | 20% | 2.0 | 2 | 20% | PASS |
| `regime` | 15% | 1.5 | 1 | 10% | PASS with integer-rounding note |
| `liquidity_pa` | 15% | 1.5 | 2 | 20% | PASS with integer-rounding note |
| `bbo_tradability` | 10% | 1.0 | 1 | 10% | PASS |
| **Total** | **100%** | **10.0** | **10** | **100%** | **PASS** |

The 15%/15% families cannot both receive exactly 1.5 accepted specs under a
10-spec cap. The audit applies an explicit one-seat/two-seat integer split for
the tied remainder. The extra rounded seat is assigned to `liquidity_pa` because
the accepted liquidity/PA records have more narrowly objective trigger rules at
this critique gate; this does not authorize further liquidity/PA expansion and
does not reduce the downstream requirement to preserve regime diagnostics for
the one accepted regime candidate.

## Accepted Drafts

| Family | Draft id | Source draft | Decision record |
| --- | --- | --- | --- |
| `cross_market` | `aspec_0ebd90cecfd475607685b445` | `cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context.json` | `critiques/cross_market/FUTCORE-P07_cross_market_01_nq_leads_es_completed_bar_context_critique.md` |
| `cross_market` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket.json` | `critiques/cross_market/FUTCORE-P07_cross_market_05_nq_beta_residual_vs_es_rty_basket_critique.md` |
| `cross_market` | `aspec_a41dcccac5552de945aba825` | `cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context.json` | `critiques/cross_market/FUTCORE-P07_cross_market_10_rty_catchup_rotation_context_critique.md` |
| `cross_market` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context.json` | `critiques/cross_market/FUTCORE-P07_cross_market_14_nq_es_divergence_context_critique.md` |
| `vwap_session` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session/FUTCORE-P08_vwap_session_01.md` | `critiques/vwap_session/FUTCORE-P08_vwap_session_01_critique.md` |
| `vwap_session` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session/FUTCORE-P08_vwap_session_07.md` | `critiques/vwap_session/FUTCORE-P08_vwap_session_07_critique.md` |
| `regime` | `aspec_eb962fc197eaf3955c5e4711` | `regime/FUTCORE-P09_regime_01.md` | `critiques/regime/FUTCORE-P09_regime_01_critique.md` |
| `liquidity_pa` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa/FUTCORE-P10_liquidity_pa_02.md` | `critiques/liquidity_pa/FUTCORE-P10_liquidity_pa_02_critique.md` |
| `liquidity_pa` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa/FUTCORE-P10_liquidity_pa_06.md` | `critiques/liquidity_pa/FUTCORE-P10_liquidity_pa_06_critique.md` |
| `bbo_tradability` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability/FUTCORE-P11_bbo_tradability_01.md` | `critiques/bbo_tradability/FUTCORE-P11_bbo_tradability_01_critique.md` |

Accepted status means `accept-for-StudySpec` only. The accepted records still
carry downstream flags for P13/P15 binding checks, P14 StudySpec construction,
and the No-Lookahead Auditor lane.

## Decision Counts

| Family | Accept-for-StudySpec | Revise | Reject | Total |
| --- | ---: | ---: | ---: | ---: |
| `cross_market` | 4 | 9 | 3 | 16 |
| `vwap_session` | 2 | 4 | 2 | 8 |
| `regime` | 1 | 4 | 1 | 6 |
| `liquidity_pa` | 2 | 4 | 0 | 6 |
| `bbo_tradability` | 1 | 3 | 0 | 4 |
| **Total** | **10** | **24** | **6** | **40** |

## Cap Verdicts

| Cap | Observed | Limit | Verdict | Reason |
| --- | ---: | ---: | --- | --- |
| AlphaSpec drafts | 40 | 40 | PASS | Every P07-P11 draft has one critique record; the draft cap is not exceeded. |
| Approved AlphaSpecs | 10 | 10 | PASS | The accepted set equals, but does not exceed, the approval cap. |
| Family budget | 4/2/1/2/1 | 40/20/15/15/10 | PASS | Integer rounding is explicit for the tied 15% families; no hidden reallocation is recorded. |
| New FeatureRequest or LabelSpec records | 0 | 5 | PASS | P12 creates no FeatureRequest or LabelSpec; gaps are routed to P13/P15. |
| Diagnostics survivors | 0 | 3 | PASS | P12 runs no diagnostics and creates no survivor state. |
| `WATCH` or `CANDIDATE_RESEARCH` records | 0 | 2 | PASS | P12 creates no promotion decision or survivor classification. |
| Volume/activity standalone budget | 0 | 0 | PASS | Volume/activity remains overlay-only and no standalone volume family or quota is created. |

## Duplicate Exposure Routing

The critique records route duplicate exposure into these downstream groups:

| Group | Records affected | Routing note |
| --- | ---: | --- |
| Cross-market lead/lag | 4 | Keep accepted pairwise NQ-to-ES representative; reject broad triad cascade. |
| Cross-market residual | 4 | Keep one residual representative; revise sibling basket/pair residuals. |
| Cross-market rotation | 4 | Keep one RTY rotation representative; reject broad defensive umbrella. |
| Cross-market confirmation/divergence | 4 | Keep one pairwise divergence representative; reject broad dispersion umbrella. |
| VWAP reclaim/reject/distance | 3 | Keep reclaim; reject generic distance buckets and revise paired reject. |
| VWAP open/ETH/gap/overnight | 3 | Keep completed ETH VWAP context; revise gap and overnight-level variants. |
| Regime trend/vol/compression/session/VWAP gates | 6 | Keep canonical trend/vol/range gate; revise or reject overlapping specialized gates. |
| Liquidity/PA sweep and breakout | 6 | Keep close-back-inside and failed-breakout candidates; revise parent/overlay variants. |
| BBO spread/depth/microprice/quote-quality | 4 | Keep spread/depth confirmation; revise other BBO overlays into possible shared gates after P13/P15. |

## No-Lookahead Routing

No critique record resolves no-lookahead issues in P12. Records only route flags:

- Cross-market accepted records require cross-instrument `available_ts`,
  missingness, and label timing checks.
- VWAP/session accepted records require running-vs-final VWAP, completed ETH
  context, opening-window, and label timing checks.
- The accepted regime record requires causal regime metric windows, inactive
  transition state checks, and label/primitive binding checks.
- Accepted liquidity/PA records require timestamped level, boundary, breakout,
  and close-back-inside checks.
- The accepted BBO record requires valid BBO, stale/crossed/missing quote,
  causal spread-zscore, and BBO binding checks.

## Overlay Confirmation

Volume/activity remains overlay-only. The critique records do not create a
standalone volume/activity family, quota, StudySpec, FeatureRequest, LabelSpec,
diagnostic, or promotion path. Any future use must be hosted by an accepted
family and use existing primitives unless P15 explicitly records an approved gap.
