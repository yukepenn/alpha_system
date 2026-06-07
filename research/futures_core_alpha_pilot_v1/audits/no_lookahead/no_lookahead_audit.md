# FUTCORE-P23 No-Lookahead Audit

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P23`  
Report type: value-free NoLookaheadAuditReport  
Audit surface: committed `FUTCORE-P22` matrix plus referenced P03/P14/P16-P21
artifacts only.

This report audits temporal validity by reference. It does not rerun runtime
diagnostics, read raw provider data, inspect Parquet or SQLite payloads, edit
consumed primitives, assign a promotion state, create a reviewer verdict, or
make any profitability, tradability, paper/live, broker, deployment, or capital
claim.

`zero_cost` remains diagnostic-only policy context and is never a promotion or
survival basis.

## Sources Consulted

| Source | Role |
| --- | --- |
| `research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md` | P22 audit-set source and survivor/rejected-source status. |
| `research/futures_core_alpha_pilot_v1/study_specs/INDEX.md` and `study_specs/sspec_*.json` | P14 StudySpec ids, AlphaSpec ids, locked FeaturePack/LabelPack refs, timing rules, stopping rules, and P15 gap refs. |
| `research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md` | P03 DatasetVersion, FeaturePack `available_ts`, and LabelPack `label_available_ts` lock metadata. |
| `research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md` and `feature_requests/p15_*.json` | P15 governed feature/label gap records and causal availability assumptions. |
| `research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` | P15 15m LabelSpec rules and `label_available_ts` policy. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**` | P16 cross-market availability, missingness, same-bar, and rejection-source context. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**` | P17 VWAP/session source status, running-vs-final context, and unresolved VWAP/15m bindings. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**` | P18 regime source status and unresolved activation/15m bindings. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**` | P19 liquidity/PA source status and unresolved structure/15m bindings. |
| `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**` | P20 BBO source status and unresolved BBO/15m bindings. |
| `research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md` | P21 carried BBO fallback and cross-market cost-coverage context. |
| `tools/hooks/canary_runner.py` | Session-label guard and no-lookahead canary surface; passed in this phase with exit code `0`. |

## Audit Set Reconciliation

The audit set matches the P22 matrix exactly: six non-rejected
`diagnostic_survivors_for_consolidation` StudySpecs plus four retained
cross-market rejected-source StudySpecs. No additional StudySpec is added and no
P22 StudySpec is omitted.

| StudySpec id | Hash component | AlphaSpec id | Family | P22 role | P22 runtime status |
| --- | --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `dde3e64667fe158f9bad527d` | `aspec_0ebd90cecfd475607685b445` | `cross_market` | retained rejected-source context | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_c671fbeeb143512cbc03bc5b` | `c671fbeeb143512cbc03bc5b` | `aspec_8d9e272e4b78eedcd27f0bec` | `cross_market` | retained rejected-source context | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_90b28233d828128664588a9a` | `90b28233d828128664588a9a` | `aspec_a41dcccac5552de945aba825` | `cross_market` | retained rejected-source context | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_7c8fb13628843890c171b122` | `7c8fb13628843890c171b122` | `aspec_fa4895a43a80d4eef0a607a4` | `cross_market` | retained rejected-source context | `REJECTED_FOR_CROSS_MARKET_MISSINGNESS` |
| `sspec_69c22ec5847395ac8e81b5b6` | `69c22ec5847395ac8e81b5b6` | `aspec_b40aee52d4399dd5b855a6ed` | `vwap_session` | `diagnostic_survivor_for_consolidation` | `INCONCLUSIVE` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `aff70fcbc4b7ff226fcc8149` | `aspec_43cd6c154bca2fcc419eee83` | `vwap_session` | `diagnostic_survivor_for_consolidation` | `INCONCLUSIVE` |
| `sspec_267cc052e37668339c38d179` | `267cc052e37668339c38d179` | `aspec_eb962fc197eaf3955c5e4711` | `regime` | `diagnostic_survivor_for_consolidation` | `INCONCLUSIVE` |
| `sspec_27bf1262b0bd23d27191cc86` | `27bf1262b0bd23d27191cc86` | `aspec_df2d040e45564c259ef3de6d` | `liquidity_pa` | `diagnostic_survivor_for_consolidation` | `INCONCLUSIVE` |
| `sspec_02c400a561891171a33c0c66` | `02c400a561891171a33c0c66` | `aspec_39ffc190cfbfa6ba0b1a2a25` | `liquidity_pa` | `diagnostic_survivor_for_consolidation` | `INCONCLUSIVE` |
| `sspec_9f6f741192a4b534f06e51c0` | `9f6f741192a4b534f06e51c0` | `aspec_1284e49b083df11eeb0481ea` | `bbo_tradability` | `diagnostic_survivor_for_consolidation` | `INCONCLUSIVE` |

