# ALPHA_FEATURE_LABEL_FOUNDATION_V1 Campaign Goal

## Campaign Identity

**ALPHA_FEATURE_LABEL_FOUNDATION_V1 — The Versioned, No-Lookahead-Safe Research Substrate for AI Alpha Researchers**

* **Campaign ID:** `ALPHA_FEATURE_LABEL_FOUNDATION_V1`
* **Campaign name:** Feature/Label Foundation: Versioned, No-Lookahead-Safe Research Substrate
* **Campaign path:** `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1`
* **Repo name:** `alpha_system`
* **Repo path:** `~/projects/alpha_system`
* **Host environment:** Windows host
* **Primary runtime:** WSL2 Ubuntu
* **Required active filesystem location:** WSL2 Linux filesystem under `~/projects/alpha_system`
* **Forbidden active worktree locations:** `/mnt/c`, `/mnt/d`, `/mnt/e`, OneDrive, Dropbox, Google Drive, Windows-synced folders, network drives, temporary directories
* **Project profile:** `trading_research` / `research` / `feature_label_foundation`
* **Campaign execution mode:** Frontier Harness Generic v3.0 Workflow 2 with the DAG wave scheduler
* **Campaign driver:** Ralph strict autonomous loop
* **Scheduler mode:** `dag_wave` (parallel build, serial merge queue)
* **Primary executor:** Codex GPT-5.5 high
* **Primary semantic reviewer:** Claude Opus 4.8 xhigh
* **Verifier / source-map / audit support:** Claude Sonnet 4.6
* **Strategic campaign reasoning:** ChatGPT Pro GPT-5.5 Thinking
* **Phase count:** 32 phases (`FLF-P00` … `FLF-P31`)

This campaign is **contract generation and substrate construction only**. It defines, designs,
and (where local-only and authorized) implements the Feature/Label substrate. It does **not**
implement alpha research, does **not** materialize committed feature/label values, does **not**
run alpha search, does **not** call Databento or IBKR, and does **not** pull or commit raw,
canonical, feature, or label data.

## Mission

Build the **versioned, no-lookahead-safe, deduplicated, cost-aware, BBO-aware research
substrate** — a governed FeatureStore and LabelStore over **accepted DatasetVersions** — that
future AI Alpha Researchers consume.

This campaign is the **research substrate layer**. It is the bridge from an
`accepted DatasetVersion` to a `research-ready FeatureStore / LabelStore substrate` that future
agents reference through a StudySpec. It is not just feature engineering and it is not just
label construction: it is the governed, point-in-time-safe substrate beneath all later alpha
search.

One sentence captures the posture:

```text
A feature is not alpha; a label is not alpha; a FeatureStore is not a factor library;
a materialized FeatureSet is not a promoted candidate; a good diagnostic is not production readiness.
```

The critical framing is stated explicitly and must hold everywhere in this campaign:

```text
A feature is not alpha.
A label is not alpha.
A FeatureStore is not a factor library.
A materialized FeatureSet is not a promoted candidate.
A good diagnostic is not production readiness.
DatasetVersion accepted does not imply alpha validated.
Feature/Label Foundation prepares research substrate; it does not conduct alpha search.
```

## Why This Campaign Exists

The strategic ordering of the program is precise and deliberate:

```text
ALPHA_SYSTEM_V1                made the system able to run.
ASV1_RELEASE_HYGIENE           made the V1 release baseline clean and reviewable.
ALPHA_RESEARCH_GOVERNANCE_MVP  decided what research results are allowed to be believed.
ALPHA_DATA_FOUNDATION_V1       let real market truth enter — controlled, versioned, read-only.
ALPHA_FEATURE_LABEL_FOUNDATION_V1  turns accepted DatasetVersions into a governed research substrate.
```

`alpha_system` is becoming an **AI Alpha Research Factory**, not a backtester and not a strategy
repository. The long-term north star is an AI-driven, evidence-gated, cost-aware intraday alpha
factory that continuously discovers, validates, combines, monitors, deweights, and retires
alphas under strict point-in-time and reproducibility rules. The long-term objective — used here
only for framing, never as a claim — is to maximize robust out-of-sample, cost-adjusted,
capacity-aware, low-correlation intraday Sharpe, subject to drawdown, turnover, liquidity,
execution, and reproducibility constraints. In that factory:

