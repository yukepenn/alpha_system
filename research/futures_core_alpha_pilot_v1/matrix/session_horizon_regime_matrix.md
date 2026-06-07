# FUTCORE-P22 Session / Horizon / Regime Stability Matrix

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P22`  
Report type: value-free session x horizon x regime consolidation  
Generated from committed `FUTCORE-P16` through `FUTCORE-P21` evidence only.

This report consolidates existing diagnostics reports and the `FUTCORE-P21`
cost-sensitivity report by reference. It does not run new diagnostics, read raw
or row-level data, edit consumed primitives, promote any idea, create a
reviewer verdict, or make any profitability, tradability, paper/live, broker,
deployment, or capital-allocation claim.

`zero_cost` remains diagnostic-only policy context. It is never a survival,
promotion, watch, candidate, or favorable-evidence basis.

## Sources Consulted

| Source | Role |
| --- | --- |
| `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md` | P14 StudySpec to AlphaSpec mapping, sessions, horizons, and pack references. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**` | P16 cross-market diagnostic statuses and input-gap references. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**` | P17 VWAP/session diagnostic statuses and session-horizon coverage. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**` | P18 regime split diagnostic statuses and regime-axis coverage. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**` | P19 liquidity/PA diagnostic statuses and session/regime split coverage. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**` | P20 BBO diagnostic statuses, BBO fallback flags, and detailed 5m session cost refs. |
| `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md` | P21 nonzero cost coverage, thin-session flags, `zero_cost` boundary, and BBO fallback flags. |

Run-local `RuntimeRunSummary` and `RuntimeToolResult` ids are cited only where
already present in committed reports. No `runs/**` file is copied here.

## Matrix Contract

Required session views:

`full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`,
`pre_RTH`, `RTH`, `post_RTH`, `RTH_with_ETH_context`.

Horizon zones:

`1m` sampling-only; `1m` and `3m` fragile diagnostics-only; primary `5m`,
`10m`, `15m`, `30m`; extended intraday `60m`, `120m`, `240m`,
`session_close`.

Regime axes:

trendiness / gate activation, volatility, and range-compression. Momentum vs
reversion activation is recorded only for regime-gated ideas.

Cell codes:

| Code | Meaning |
| --- | --- |
| `POP n` | Source report has populated coverage count `n`; status remains diagnostic/inconclusive unless otherwise stated. |
| `ZERO` | Source report has a resolved label/session view but zero observations for that cell. |
| `UNRES` | Required locked input, label pack, or subsegment binding is unresolved in source reports. |
| `FRAG` | Fragile-horizon diagnostics-only cell (`1m` or `3m`); no promotion basis. |
| `NS` | No P16-P21 source report for that horizon/cell; no evidence is synthesized. |
| `REJ` | Family diagnostics rejected the StudySpec before a populated matrix could support survival. |
| `ETH-RO` | ETH/thin-session research-only; not trading-approved. |
| `BBO-FB` | BBO-unavailable fallback/proxy marker carried from diagnostics/cost reports. |

No cell below is a promotion state or reviewer verdict.

## Consolidated Idea Set

P22 treats the six non-rejected P17-P20 StudySpecs as
`diagnostic_survivors_for_consolidation`. This phrase is only a reporting label:
all six remain `INCONCLUSIVE`, require later review, and have no promotion
state. The four P16 cross-market StudySpecs are retained in a rejected-source
summary because P21 consolidated their cost coverage gaps.