## Flag Semantics

`CLEARED` means the committed evidence supplies the requested timing control for
the audited surface. `FLAGGED` means a temporal-validity issue or unresolved
timing dependency is carried forward. A flag is not a promotion state, rejection
ledger entry, reviewer verdict, profitability claim, or tradability claim.

Allowed flags:

| Flag | Meaning in this audit |
| --- | --- |
| `LOOKAHEAD` | A required feature timing dependency is not cleared by a locked point-in-time FeaturePack, or a final-session aggregate boundary remains unproven for intraday use. |
| `LABEL_LEAKAGE` | A required label timing dependency is not cleared by a locked `label_available_ts` LabelPack, or label use as an input is not ruled out by committed evidence. |
| `SAME_BAR_OPTIMISM` | Decision/entry timing does not preclude same-bar outcome or realization-bar information. |
| `CROSS_INSTRUMENT_AVAILABILITY` | Cross-market legs are missing, late, stale, out-of-order, or otherwise unavailable at the primary decision time. |

## Common Timing Evidence

Locked FeaturePack refs in P03/P14 carry non-empty `available_ts` windows for
all consumed base OHLCV, rolling OHLCV, volume/activity, and session-context
features. Session-context refs `F1` and `F2` are treated as point-in-time
metadata under the `session_label` guard.

Locked LabelPack refs for `5m`, `10m`, and `30m` carry non-empty
`label_available_ts` windows and remain labels only:

