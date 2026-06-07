# GOAL — ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

## Campaign Identity

- Campaign ID: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Campaign path: `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
- Repo: `alpha_system`
- Repo path: `~/projects/alpha_system`
- Workflow: `workflow2` (Ralph strict autonomous loop, `dag_wave` parallel build + serial merge)
- Project profile: `trading_research` / `research` / `core_alpha_pilot`
- Lane policy: Green/Yellow only; **no Red scope** in this campaign
- Phase count: 31 phases (`FUTCORE-P00` … `FUTCORE-P30`)

## Mission

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` is the **first small-but-real,
evidence-gated, cost-aware ES/NQ/RTY futures alpha research pilot** that drives
the completed **Data + Feature/Label + Research Runtime + Agent Factory** stack
through one full controlled research loop:

```text
Hypothesis -> AlphaSpec -> StudySpec -> Runtime diagnostics
  -> cost / session / regime / no-lookahead review
  -> TrialLedger / RejectedIdeaLedger
  -> REJECT | INCONCLUSIVE | WATCH | CANDIDATE_RESEARCH
```

It is **not** a search for "a strategy that makes money." It validates that the
real research operating system works end-to-end, that agents stay constrained,
that most ideas are rejected for clear reasons, and that the few survivors (if
any) carry reviewable, FactorLibrary-ready evidence into the next campaigns.

## North Star

Maximize robust out-of-sample, cost-adjusted, capacity-aware, low-correlation
intraday Sharpe, subject to drawdown, turnover, liquidity, execution, and
reproducibility constraints. In this pilot that north star is pursued only as
**diagnostics and evidence**, never as a tradability or profitability claim.

## Why This Campaign Exists Now

`PRE_CORE_ALPHA_DATA_ACCESS_HARDENING_V1` removed the last two pre-pilot
blockers, so continuing to build pure infra would be procrastination:

- `FEATURE_LABEL_PARQUET_SINK_V1` is complete — research-scale feature/label
  values flow through a Parquet sink; JSONL stays the audit/smoke/small tier;
  SQLite stays metadata/pointer/lineage/hash only.
- `SESSION_LABEL_GUARD_FIX_V1` is complete — the role-aware `session_label`
  guard false-positive is fixed, so point-in-time RTH/ETH/session-context
  features are usable.
- The Research Runtime real-data smoke passed on local Databento-backed Parquet
  feature/label values, and the Agent Factory preflight passed.

At the same time the pilot must stay **bounded**: Validation Governance V1,
FactorLibrary V1, Strategy Reference Validation, AlphaBook, and the Paper/Live
RED lane do **not** exist yet. This campaign is the one that surfaces the real
failure modes those later campaigns must address.

## What Prior Layers Already Provide (consumed, not rebuilt)

- **Data**: accepted Databento ES/NQ/RTY OHLCV-1m + BBO-1m + Definition/
  Statistics/Status metadata, canonical timestamps, `available_ts`,
  `exchange_trade_date`, `session_segment`, contract/continuous provenance, and
  quality/missingness flags — resolved through registry tools.
- **Feature/Label**: registry-resolved Parquet FeaturePacks and LabelPacks; dual
  JSONL+Parquet materialization; registries record `value_store_format`,
  `parquet_path`, `value_content_hash`, `value_schema_version`.
- **Research Runtime** (`src/alpha_system/runtime`): `input_resolver`,
  `tool_results` (`RuntimeToolResult`/`RuntimeRunSummary`), diagnostics
  (`cross_market`, `splits`, `label`), `cost`, `grid`, `probe`, `evidence`,
  `decisions`, `handoff`, `reports`, real-data `smoke`, `dry_run`.
- **Governance** (`src/alpha_system/governance`): `alpha_spec`, `study_spec`,
  `feature_request`, `label_spec`, `study_input_pack`, `trial_ledger`,
  `rejected_idea`, `evidence_bundle`, `promotion_gate`, `promotion`, `claims`,
  `registry`, canaries.
- **Agent Factory** (`src/alpha_system/agent_factory`): role contracts,
  permission matrix, research queue, records/memory, separation-of-duties
  wiring, tool contracts, bounded dry-run harness, and the runtime bridge.