| StudySpec | Family | Runtime status carried into P22 | Consolidated in survivor matrix |
| --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `cross_market` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | no |
| `sspec_c671fbeeb143512cbc03bc5b` | `cross_market` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | no |
| `sspec_90b28233d828128664588a9a` | `cross_market` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | no |
| `sspec_7c8fb13628843890c171b122` | `cross_market` | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` | no |
| `sspec_69c22ec5847395ac8e81b5b6` | `vwap_session` | `INCONCLUSIVE` | yes |
| `sspec_aff70fcbc4b7ff226fcc8149` | `vwap_session` | `INCONCLUSIVE` | yes |
| `sspec_267cc052e37668339c38d179` | `regime` | `INCONCLUSIVE` | yes |
| `sspec_27bf1262b0bd23d27191cc86` | `liquidity_pa` | `INCONCLUSIVE` | yes |
| `sspec_02c400a561891171a33c0c66` | `liquidity_pa` | `INCONCLUSIVE` | yes |
| `sspec_9f6f741192a4b534f06e51c0` | `bbo_tradability` | `INCONCLUSIVE` | yes |

## Source Rejection Summary

The P16 cross-market reports reached runtime input resolution and cost surfaces,
but cross-market alignment produced zero aligned ES/NQ/RTY snapshots because
NQ and RTY rows were absent from the diagnostics view. P21 carries these as
`COST_COVERAGE_GAP` plus `BBO_PROXY_FALLBACK`; no narrow-cell-only survivor
flag applies because these StudySpecs did not survive the family diagnostics
gate.

| StudySpec | Declared primary horizon | Source coverage summary | P21 carried flags |
| --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `5m` | aligned snapshots `0`; required symbols observed `1` of `3`; NQ/RTY missing | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_c671fbeeb143512cbc03bc5b` | `10m` | aligned snapshots `0`; required symbols observed `1` of `3`; NQ/RTY missing | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_90b28233d828128664588a9a` | `15m` | aligned snapshots `0`; required symbols observed `1` of `3`; NQ/RTY missing; 15m LabelPack unresolved | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |
| `sspec_7c8fb13628843890c171b122` | `30m` | aligned snapshots `0`; required symbols observed `1` of `3`; NQ/RTY missing | `COST_COVERAGE_GAP`, `BBO_PROXY_FALLBACK` |

## Consolidated Flag Table

| StudySpec | `narrow_cell_only` | `fragile_horizon_diagnostics_only` | `thin_session_research_only` | `zero_cost_only` | P21 carried cost/thin-session flags |
| --- | --- | --- | --- | --- | --- |
| `sspec_69c22ec5847395ac8e81b5b6` | `false_no_stable_cells_recorded` | `1m`, `3m` | `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `post_RTH` | `false` | `MATERIAL_COST_STRESS_GRADIENT`, `BBO_PROXY_FALLBACK`; thin evidence diagnostic-only |
| `sspec_aff70fcbc4b7ff226fcc8149` | `false_no_stable_cells_recorded` | `1m`, `3m` | `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `post_RTH` | `false` | `MATERIAL_COST_STRESS_GRADIENT`, `BBO_PROXY_FALLBACK`; thin evidence diagnostic-only |
| `sspec_267cc052e37668339c38d179` | `false_no_stable_cells_recorded` | `1m`, `3m` | `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `post_RTH` | `false` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_27bf1262b0bd23d27191cc86` | `false_no_stable_cells_recorded` | `1m`, `3m` | `ETH_only`; thin subsegments unresolved | `false` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_02c400a561891171a33c0c66` | `false_no_stable_cells_recorded` | `1m`, `3m` | `ETH_only`; thin subsegments unresolved | `false` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_ONLY_COST_BREAKDOWN`, `BBO_PROXY_FALLBACK` |
| `sspec_9f6f741192a4b534f06e51c0` | `false_no_stable_cells_recorded` | `1m`, `3m` | `ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, `post_RTH` | `false` | `MATERIAL_COST_STRESS_GRADIENT`, `THIN_SESSION_RTH_GAP`, `BBO_PROXY_FALLBACK` |

No P16-P21 source report records a stable favorable cell that is confined to one
session/horizon/regime slice. Thin-session-only coverage gaps are still flagged
because ETH/pre_RTH/post_RTH evidence is research-only and not trading-approved.

## Matrix A: VWAP / Session Survivors

Applies to:

- `sspec_69c22ec5847395ac8e81b5b6` / `aspec_b40aee52d4399dd5b855a6ed`.
- `sspec_aff70fcbc4b7ff226fcc8149` / `aspec_43cd6c154bca2fcc419eee83`.

Source status: `INCONCLUSIVE` because no locked running/completed VWAP trigger
FeaturePack resolved and `15m` has no locked LabelPack. Source cost refs:
`dreport_f8344cf7fd0b8e7b262402f2` and
`dreport_3386524bdd142b97b717c374`; both carry BBO fallback and nonzero
profiles `base`, `stress_1`, `stress_2`, `double_cost`.