* AI generates research throughput.
* `alpha_system` owns evidence and truth.
* Ralph / Workflow 2 owns process and gates.
* Claude reviews semantics and runs done-checks.
* Codex implements scoped phase specs.
* The human owns direction and risk/capital judgment.

Governance now exists, and a real, versioned, quality-gated data foundation now exists. Before
real alpha search, an Agent Factory, Futures Core Alpha, an AlphaBook, or any broker work, the
system needs a **research substrate** that converts accepted DatasetVersions into features and
labels that are reproducible, point-in-time safe, deduplicated, cost-aware, and governed.

This campaign exists to **prevent** the failure modes that destroy intraday research quality:

```text
raw-data feature hacking          (features read provider files directly)
feature dumping ground            (an unbounded, ungoverned FeatureStore)
duplicate factor zoo              (the same exposure re-encoded many times)
label leakage factory             (labels that leak future information into features)
cost-unaware backtest factory     (returns labels with no spread/cost adjustment)
unversioned materialization mess  (values with no FeatureVersion / LabelVersion lineage)
agent-specific feature code       (per-agent implementations that bypass governance)
```

Each is a known way that an AI research loop manufactures convincing but false evidence. The
Feature/Label Foundation installs the governed substrate that makes those failure modes
unreachable by construction.

## Baseline from Completed Campaigns

The following campaigns are treated as **complete** and form this campaign's baseline:

* `ALPHA_SYSTEM_V1` — local-first research harness foundation.
* `ASV1_RELEASE_HYGIENE` — clean, reviewable V1 release baseline with validation gates.
* `ALPHA_RESEARCH_GOVERNANCE_MVP` (COMPLETE_WITH_WARNINGS) — the admissibility/evidence protocol:
  `AlphaSpec`, `FeatureRequest`, `LabelSpec`, `StudySpec`, and the hard rules *no-code-before-spec*,
  *no-candidate-without-evidence*, and *no-promotion-without-ledger*. This governance layer is
  **fully built** and must be **consumed, not duplicated** (R-022).
* `ALPHA_DATA_FOUNDATION_V1` (25/25 phases, PASS_WITH_WARNINGS) — the read-only,
  provenance-rich, quality-gated data truth layer; the DatasetVersion registry; canonical
  records; partitions; and the sanctioned consumption API.
* IBKR read-only recent-validation path.
* Databento ES/NQ/RTY OHLCV + BBO + metadata deep-history ingestion (27 local-only Databento
  DatasetVersions + 2 IBKR DatasetVersions).
* `PRE_FEATURE_REPO_CONSOLIDATION_V1` — pre-Feature/Label repo consolidation.
* `WF2_PARALLEL_DAG_SCHEDULER_MVP` — the opt-in DAG wave scheduler (parallel build, serial merge)
  this campaign runs under.