## What Prior Layers Intentionally Did Not Provide

- True forward-looking labels remain **blocked**.
- No Validation Governance V1 (full DSR/PBO/PSR, purged/embargo, locked-test
  contamination system, ResearchGraveyard hardening).
- No FactorLibrary V1 promotion, Strategy Reference Validation, or AlphaBook.
- No Paper/Live/Broker/Order RED lane.

## What This Campaign Builds

Only **research evidence** (all value-free, commit-eligible under
`research/futures_core_alpha_pilot_v1/**`):

- AlphaSpec drafts, AlphaSpec critique records, approved AlphaSpecs
- minimal FeatureRequests / LabelSpecs (only if a gap is proven, ≤5)
- StudySpecs
- RuntimeRunSummaries / RuntimeToolResults references
- DiagnosticsReports, CostSensitivityReports, RegimeSplitReports,
  SessionSplitReports, CrossMarketDiagnosticsReports, NoLookaheadAuditReports
- TrialLedgerRecords, RejectedIdeaRecords
- EvidenceDrafts
- ReviewerVerdicts
- PromotionDecision records (`REJECT` | `INCONCLUSIVE` | `WATCH` |
  `CANDIDATE_RESEARCH`)
- FactorCard drafts / ReferenceCandidateHandoffs for survivors only
- failure-mode handoffs to Validation Governance / FactorLibrary / Strategy
  Reference

## What This Campaign Does NOT Build

- NOT scaled or autonomous alpha mining; NOT a continuous Research Runner
- NOT FactorLibrary V1; NOT Strategy Reference Validation; NOT AlphaBook
- NOT strategy production, paper trading, live trading, broker/order/execution
- NOT proof of profitability or tradability
- NOT ML/DL/RL; NOT L1/L2 event-stream; NOT portfolio construction
- NOT any edit to the consumed runtime/governance/agent_factory/research/
  experiments/backtest/data/core primitives (features/labels touched **only** in
  `FUTCORE-P15` via FeatureRequest/LabelSpec)

## Alpha Family Priorities (5 primary + 1 overlay)

| Family | Budget | Focus |
| --- | --- | --- |
| Cross-market / relative value | 40% | ES/NQ/RTY lead-lag, beta residual, rotation, confirmation/divergence; requires timestamp-alignment + cross-market missingness diagnostics |
| VWAP / session auction | 20% | VWAP reclaim/reject, distance-to-VWAP, opening range, overnight H/L, gap, RTH-open-vs-ETH; running vs final VWAP must be distinguished |
| Regime-gated momentum vs reversion | 15% | trendiness/volatility/range-compression regimes that **gate** momentum vs reversion (not a global choice) |
| Liquidity sweep / failed breakout / objective PA | 15% | sweeps, close-back-inside, wick rejection, displacement, compression breakout, failed-breakout reversal; objective computable rules only |
| BBO tradability / top-book confirmation | 10% | spread/microprice/imbalance/depth/quote-quality; primarily tradability/risk/confirmation evidence, not standalone edge |

**Overlay — Volume / activity / effort-vs-result**: no standalone family budget;
used only as an overlay inside VWAP/session, regime, liquidity, and BBO
diagnostics, and only where the repo already has volume/activity primitives. No
new volume feature zoo.

## Data / Feature / Label / Runtime Contract

- Universe in scope: **ES, NQ, RTY**. Deferred: MES/MNQ/M2K, rates, FX,
  commodities, vol products, options, equities, L1 eventstream, L2/L3.
- Inputs resolved only through registry tools and `resolve_dataset_version`; no
  raw provider reads, no external provider calls, no hand-read arbitrary paths.
- Research-scale scans use registry-resolved **Parquet** values; JSONL is only
  for audit/smoke/small tiers.
- Every feature has `available_ts`; every label has `label_available_ts`.
- Diagnostics run **only** through the Research Runtime tool surface
  (`RuntimeToolResult`/`RuntimeRunSummary`), never re-implemented in pilot code.