| Horizon | full_session | RTH_only | ETH_only | ETH_evening | ETH_overnight | pre_RTH | RTH | post_RTH | RTH_with_ETH_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1m` | `FRAG` | `FRAG` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG` | `FRAG ETH-RO` | `FRAG` |
| `3m` | `FRAG` | `FRAG` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG` | `FRAG ETH-RO` | `FRAG` |
| `5m` | `POP 6862` | `ZERO` | `POP 6862 ETH-RO` | `POP 1783 ETH-RO` | `POP 2399 ETH-RO` | `POP 450 ETH-RO` | `ZERO` | `POP 280 ETH-RO` | `ZERO` |
| `10m` | `POP 6832` | `ZERO` | `POP 6832 ETH-RO` | `POP 1778 ETH-RO` | `POP 2399 ETH-RO` | `POP 450 ETH-RO` | `ZERO` | `POP 255 ETH-RO` | `ZERO` |
| `15m` | `UNRES` | `UNRES` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES` | `UNRES ETH-RO` | `UNRES` |
| `30m` | `POP 6712` | `ZERO` | `POP 6712 ETH-RO` | `POP 1758 ETH-RO` | `POP 2399 ETH-RO` | `POP 450 ETH-RO` | `ZERO` | `POP 155 ETH-RO` | `ZERO` |
| `60m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `120m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `240m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `session_close` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |

Regime-axis summary for both VWAP ideas:

| Regime axis | Summary |
| --- | --- |
| Trendiness / gate activation | Not regime-gated by source reports; no per-idea trend activation report. |
| Volatility | No per-idea VWAP regime split in P17; P18 common locked-partition context records high/low coverage but does not make this a VWAP stability finding. |
| Range-compression | No per-idea VWAP regime split in P17; P18 common locked-partition context records compression/not-compression coverage but does not make this a VWAP stability finding. |
| Momentum vs reversion | Not applicable; these StudySpecs are not regime-gated momentum/reversion ideas. |

## Matrix B: Regime Momentum/Reversion Survivor

Applies to `sspec_267cc052e37668339c38d179` /
`aspec_eb962fc197eaf3955c5e4711`.

Source status: `INCONCLUSIVE`. Exact gate activation is
`INCONCLUSIVE_MISSING_LOCKED_TRENDINESS_AND_ACTIVATION_BINDING`; both momentum
and reversion signal-probe arms are recorded as `REJECTED`. P21 carries
`THIN_SESSION_ONLY_COST_BREAKDOWN`, `MATERIAL_COST_STRESS_GRADIENT`, and
`BBO_PROXY_FALLBACK`.

| Horizon | full_session | RTH_only | ETH_only | ETH_evening | ETH_overnight | pre_RTH | RTH | post_RTH | RTH_with_ETH_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1m` | `FRAG` | `FRAG` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG` | `FRAG ETH-RO` | `FRAG` |
| `3m` | `FRAG` | `FRAG` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG` | `FRAG ETH-RO` | `FRAG` |
| `5m` | `POP 6862` | `ZERO` | `POP 6862 ETH-RO` | `POP 1783 ETH-RO` | `POP 2399 ETH-RO` | `POP 450 ETH-RO` | `ZERO` | `POP 280 ETH-RO` | `ZERO` |
| `10m` | `POP 6832` | `ZERO` | `POP 6832 ETH-RO` | `POP 1778 ETH-RO` | `POP 2399 ETH-RO` | `POP 450 ETH-RO` | `ZERO` | `POP 255 ETH-RO` | `ZERO` |
| `15m` | `UNRES` | `UNRES` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES` | `UNRES ETH-RO` | `UNRES` |
| `30m` | `POP 6712` | `ZERO` | `POP 6712 ETH-RO` | `POP 1758 ETH-RO` | `POP 2399 ETH-RO` | `POP 450 ETH-RO` | `ZERO` | `POP 155 ETH-RO` | `ZERO` |
| `60m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `120m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `240m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `session_close` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |

Regime-axis summary:

| Regime axis | All resolved horizons | 5m | 10m | 30m | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Trendiness / gate activation | unresolved `20406` | unresolved `6862` | unresolved `6832` | unresolved `6712` | activation binding unresolved |
| Volatility | high `10157`, low `10159`, unresolved `90` | high `3388`, low `3444`, unresolved `30` | high `3388`, low `3414`, unresolved `30` | high `3381`, low `3301`, unresolved `30` | split coverage only, no stable activation |
| Range-compression | compression `5510`, not-compression `14809`, unresolved `87` | compression `1883`, not-compression `4950`, unresolved `29` | compression `1854`, not-compression `4949`, unresolved `29` | compression `1773`, not-compression `4910`, unresolved `29` | split coverage only, no stable activation |
| Momentum vs reversion | both arms source-status `REJECTED` | source-status `REJECTED` | source-status `REJECTED` | source-status `REJECTED` | no activation survivor |

## Matrix C: Liquidity / Objective PA Survivors

Applies to:

- `sspec_27bf1262b0bd23d27191cc86` / `aspec_df2d040e45564c259ef3de6d`.
- `sspec_02c400a561891171a33c0c66` / `aspec_39ffc190cfbfa6ba0b1a2a25`.

Source status: `INCONCLUSIVE` because exact objective price-action trigger
counts are unresolved without a locked structure FeaturePack and `15m` has no
locked LabelPack. P21 carries `THIN_SESSION_ONLY_COST_BREAKDOWN`,
`MATERIAL_COST_STRESS_GRADIENT`, and `BBO_PROXY_FALLBACK`. Source runtime run
ids are
`2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1_sspec_27bf1262b0bd23d27191cc86`
and
`2026-06-07T041343Z_ALPHA_FUTURES_CORE_ALPHA_PILOT_V1_sspec_02c400a561891171a33c0c66`.

| Horizon | full_session | RTH_only | ETH_only | ETH_evening | ETH_overnight | pre_RTH | RTH | post_RTH | RTH_with_ETH_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1m` | `FRAG` | `FRAG` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG` | `FRAG ETH-RO` | `FRAG` |
| `3m` | `FRAG` | `FRAG` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG ETH-RO` | `FRAG` | `FRAG ETH-RO` | `FRAG` |
| `5m` | `POP 6862` | `ZERO` | `POP 6862 ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `ZERO` | `UNRES ETH-RO` | `ZERO` |
| `10m` | `POP 20406` | `ZERO` | `POP 20406 ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `ZERO` | `UNRES ETH-RO` | `ZERO` |
| `15m` | `UNRES` | `UNRES` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES` | `UNRES ETH-RO` | `UNRES` |
| `30m` | `POP 20406` | `ZERO` | `POP 20406 ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `UNRES ETH-RO` | `ZERO` | `UNRES ETH-RO` | `ZERO` |
| `60m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `120m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `240m` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |
| `session_close` | `NS` | `NS` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS ETH-RO` | `NS` | `NS ETH-RO` | `NS` |

Regime-axis summary for both liquidity ideas:

| Regime axis | Summary |
| --- | --- |
| Trendiness / gate activation | P19 regime split reports mark trend splits inconclusive with zero retained trend/range observations; no momentum/reversion activation applies. |
| Volatility | P19 reports expose volatility bucket coverage for split diagnostics, but source status remains `INCONCLUSIVE`; no stable regime cell is recorded. |
| Range-compression | Objective trigger binding is unresolved; no range-compression activation is recorded as stable. |
| Momentum vs reversion | Not applicable; these StudySpecs are liquidity/PA ideas, not regime-gated momentum/reversion ideas. |

## Matrix D: BBO Tradability Survivor

Applies to `sspec_9f6f741192a4b534f06e51c0` /
`aspec_1284e49b083df11eeb0481ea`.

Source status: `INCONCLUSIVE` because no locked BBO FeaturePack resolves and
`15m` has no locked LabelPack. P21 carries `THIN_SESSION_RTH_GAP`,
`MATERIAL_COST_STRESS_GRADIENT`, and `BBO_PROXY_FALLBACK`. Detailed 5m session
cost refs are present for every required session view; RTH detailed session
cost cells are zero-fill/inconclusive.