| Label ref | Label id | Locked LabelVersion id | Availability result |
| --- | --- | --- | --- |
| `L5` | `fwd_ret_5m` | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` | `label_available_ts` after the fixed horizon; cleared for locked 5m use. |
| `L10` | `fwd_ret_10m` | `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` | `label_available_ts` after the fixed horizon; cleared for locked 10m use. |
| `L30` | `fwd_ret_30m` | `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` | `label_available_ts` after the fixed horizon; cleared for locked 30m use. |

The governed `15m` LabelSpec exists at
`research/futures_core_alpha_pilot_v1/label_specs/fwd_ret_15m.json` and records
`label_available_ts = max(terminal.available_ts, LabelSpec.availability_time)`,
`no_same_bar_terminal`, and `no_final_session_aggregate`. However, P17-P20 and
P22 record no locked materialized `15m` LabelPack for the audited survivor
matrix. Any idea that depends on the unresolved `15m` primary horizon is
therefore `FLAGGED` for `LABEL_LEAKAGE` until a locked LabelPack proves the
metadata by reference.

The P15 FeatureRequest records declare causal `available_ts` rules, but P17-P20
record unresolved locked FeaturePack bindings for VWAP/session, cross-market
derived-state, structure/regime/liquidity, and BBO confirmation groups. Those
unresolved bindings are carried as `LOOKAHEAD` flags for the affected ideas.

The canary surface passed in this phase:

| Command | Result |
| --- | --- |
| `python tools/hooks/canary_runner.py` | Passed, exit code `0`; all Frontier canaries passed, including future-shift, permuted-label, and optimistic-fill governance canaries. |

## Per-Idea Temporal Verdicts

| StudySpec | `available_ts` / final-aggregate check | `label_available_ts` / leakage check | Same-bar optimism check | Cross-instrument availability check | Session guard corroboration | Verdict | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sspec_dde3e64667fe158f9bad527d` | `CLEARED`: locked `F1`/`F2` carry `available_ts`; no final-session aggregate dependency is recorded for the locked 5m baseline. | `CLEARED`: locked `L5` primary label plus locked `L10`/`L30` refs carry `label_available_ts`; no 15m primary dependency for this StudySpec. | `CLEARED`: P16 records `same_bar_optimism_allowed=false`; no same-bar fill permission is recorded. | `FLAGGED`: P16/P22 record aligned snapshots `0`, observed required symbols `1` of `3`, and missing `NQ`/`RTY` legs. | `CLEARED`: `F1`/`F2` session refs are point-in-time and canaries passed. | `FLAGGED` | `CROSS_INSTRUMENT_AVAILABILITY` |
| `sspec_c671fbeeb143512cbc03bc5b` | `FLAGGED`: locked `F1`/`F2`/`F3`/`F4` carry `available_ts`, but P15-G3 cross-market derived-state FeaturePack is not locked in P16/P22 evidence. | `CLEARED`: declared primary `10m` label is locked with `label_available_ts`; no 15m primary dependency for this StudySpec. | `CLEARED`: P16 records `same_bar_optimism_allowed=false`; no same-bar fill permission is recorded. | `FLAGGED`: P16/P22 record aligned snapshots `0`, observed required symbols `1` of `3`, and missing `NQ`/`RTY` legs. | `CLEARED`: `F1`/`F2` session refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `CROSS_INSTRUMENT_AVAILABILITY` |
| `sspec_90b28233d828128664588a9a` | `FLAGGED`: locked `F1`/`F2`/`F3`/`F4` carry `available_ts`, but P15-G3 cross-market derived-state FeaturePack is not locked in P16/P22 evidence. | `FLAGGED`: declared primary `15m` horizon has a governed P15 LabelSpec but no locked materialized `15m` LabelPack in P16/P22 evidence. | `CLEARED`: P16 records `same_bar_optimism_allowed=false`; the P15 15m LabelSpec also records `no_same_bar_terminal`. | `FLAGGED`: P16/P22 record aligned snapshots `0`, observed required symbols `1` of `3`, and missing `NQ`/`RTY` legs. | `CLEARED`: `F1`/`F2` session refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE`, `CROSS_INSTRUMENT_AVAILABILITY` |
| `sspec_7c8fb13628843890c171b122` | `FLAGGED`: locked `F1`/`F2`/`F3`/`F4` carry `available_ts`, but P15-G3 cross-market derived-state FeaturePack is not locked in P16/P22 evidence. | `CLEARED`: declared primary `30m` label is locked with `label_available_ts`; no 15m primary dependency for this StudySpec. | `CLEARED`: P16 records `same_bar_optimism_allowed=false`; no same-bar fill permission is recorded. | `FLAGGED`: P16/P22 record aligned snapshots `0`, observed required symbols `1` of `3`, and missing `NQ`/`RTY` legs. | `CLEARED`: `F1`/`F2` session refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `CROSS_INSTRUMENT_AVAILABILITY` |
| `sspec_69c22ec5847395ac8e81b5b6` | `FLAGGED`: locked base/session refs carry `available_ts`, but P17/P22 record no locked running VWAP/session FeaturePack; active-session final VWAP remains forbidden intraday until a locked point-in-time pack proves the running/final boundary. | `FLAGGED`: locked `5m`/`10m`/`30m` labels clear, but the P22 survivor matrix includes unresolved `15m` primary horizon coverage with no locked materialized `15m` LabelPack. | `CLEARED`: StudySpec stopping rules forbid same-bar outcome information; locked labels are post-horizon labels only; optimistic-fill canary passed. | `CLEARED`: not a cross-market/relative-value StudySpec; no non-primary instrument input is required at a primary decision timestamp. | `CLEARED`: session-context refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE` |
| `sspec_aff70fcbc4b7ff226fcc8149` | `FLAGGED`: locked base/session refs carry `available_ts`, but P17/P22 record no locked VWAP/session FeaturePack; completed ETH context is allowed only after segment completion and active-session final aggregates remain forbidden intraday until locked evidence proves the boundary. | `FLAGGED`: locked `5m`/`10m`/`30m` labels clear, but the P22 survivor matrix includes unresolved `15m` primary horizon coverage with no locked materialized `15m` LabelPack. | `CLEARED`: StudySpec stopping rules forbid same-bar outcome information; locked labels are post-horizon labels only; optimistic-fill canary passed. | `CLEARED`: not a cross-market/relative-value StudySpec; no non-primary instrument input is required at a primary decision timestamp. | `CLEARED`: session-context refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE` |
| `sspec_267cc052e37668339c38d179` | `FLAGGED`: locked base/session/regime proxy refs carry `available_ts`, but P18/P22 record missing locked trendiness and activation binding under P15-G4. | `FLAGGED`: locked `5m`/`10m`/`30m` labels clear, but the P22 survivor matrix includes unresolved `15m` primary horizon coverage with no locked materialized `15m` LabelPack. | `CLEARED`: StudySpec stopping rules forbid same-bar outcome information; locked labels are post-horizon labels only; optimistic-fill canary passed. | `CLEARED`: not a cross-market/relative-value StudySpec; no non-primary instrument input is required at a primary decision timestamp. | `CLEARED`: session-context refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE` |
| `sspec_27bf1262b0bd23d27191cc86` | `FLAGGED`: locked base/session/liquidity proxy refs carry `available_ts`, but P19/P22 record unresolved objective trigger counts because no locked structure FeaturePack exposes the required trigger flags under P15-G4. | `FLAGGED`: locked `5m`/`10m`/`30m` labels clear, but the P22 survivor matrix includes unresolved `15m` primary horizon coverage with no locked materialized `15m` LabelPack. | `CLEARED`: StudySpec stopping rules forbid same-bar outcome information; locked labels are post-horizon labels only; optimistic-fill canary passed. | `CLEARED`: not a cross-market/relative-value StudySpec; no non-primary instrument input is required at a primary decision timestamp. | `CLEARED`: session-context refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE` |
| `sspec_02c400a561891171a33c0c66` | `FLAGGED`: locked base/session/liquidity proxy refs carry `available_ts`, but P19/P22 record unresolved objective trigger counts because no locked structure FeaturePack exposes the required trigger flags under P15-G4. | `FLAGGED`: locked `5m`/`10m`/`30m` labels clear, but the P22 survivor matrix includes unresolved `15m` primary horizon coverage with no locked materialized `15m` LabelPack. | `CLEARED`: StudySpec stopping rules forbid same-bar outcome information; locked labels are post-horizon labels only; optimistic-fill canary passed. | `CLEARED`: not a cross-market/relative-value StudySpec; no non-primary instrument input is required at a primary decision timestamp. | `CLEARED`: session-context refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE` |
| `sspec_9f6f741192a4b534f06e51c0` | `FLAGGED`: locked session refs carry `available_ts`, but P20/P22 record missing locked BBO FeaturePack under P15-G5; missing/quarantined quote rows must remain flags or gaps and cannot be filled. | `FLAGGED`: locked `5m`/`10m`/`30m` labels clear, but the P22 survivor matrix includes unresolved `15m` primary horizon coverage with no locked materialized `15m` LabelPack. | `CLEARED`: StudySpec stopping rules forbid same-bar outcome information; locked labels are post-horizon labels only; optimistic-fill canary passed. | `CLEARED`: not a cross-market/relative-value StudySpec; no non-primary instrument input is required at a primary decision timestamp. | `CLEARED`: session-context refs are point-in-time and canaries passed. | `FLAGGED` | `LOOKAHEAD`, `LABEL_LEAKAGE` |