## Agent Workflow Contract

Constrained research workers (driven from the Agent Factory contracts, not
instantiated as autonomous traders): Research Director, Hypothesis Scout,
AlphaSpec Critic, Data Contract Auditor, Feature Engineer, Label Engineer,
No-Lookahead Auditor, Diagnostics Runner, Statistical Reviewer, Librarian.

Separation of duties: Hypothesis Scout cannot approve; Feature/Label Engineer
cannot review own implementation; Diagnostics Runner cannot promote; Statistical
Reviewer is independent of the implementer; Librarian cannot update durable
memory/registry without a reviewer verdict; **the human owns capital/live
judgment**.

## Cost / Session / Horizon Contract

- **Horizons**: 1m = sampling only; 1–3m = execution-fragile diagnostics with
  stricter spread/liquidity/cost gates; **5–30m = primary pilot zone**; 30m–4h =
  valid extended intraday with stronger sample/overlap/regime/stability checks;
  session-close/maintenance-flat valid. Hard boundary: no position crosses the
  exchange daily maintenance / trade-date break.
- **Sessions**: full_session, RTH_only, ETH_only, ETH_evening, ETH_overnight,
  pre_RTH, RTH, post_RTH, RTH_with_ETH_context; required outputs include the
  session × horizon matrix and spread/depth/volatility/quote-quality splits.
- **Cost**: three layers (hard transaction cost; spread crossing via BBO; bucketed
  slippage proxy) under profiles `zero_cost` (diagnostic only),
  `base`, `stress_1`, `stress_2`, `double_cost`, with thin-session penalties for
  ETH/pre_RTH/post_RTH. **Zero-cost is never a promotion basis.**

## Allowed Outputs

See "What This Campaign Builds." All outputs are value-free research evidence.

## Forbidden Outputs

`VALIDATED_RESEARCH`, `LIVE_APPROVED`, `PAPER_APPROVED`, `PRODUCTION_READY`,
`CAPITAL_ALLOCATED`, `PROFITABLE`, `TRADABLE`, `STRATEGY_READY`,
`PORTFOLIO_READY`; final FactorLibrary promotion; final Strategy Reference
validation; broker/live/paper/order code; capital allocation; any production
trading claim.

## Success Criteria

The campaign succeeds if:

- the real research loop runs end-to-end and agents remain constrained;
- most ideas are **rejected** with clear, recorded reasons;
- data/feature/label/runtime/governance gates hold;
- diagnostics are reviewable, with cost/session/horizon/regime outputs;
- TrialLedger and RejectedIdeaLedger are populated (failures visible);
- **0–2** ideas at most reach `WATCH` or `CANDIDATE_RESEARCH`, each with an
  independent reviewer verdict;
- concrete failure-mode handoffs are produced for the next campaigns.

**Zero surviving ideas is acceptable** if the rejection/evidence loop is healthy.

## Closeout Handoffs

`FUTCORE-P29` produces concrete, failure-mode-driven requirement handoffs to:

- `ALPHA_VALIDATION_GOVERNANCE_V1` — full DSR/PBO/PSR, purged/embargo, locked-test
  contamination, ResearchGraveyard hardening, derived from real pilot failures.
- `ALPHA_FACTOR_LIBRARY_V1` — FactorCard/EvidenceBundle ingestion of survivors.
- `ALPHA_STRATEGY_REFERENCE_VALIDATION_V1` — Reference-truth validation of any
  candidate (this pilot only hands off candidates; it never validates them).

## Boundaries Summary

```text
Data ≠ Feature ≠ Factor ≠ Signal ≠ Strategy ≠ Portfolio ≠ Execution
Fast path ≠ Reference truth
Validated research ≠ paper/live approval
Candidate ≠ capital allocation
Agent ≠ autonomous trader ≠ self-reviewer ≠ self-promoter
```

This is the campaign **goal contract**. The executable per-phase contracts live
in `PHASE_PLAN.md` and `campaign.yaml`; acceptance in `ACCEPTANCE.md`; risks in
`RISK_REGISTER.md`; operations in `RUNBOOK.md`.