| Horizon | full_session | RTH_only | ETH_only | ETH_evening | ETH_overnight | pre_RTH | RTH | post_RTH | RTH_with_ETH_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1m` | `FRAG BBO-FB` | `FRAG BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG BBO-FB` |
| `3m` | `FRAG BBO-FB` | `FRAG BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG BBO-FB` | `FRAG ETH-RO BBO-FB` | `FRAG BBO-FB` |
| `5m` | `POP 6862 BBO-FB` | `ZERO BBO-FB` | `POP 6862 ETH-RO BBO-FB` | `POP 1783 ETH-RO BBO-FB` | `POP 2399 ETH-RO BBO-FB` | `POP 450 ETH-RO BBO-FB` | `ZERO BBO-FB` | `POP 280 ETH-RO BBO-FB` | `ZERO BBO-FB` |
| `10m` | `POP 6832 BBO-FB` | `ZERO BBO-FB` | `POP 6832 ETH-RO BBO-FB` | `POP 1778 ETH-RO BBO-FB` | `POP 2399 ETH-RO BBO-FB` | `POP 450 ETH-RO BBO-FB` | `ZERO BBO-FB` | `POP 255 ETH-RO BBO-FB` | `ZERO BBO-FB` |
| `15m` | `UNRES BBO-FB` | `UNRES BBO-FB` | `UNRES ETH-RO BBO-FB` | `UNRES ETH-RO BBO-FB` | `UNRES ETH-RO BBO-FB` | `UNRES ETH-RO BBO-FB` | `UNRES BBO-FB` | `UNRES ETH-RO BBO-FB` | `UNRES BBO-FB` |
| `30m` | `POP 6712 BBO-FB` | `ZERO BBO-FB` | `POP 6712 ETH-RO BBO-FB` | `POP 1758 ETH-RO BBO-FB` | `POP 2399 ETH-RO BBO-FB` | `POP 450 ETH-RO BBO-FB` | `ZERO BBO-FB` | `POP 155 ETH-RO BBO-FB` | `ZERO BBO-FB` |
| `60m` | `NS BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` |
| `120m` | `NS BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` |
| `240m` | `NS BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` |
| `session_close` | `NS BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` | `NS ETH-RO BBO-FB` | `NS BBO-FB` |

Regime-axis summary:

| Regime axis | Summary |
| --- | --- |
| Trendiness / gate activation | Not regime-gated by source reports; no per-idea trend activation report. |
| Volatility | No per-idea BBO regime split in P20; source BBO binding is unresolved, so no stable volatility cell is recorded. |
| Range-compression | No per-idea BBO range-compression split in P20; no stable range-compression cell is recorded. |
| Momentum vs reversion | Not applicable; this StudySpec is a BBO confirmation/risk idea. |

## BBO Detailed 5m Session Cost References

These are source ids/hashes only, carried from P20 and P21. They are not
execution evidence and do not imply trading approval.

| Session view | Report id | Report hash prefix | P22 cell state |
| --- | --- | --- | --- |
| `full_session` | `dreport_126f25952a585ad598ce9cd3` | `126f25952a585` | populated, BBO fallback |
| `RTH_only` | `dreport_85c48fa781b41066299b7180` | `85c48fa781b4` | zero-fill/inconclusive, BBO fallback |
| `ETH_only` | `dreport_4c924616e5fd1508cd1532e4` | `4c924616e5fd` | populated, ETH research-only, BBO fallback |
| `ETH_evening` | `dreport_01f705b5559a10c09f6323aa` | `01f705b5559a` | populated, ETH research-only, BBO fallback |
| `ETH_overnight` | `dreport_6a44cc8a64933fabaaadd5f1` | `6a44cc8a6493` | populated, ETH research-only, BBO fallback |
| `pre_RTH` | `dreport_cffef48926a3dd5826ae0b4b` | `cffef48926a3` | populated, thin-session research-only, BBO fallback |
| `RTH` | `dreport_4fc478390d5b69ea8001aa6c` | `4fc478390d5b` | zero-fill/inconclusive, BBO fallback |
| `post_RTH` | `dreport_d600aaa4234442b049290541` | `d600aaa42344` | populated, thin-session research-only, BBO fallback |
| `RTH_with_ETH_context` | `dreport_7a5cd0e9cd6db40fe7b96bff` | `7a5cd0e9cd6d` | zero-fill/inconclusive, BBO fallback |

## Consolidated Gaps

- `1m` and `3m` are diagnostics-only fragile horizons for every consolidated
  idea. They are not robust evidence cells and cannot be a promotion basis.
- `15m` remains unresolved across consolidated survivors because no locked
  `15m` LabelPack resolves in the P03/P14 binding.
- `60m`, `120m`, `240m`, and `session_close` have no P16-P21 runtime source
  reports. They remain `NS` cells, not missing favorable evidence.
- RTH comparator cells are zero-count or zero-fill in the locked development
  partition for VWAP, regime, liquidity, and BBO survivors.
- ETH/pre_RTH/post_RTH cells are research-only and not trading-approved.
- BBO fallback is visible across completed cost reports; no capacity,
  spread/depth, or tradability proof is claimed.
- No `ZERO_COST_ONLY_SURVIVOR` or `UNDER_STRESSED_ONLY` flag is set in P21 or
  carried here.

## Boundary Confirmations

- Fast path is not reference truth.
- Validated research is not paper/live approval.
- Agent output is not autonomous trading, self-review, or self-promotion.
- No promotion state, reviewer verdict, PR state, merge state, order, broker,
  paper/live, deployment, profitability, or tradability claim is recorded here.
- This report contains only source ids/hashes, statuses, counts, coverage
  flags, and diagnostic metadata. It contains no row-level feature values,
  label values, signal values, market values, provider payloads, raw/canonical
  data, Parquet/Arrow/Feather/SQLite/DB payloads, model binaries, logs, caches,
  or secrets.