**Dependency warnings:** the SHARED FACTS record `WF2_PARALLEL_DAG_SCHEDULER_MVP` as merged to
`main` (PR #110); if that DAG-scheduler merge or any baseline item is found not-on-`main` at run
time, treat it as a dependency warning and proceed only against the on-`main` state — but the
campaign contract itself is still valid and may still be generated. The data corpus
(27 Databento + 2 IBKR DatasetVersions) is **local-only**; its absence in a clean checkout is
expected and is not a contract blocker, because this campaign consumes accepted DatasetVersions
through the registry rather than committing the data.

That baseline deliberately did **not** provide a features package, canonical input views,
feature/label contract objects, transform/window/normalization primitives, feature families,
label families, materialization engines, a FeatureStore/LabelStore, quality/coverage reports,
leakage/availability audits, diagnostics, or a StudySpec Input Pack. This campaign supplies
exactly that missing substrate.

## Data Posture

* The Feature/Label layer consumes **accepted DatasetVersions only**, never raw provider files.
* A DatasetVersion is **admissible** when its lifecycle state is in `{VERSIONED, READY_FOR_RESEARCH}`
  with non-blocking quality and coverage. DatasetVersion ids use the `dsv_<source>_...` format
  (e.g. `dsv_databento_ohlcv_<hex>`, `dsv_databento_bbo_<hex>`,
  `dsv_databento_ohlcv_dense_<year>_v1`, `dsv_ibkr_es_nq_rty_eth_20260603_v1`,
  `dsv_ibkr_es_dated_202404_validation_v1`).
* The sanctioned consumption API is
  `alpha_system.data.foundation.version_registry.resolve_dataset_version(registry_path, id)`,
  returning DatasetVersion metadata. Records are built via `CanonicalBarRecord.from_mapping`,
  `CanonicalBBORecord.from_mapping`, and `DenseGridBarRecord.from_mapping`. The locked-partition
  gate is `require_governance_metadata_for_locked_partition_use(...)`. The registry path is
  local-only at `$ALPHA_DATA_ROOT/registry/datasets.sqlite`.
* It is **forbidden** for any feature/label code to read `.dbn`, `.zst`, parquet, arrow, feather,
  or provider files directly. Canonical records only.
* **Partitions:** development `2018-01-01 .. 2022-12-31`; validation `2023-01-01 .. 2024-12-31`;
  locked_test_candidate `2025-01-01 .. as_of_run`; latest_shadow_candidate optional. Use of the
  locked-test partition requires governance contamination metadata.
* Raw, canonical, feature, and label values are **local-only** and never committed. The suggested
  data root is outside the repo (e.g. `~/alpha_data/alpha_system`) configured via `ALPHA_DATA_ROOT`.
* This campaign makes **no external provider calls**. The data is already pulled.

### Canonical records consumed

* **CanonicalBarRecord** — `instrument_id`, `contract_id`, `series_id`, `bar_start_ts`,
  `bar_end_ts`, `event_ts`, `available_ts`, `ingested_at`, `open`, `high`, `low`, `close`,
  `volume`, `source`, `source_request_id`, `data_version`, `quality_flags`, `session_label`.
  `available_ts` is **the** no-lookahead "available" field (`available_ts >= bar_end_ts` enforced;
  `ingested_at != available_ts`). A missing minute means **no trade** — sparse OHLCV is the truth.
* **CanonicalBBORecord** — `bid`, `ask`, `bid_size`, `ask_size`, `mid`, `spread`,
  optional `spread_ticks`, `microprice`, `bid_order_count`, `ask_order_count`. Enforced:
  `mid == (bid + ask) / 2`, `spread == ask - bid`, `ask >= bid`, `available_ts >= bar_end_ts`,
  `bid <= microprice <= ask`. Quality-flag tokens in `quality_flags`: `missing_bbo` (the
  missing/bad-quote flag) and `bbo_quarantined` (crossed/abnormal, non-blocking). There is **no**
  `bad_quote_flag` column by that literal name.
* **DenseGridBarRecord** — adds `has_trade` (bool), `synthetic` (bool), `fill_method` (str|None),
  `provider_bar_ref` (str|None). No-trade synthetic rows carry `has_trade=False`,
  `synthetic=True`, `fill_method="previous_close"`, `volume==0`, the `no_trade` quality flag, and
  `provider_bar_ref=None`. Synthetic rows must **never** be treated as trade bars.

## Databento / IBKR Provider Roles

* **Databento is the primary deep-history research source.** GLBX.MDP3, ES/NQ/RTY,
  OHLCV-1m + BBO-1m + Definition / Statistics / Status. This is the deep-history research corpus
  the feature/label substrate is built to consume.
* **IBKR is a broker-source, recent-validation-only DatasetVersion path.** It is never a primary
  alpha source and is never an execution venue in this campaign.
* The Feature/Label Foundation consumes **accepted DatasetVersions**, not raw Databento/IBKR data.
* **Databento and IBKR DatasetVersions are never merged.** They remain distinct provenance lines.
* No external Databento or IBKR provider call occurs in this campaign; raw provider data is
  local-only and is read only through the canonical record loaders behind the sanctioned API.

## Workflow 2 DAG-Wave Execution Posture

This campaign runs under **Workflow 2 with the DAG wave scheduler**. The strict state order is:

```text
RUN_INIT -> CAMPAIGN_LOAD -> PHASE_SELECT -> SPEC_GENERATE -> SPEC_VALIDATE -> WORKTREE_CREATE ->
CODEX_EXECUTE -> CHECKS_RUN -> HANDOFF_VALIDATE -> CLAUDE_REVIEW -> VERDICT_PARSE -> PR_CREATE ->
CI_WAIT -> MERGE_GATE -> MERGE -> DONE_CHECK -> NEXT_PHASE -> CAMPAIGN_DONE_CHECK -> RUN_SUMMARY
```

Scheduler configuration:

```text
workflow2.scheduler.mode:              dag_wave
workflow2.scheduler.parallel_execution: true
workflow2.scheduler.max_parallel_phases: 3
workflow2.scheduler.merge_queue:        serial
workflow2.scheduler.update_active_campaign: coordinator_only
```

* Parallel-safe phases build **concurrently** in isolated worktrees; merge is always **serial**,
  one PR at a time, through the serial merge queue.
* A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares **disjoint**
  `allowed_paths`, sets `must_run_alone: false`, declares no global/coordinator file, and is not
  RED. If a phase lacks explicit `allowed_paths` or `parallel_safe: true`, it **runs alone**.
* Phase branches **never** write `ACTIVE_CAMPAIGN.md` in parallel mode; the pointer is
  coordinator-owned (`update_active_campaign: coordinator_only`).
* Run `just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1` (read-only plan-dag) and
  `just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3` (mock) before the first
  live parallel run; the live run is `just frontier-run-parallel ALPHA_FEATURE_LABEL_FOUNDATION_V1 3`.

Lanes:

* **GREEN** — low-risk docs/mechanical work, no Claude review required, auto PR + auto merge.
* **YELLOW** — material Feature/Label engineering and research-substrate work; requires fresh
  Claude Opus review with a `verdict.json` (`PASS` / `PASS_WITH_WARNINGS` to merge), auto merge
  after review. Most phases are YELLOW.
* **RED** — external, destructive, live, production, or broker-adjacent operations.
  **This campaign has no RED-lane phases**; the data is already pulled, so the Feature/Label
  layer only consumes local accepted DatasetVersions. The RED definition is retained for harness
  completeness only.

### Wave shape

```text
Wave 0  — Sequential bootstrap and core contracts (run-alone): FLF-P00 … FLF-P07.
Wave 1  — Parallel feature families (disjoint allowed_paths): FLF-P08, FLF-P09, FLF-P10, FLF-P11, FLF-P12.
Wave 2  — Sequential feature integration (run-alone): FLF-P13, FLF-P14, FLF-P15.
Wave 3  — Label contracts FLF-P16 (run-alone) then parallel label families: FLF-P17, FLF-P18, FLF-P19, FLF-P20.
Wave 4  — Sequential label integration (run-alone): FLF-P21, FLF-P22, FLF-P23.
Wave 5  — Partial-parallel diagnostics / fixtures / governance / docs: parallel FLF-P24, FLF-P25, FLF-P27, FLF-P29; run-alone FLF-P26, FLF-P28.
Wave 6  — Sequential dry run and closeout (run-alone): FLF-P30, FLF-P31.
```

After the canonical input layer (FLF-P03/FLF-P04 inputs and FLF-P06/FLF-P07 contracts and
primitives), the **feature track** and the **label track** fan out and interleave. Waves are
computed by the DAG scheduler from dependencies plus DAG metadata, not hard-coded; the lists
above are the intended shape, and `just frontier-plan` previews the exact waves.

## What This Campaign Builds

Across 32 Workflow 2 phases (`FLF-P00` … `FLF-P31`) the campaign defines, designs, and
(where local-only and authorized) implements:

* **Campaign bootstrap and entry contract** (FLF-P00 … FLF-P02): the docs root, the single
  sanctioned DatasetVersion consumption adapter, and the importable features package skeleton +
  naming conventions, with the existing `labels/` package extended additively via a `families/`
  subpackage.
* **Canonical input layer** (FLF-P03 … FLF-P04): provider-agnostic, no-lookahead OHLCV/BBO input
  views keyed off `available_ts`, plus dense-grid / no-trade / BBO-missingness semantics that
  flag synthetic rows and missing/abnormal quotes without silent forward-fill.
* **Feature contracts** (FLF-P05 … FLF-P07): the FeatureRequest gate and duplicate-exposure guard
  wired to governance; the FeatureSpec/FeatureVersion contract family; and the shared
  transform/window/normalization primitives.
* **Feature families** (FLF-P08 … FLF-P12, parallel): Base OHLCV, BBO tradability, Session /
  Calendar / Roll, Cross-Market ES/NQ/RTY, and Liquidity Sweep / Structure primitive families,
  each additive in disjoint family directories.
* **Feature materialization** (FLF-P13 … FLF-P15): the feature materialization engine, the
  FeatureStore / FeatureRegistry integration (local-only), and the feature quality and coverage
  reports.
* **Label contracts and families** (FLF-P16 … FLF-P20): LabelSpec/LabelVersion contracts bound to
  governance, then the fixed-horizon/midprice, cost-adjusted/spread-adjusted, path
  (MFE/MAE/triple-barrier), and strategy-agnostic event label families (FLF-P17 … FLF-P20
  parallel).
* **Label materialization** (FLF-P21 … FLF-P23): the label materialization engine, the
  LabelStore / LabelRegistry integration (local-only), and the label leakage and availability
  audits.
* **Diagnostics, fixtures, governance integration, and tooling** (FLF-P24 … FLF-P29):
  descriptive, non-promotional Feature/Label diagnostics; synthetic fixtures and fail-closed
  tests; a small real Databento DatasetVersion dry run; the StudySpec Input Pack governance
  integration; the CLI / tooling surface; and durable docs, templates, and the agent guide.
* **Closeout** (FLF-P30 … FLF-P31): the end-to-end Feature/Label dry run and the Workflow 2
  acceptance audit and closeout.

### Required feature objects to name

`FeatureRequest`, `FeatureSpec`, `FeatureFamily`, `FeatureInputSpec`, `TransformSpec`,
`WindowSpec`, `NormalizationSpec`, `FeatureSetSpec`, `FeatureMaterializationPlan`,
`FeatureValueRecord`, `FeatureVersion`, `FeatureRegistryRecord`, `FeatureStore`,
`FeatureLineageRecord`, `FeatureQualityReport`, `FeatureCoverageReport`,
`DuplicateExposureReport`, `EquivalentFeatureGroup`, `FeatureDeprecationRecord`,
`BBOFeatureSpec`, `SpreadFeatureSpec`, `MicropriceFeatureSpec`, `TopBookImbalanceFeatureSpec`,
`LiquidityQualityFeatureSpec`. The features-package `FeatureSetSpec` must avoid colliding with
the pre-existing non-governance `FeatureSetSpec` in `experiments/feature_sets.py`.

### Required label objects to name

`LabelSpec`, `LabelFamily`, `LabelInputSpec`, `LabelHorizonSpec`, `LabelPathSpec`, `BarrierSpec`,
`CostAdjustmentSpec`, `LabelMaterializationPlan`, `LabelValueRecord`, `LabelVersion`,
`LabelRegistryRecord`, `LabelStore`, `LabelLineageRecord`, `LabelQualityReport`,
`LabelCoverageReport`, `LabelLeakageAuditReport`, `LabelAvailabilityPolicy`.

### Feature families

* **Base OHLCV:** returns, log returns, rolling volatility, rolling range, ATR, volume z-score,
  rolling volume, session minute, RTH/ETH flags, opening range, overnight range, VWAP, anchored
  VWAP, distance to VWAP, range position, trendiness.
* **BBO / tradability:** mid, spread, spread_ticks, spread_bps, spread_zscore, bid size, ask
  size, top_book_depth, top_book_imbalance, microprice, microprice_minus_mid, missing_bbo_flag,
  bad_quote_flag, wide_spread_flag, low_depth_flag.
* **Cross-market ES/NQ/RTY:** synchronized ES/NQ/RTY returns, NQ-minus-ES return spread,
  RTY-minus-ES return spread, rolling beta residual, rolling correlation, confirmation/divergence
  flags, risk-on/risk-off rotation proxies.
* **Session / roll / calendar:** session_id, minutes_from_rth_open, minutes_to_rth_close,
  ETH/RTH segment, day_of_week, roll proximity, expiration proximity, status/halt flags.
* **Liquidity / structure primitives:** prior high/low distance, opening range high/low distance,
  sweep high/low flags, failed breakout flags, close location value, wick rejection score,
  compression / range contraction.

### Label families

`fwd_ret_1m/3m/5m/10m/30m`; `mid_fwd_ret_1m/3m/5m/10m/30m`; `cost_adjusted_fwd_ret`;
`spread_adjusted_fwd_ret`; `MFE`; `MAE`; `target_before_stop`; `triple_barrier`;
`breakout_success`; `return_to_vwap`; and a `liquidity_quality_future` label if appropriate.

## What This Campaign Does Not Build

This campaign must not implement or require any of the following:

* no alpha discovery, factor search, strategy research, backtest research, or portfolio
  allocation;
* no promotion of any feature, label, FeatureSet, or LabelSet into a candidate or strategy;
* no Agent Factory, Futures Core Alpha, AlphaBook, or validation-governance work beyond consuming
  existing governance objects;
* no order placement, account trading, position polling, broker execution, or order routing;
* no paper trading, live trading, real-time signal generation, or production execution adapter;
* no external Databento or IBKR provider call; no raw provider data access from feature/label code;
* no L2 depth, MBO, event-stream ingestion, or tick-data ingestion;
* no ML/DL training beyond authorized scope;
* no committed feature values, label values, raw/canonical data, provider responses, heavy
  artifacts, or local registries/DBs;
* no profitability, tradability, alpha-validity, strategy-readiness, paper-readiness,
  live-readiness, broker-readiness, or production-readiness claims.

## Feature Hard Rules

* **No raw-data feature hacking.** Feature code consumes accepted DatasetVersions only, through
  the sanctioned consumption adapter and canonical input views. No feature reads provider files.
* **No FeatureRequest, no feature.** Every feature traces to an approved governance
  `FeatureRequest` (`freq_`). `BLOCKED_DUPLICATE` / `NEEDS_REVIEW` / `PENDING` block
  implementation; only `APPROVED` proceeds.
* **No FeatureSpec, no feature values.** A `FeatureSpec` is required before any feature value is
  computed, and every `FeatureValueRecord` carries `available_ts`.
* **No future or centered live windows.** Causal windows only for live features; centered/future
  windows are offline-only and unavailable to live-feature contracts.
* **No dumping ground.** Duplicate or equivalent exposure is checked against the governance
  duplicate-exposure guard and recorded via `DuplicateExposureReport` / `EquivalentFeatureGroup`;
  the FeatureStore is governed, not unbounded.
* **Governance is consumed, not duplicated (R-022).** `FeatureRequest` and the duplicate-exposure
  guard come from `alpha_system.governance`; the feature layer adapts them.
* **BBO missingness is flagged, never silently filled.** The `missing_bbo` and `bbo_quarantined`
  tokens drive feature handling; synthetic no-trade rows are never treated as trade bars.
* **Feature values are local-only.** Materialized values, the FeatureStore, and the
  FeatureRegistry are never committed.

## Label Hard Rules

* **No label leakage factory.** A label is never exposed as a live feature; `forbidden_feature_overlap`
  and the `label_leakage_guard` are enforced. The leakage checks include `label_as_feature` and
  `availability_time`.
* **No LabelSpec, no label values.** A governance `LabelSpec` (`lspec_`) is required before any
  label value is computed, and every `LabelValueRecord` carries `label_available_ts`.
* **Future data is legal only for labels.** Forward-looking horizons are the defining property of
  labels; they are never permitted in features.
* **Cost awareness is mandatory.** Cost-adjusted and spread-adjusted labels are first-class,
  driven by the LabelSpec `cost_model` and `CostAdjustmentSpec`; a raw return label without a
  cost-aware companion is not a complete label set.
* **Availability is governed.** `LabelAvailabilityPolicy` and `availability_time` ensure label
  availability semantics are explicit and audited; `target_stop_rules` and `path_rules` are
  contract-bound.
* **Governance is consumed, not duplicated (R-022).** `LabelSpec` and `label_leakage_guard` come
  from `alpha_system.governance`; the label layer adapts them and does not edit the existing
  `labels/*.py` modules destructively.
* **Label values are local-only.** Materialized values, the LabelStore, and the LabelRegistry are
  never committed; leakage and availability audits must pass before a label is registered.

## BBO / Tradability Scope

The Feature/Label Foundation includes the first full-history L1-lite **tradability** layer over
BBO, treated as research substrate and never as an executable-quote or order surface:

* BBO features are allowed and consume `CanonicalBBORecord` fields: `bid`, `ask`, `bid_size`,
  `ask_size`, `mid`, `spread`, optional `spread_ticks`, `microprice`, `bid_order_count`,
  `ask_order_count`.
* Missing/bad quotes are flagged with the `missing_bbo` token; crossed/abnormal quotes are flagged
  `bbo_quarantined` (non-blocking). There is **no silent forward-fill**.
* `microprice` requires valid bid/ask sizes; the `bid <= microprice <= ask` invariant holds.
* Spread/cost fields (`spread`, `spread_ticks`, `spread_bps`) are required so labels can be
  cost-adjusted; the BBO tradability features feed but do not constitute cost-adjusted labels.
* Tradability features are descriptive substrate. They make **no** claim that any instrument,
  minute, or quote is tradable, executable, or live-ready. The required BBO feature contract
  objects to name are `BBOFeatureSpec`, `SpreadFeatureSpec`, `MicropriceFeatureSpec`,
  `TopBookImbalanceFeatureSpec`, and `LiquidityQualityFeatureSpec`.

## DatasetVersion Entry Contract

The single sanctioned entry path is established in FLF-P01 and consumed by every later phase:

```text
resolve_dataset_version(registry_path, id) -> DatasetVersion (metadata, accepted-only)
CanonicalBarRecord.from_mapping(...)        -> CanonicalBarRecord
CanonicalBBORecord.from_mapping(...)        -> CanonicalBBORecord
DenseGridBarRecord.from_mapping(...)        -> DenseGridBarRecord
require_governance_metadata_for_locked_partition_use(...)  -> locked-partition gate
```

* Admissibility: the DatasetVersion lifecycle state must be in `{VERSIONED, READY_FOR_RESEARCH}`
  with non-blocking quality and coverage.
* No feature/label code may read `.dbn`, `.zst`, parquet, arrow, feather, or any provider file.
  Canonical records only.
* Databento and IBKR DatasetVersions are never merged.
* Locked-test partition use requires governance contamination metadata, recorded through
  `require_governance_metadata_for_locked_partition_use`.
* The registry path is local-only at `$ALPHA_DATA_ROOT/registry/datasets.sqlite`; the registry and
  all data remain local-only and uncommitted.

## Feature/Label Lifecycle Model Summary

The lifecycle states below are the contract the Feature/Label objects must enforce. They are
listed here as the contract Workflow 2 phases implement; Ralph itself does not execute the
lifecycle.

```text
Feature lifecycle:
  REQUESTED
  -> SPEC_DRAFTED
  -> SPEC_VALIDATED
  -> IMPLEMENTATION_ALLOWED
  -> IMPLEMENTED
  -> MATERIALIZATION_PLANNED
  -> MATERIALIZED_DRAFT
  -> QUALITY_CHECKED
  -> REGISTERED
  -> READY_FOR_STUDY
  Any state -> REJECTED | QUARANTINED | DEPRECATED
```

```text
Label lifecycle:
  LABEL_REQUESTED
  -> LABEL_SPEC_DRAFTED
  -> LABEL_SPEC_VALIDATED
  -> MATERIALIZATION_ALLOWED
  -> MATERIALIZED_DRAFT
  -> LEAKAGE_AUDITED
  -> QUALITY_CHECKED
  -> REGISTERED
  -> READY_FOR_STUDY
  Any state -> REJECTED | QUARANTINED | DEPRECATED
```

The terminal research-substrate state is `READY_FOR_STUDY` — meaning the feature or label is ready
to be referenced by a StudySpec, **not** that any alpha is validated.

**Prohibited MVP states (must never be reachable by any transition implemented in this campaign):**

```text
ALPHA_VALIDATED
STRATEGY_READY
LIVE_READY
PROFITABLE
TRADABLE
PRODUCTION_READY
```

These are named only as future, non-MVP concepts. No feature or label may reach them in this
campaign. `READY_FOR_STUDY` is the most advanced state any object may reach.

## Success Definition

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` succeeds when:

1. The Feature/Label layer consumes only accepted DatasetVersions via `resolve_dataset_version`
   and never reads raw provider files.
2. Canonical OHLCV/BBO input views key strictly off `available_ts`, and dense-grid/no-trade and
   BBO-missingness semantics flag synthetic rows and bad quotes with no silent forward-fill.
3. The FeatureRequest gate and duplicate-exposure guard are wired to governance (not
   re-implemented), so no feature exists without an approved `FeatureRequest` and a recorded
   duplicate/equivalent-exposure check.
4. `FeatureSpec`/`FeatureVersion` and `LabelSpec`/`LabelVersion` contracts exist; every feature
   value carries `available_ts` and every label value carries `label_available_ts`.
5. Five feature families and four label families (plus an optional `liquidity_quality_future` label)
   are implemented additively in disjoint directories, unit-tested on synthetic fixtures, with no
   shared-core or cross-family edits.
6. Feature and label materialization engines, the FeatureStore/LabelStore, and their registries
   exist as local-only substrate, with quality/coverage reports and leakage/availability audits.
7. No label is exposed as a live feature; no future/centered window is used as a live feature;
   future data is legal only for labels.
8. The StudySpec Input Pack integrates additively with existing governance without modifying the
   StudySpec schema or governance modules.
9. Diagnostics are descriptive and non-promotional; a small local-only Databento DatasetVersion
   dry run and the end-to-end dry run pass or record a truthful `PASS_WITH_WARNINGS`.
10. No feature/label values, raw/canonical data, provider responses, heavy artifacts, or local DBs
    are committed; `git ls-files runs` is empty; explicit staging is used throughout.
11. DAG metadata is correct: parallel-safe phases have disjoint `allowed_paths`, no phase branch
    writes `ACTIVE_CAMPAIGN.md` in parallel mode, and merge proceeds serially.
12. No alpha, profitability, tradability, strategy, paper, live, broker, or production-readiness
    claim is introduced anywhere, and no prohibited MVP lifecycle state is reachable.

### Out-of-scope claims

This campaign must not claim that any alpha is validated, that any feature or label is
predictive, that any strategy is profitable, tradable, robust, production-ready, paper-ready,
live-ready, or broker-ready, that any FeatureSet or LabelSet is a promoted candidate, or that a
good diagnostic implies production readiness. It produces a governed research substrate only.

## Relationship to ALPHA_AGENT_FACTORY_MVP

`ALPHA_FEATURE_LABEL_FOUNDATION_V1` is the **substrate that `ALPHA_AGENT_FACTORY_MVP` consumes.**
Future AI Alpha Researchers in the Agent Factory will reference a `FeatureSet` plus a `LabelSet`
through a `StudySpec`, which binds an `AlphaSpec` (`aspec_`), a `LabelSpec` (`lspec_`), a
`dataset_scope`, a `split_protocol`, metrics, cost assumptions, a variant budget, a locked-test
policy, negative controls, and stopping rules. The **StudySpec Input Pack** delivered in this
campaign (FLF-P27) is a **new additive helper** that bundles `freq_`/`lspec_`/`aspec_` handles
plus the `dataset_scope` a StudySpec references; it must **not** modify the StudySpec schema or
any existing governance module. The Agent Factory's research throughput is only as trustworthy as
this substrate's no-lookahead, deduplication, cost-awareness, and leakage guarantees — which is
why this campaign installs them first.

## Relationship to ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

`ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` — the future core alpha pilot — will consume the registered,
`READY_FOR_STUDY` features and labels this campaign produces, under its own explicitly authorized
campaign contract and constrained by the governance gates and data-admissibility rules already
installed. The program roadmap is:

```text
Data Foundation -> Feature/Label Foundation -> Agent Factory -> Core Alpha -> Strategy/Portfolio
```

This campaign is the second link in that chain: it turns accepted DatasetVersions into a governed
research substrate so the core alpha pilot can search for alpha on point-in-time-safe,
cost-aware, deduplicated, leakage-audited features and labels — never before that substrate
exists, and never on raw provider data. The core alpha pilot must not use the locked-test
partition without governance contamination metadata, and any future use of locked partitions must
create that metadata.

---

*This document is a campaign contract describing strategic intent and boundaries. It is not an
implementation, and it makes no alpha, tradability, profitability, production, or live claim.*