## Flag Summary

| Failure mode | StudySpecs flagged | Audit basis |
| --- | --- | --- |
| `LOOKAHEAD` | `sspec_c671fbeeb143512cbc03bc5b`, `sspec_90b28233d828128664588a9a`, `sspec_7c8fb13628843890c171b122`, `sspec_69c22ec5847395ac8e81b5b6`, `sspec_aff70fcbc4b7ff226fcc8149`, `sspec_267cc052e37668339c38d179`, `sspec_27bf1262b0bd23d27191cc86`, `sspec_02c400a561891171a33c0c66`, `sspec_9f6f741192a4b534f06e51c0` | Required derived-state, VWAP/session, structure, activation, or BBO FeaturePack timing dependency not locked in committed P16-P22 evidence. |
| `LABEL_LEAKAGE` | `sspec_90b28233d828128664588a9a`, `sspec_69c22ec5847395ac8e81b5b6`, `sspec_aff70fcbc4b7ff226fcc8149`, `sspec_267cc052e37668339c38d179`, `sspec_27bf1262b0bd23d27191cc86`, `sspec_02c400a561891171a33c0c66`, `sspec_9f6f741192a4b534f06e51c0` | Required `15m` LabelPack timing dependency not locked in committed P16-P22 evidence. |
| `SAME_BAR_OPTIMISM` | none | P14 stopping rules, locked post-horizon labels, P16 same-bar metadata, the P15 15m LabelSpec rule, and the canary surface preclude same-bar outcome use in committed evidence. |
| `CROSS_INSTRUMENT_AVAILABILITY` | `sspec_dde3e64667fe158f9bad527d`, `sspec_c671fbeeb143512cbc03bc5b`, `sspec_90b28233d828128664588a9a`, `sspec_7c8fb13628843890c171b122` | P16/P22 cross-market diagnostics record zero aligned ES/NQ/RTY snapshots, observed required symbols `1` of `3`, and missing `NQ`/`RTY` legs. |

## Boundary Confirmation

- This report is value-free: it records ids, hash components, statuses, counts,
  flags, source paths, and metadata only.
- No raw provider file, provider response, row-level market value, feature
  value, label value, signal value, Parquet/Arrow/Feather payload, SQLite/DB
  payload, model binary, cache, log, or secret is embedded.
- No consumed primitive under `src/alpha_system/**` is edited or reinterpreted.
- No runtime diagnostic, cost stress, matrix consolidation, feature
  materialization, label materialization, broker/live/paper/order/deployment
  action, reviewer run, verdict, PR, merge, or promotion decision is performed.
- All flags are carried forward for downstream review; none is resolved or
  excused by this phase.
