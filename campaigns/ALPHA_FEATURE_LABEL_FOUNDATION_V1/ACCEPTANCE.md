# ALPHA_FEATURE_LABEL_FOUNDATION_V1 Acceptance Criteria

## Acceptance philosophy

Acceptance for this campaign is **semantic, not mechanical**. Passing tests are necessary
but never sufficient. A phase or gate is accepted only when the Feature/Label substrate
genuinely **fails closed**, the gates genuinely **block** missing prerequisites, no-lookahead
and leakage protections genuinely **hold**, the accepted-DatasetVersion boundary is genuinely
**enforced**, feature/label values stay genuinely **local-only**, and no prohibited scope or
claim is present.

This campaign builds the **research substrate layer** that future AI Alpha Researchers
consume: a versioned, no-lookahead-safe, deduplicated, cost-aware, BBO-aware FeatureStore and
LabelStore over **accepted DatasetVersions**. It owns the substrate and its governance, not
alpha results. A feature is not alpha; a label is not alpha; a FeatureStore is not a factor
library; a materialized FeatureSet is not a promoted candidate; a good diagnostic is not
production readiness; an accepted DatasetVersion is not alpha validated. Acceptance therefore
explicitly rejects any outcome where feature code reads raw provider files, where the accepted
DatasetVersion boundary is bypassed, where a feature lacks `available_ts`, where a label lacks
`label_available_ts`, where a label value is exposed as a live feature, where future or centered
windows are used in live features, where missing BBO is silently forward-filled, where synthetic
no-trade rows are treated as actual trade bars, where governance objects are duplicated instead
of consumed, where the FeatureStore becomes a dumping ground, where the locked-test partition is
used without contamination metadata, where parallel DAG metadata is unsound, where a phase branch
writes `ACTIVE_CAMPAIGN.md`, where merge escapes the serial merge queue, or where any
alpha/profitability/tradability/strategy/backtest/portfolio claim or scope appears.

This campaign runs under **Workflow 2 with the DAG wave scheduler**: dependency-ready phase
selection, concurrent build of conflict-free parallel-safe waves in isolated worktrees, and a
**serial merge queue** that merges one PR at a time. Ralph owns the strict driver loop, STOP
checks, validation orchestration, review routing, verdict parsing, bounded repair, PR/CI/merge
gates, and run summaries. Codex owns scoped execution of the generated spec and truthful
handoffs. Claude Opus is the fresh semantic reviewer for every YELLOW phase. ChatGPT owns
strategic framing and post-run reasoning.

The final verdict for the campaign is one of `COMPLETE`, `COMPLETE_WITH_WARNINGS`, or
`BLOCKED`. A truthful `BLOCKED` is acceptable and strongly preferred over a false `COMPLETE`.

## Campaign-level acceptance criteria

The campaign is accepted only when all of the following hold, every phase carries a merged
`PASS` or `PASS_WITH_WARNINGS` verdict (or a truthful `BLOCKED` is recorded), and the artifact
audit is clean:

1. The Feature/Label layer **consumes only accepted DatasetVersions** through the sanctioned
   `alpha_system.data.foundation.version_registry.resolve_dataset_version` adapter and the
   canonical record loaders (`CanonicalBarRecord` / `CanonicalBBORecord` /
   `DenseGridBarRecord`); **no feature or label code reads raw provider files** (`.dbn`/`.zst`/
   parquet/arrow/feather/provider responses).
2. Admissibility is enforced: a DatasetVersion is consumed only in lifecycle state
   `VERSIONED` or `READY_FOR_RESEARCH` with non-blocking quality + coverage; Databento and IBKR
   DatasetVersions are **never merged**; locked-test partition use requires governance
   contamination metadata.
3. **Every feature value carries `available_ts`; every label value carries `label_available_ts`.**
   No `FeatureRequest` → no feature; no `FeatureSpec` → no feature values; no `LabelSpec` →
   no label values.
4. The **FeatureRequest gate and duplicate-exposure guard** are wired to the existing
   `governance` modules (`FeatureRequest`, `duplicate_exposure`) and **consumed, not
   re-implemented** (R-022); the **label-leakage guard** and **LabelSpec/StudySpec** are
   likewise consumed.
5. The full Feature object set is named and contracted: `FeatureRequest`, `FeatureSpec`,
   `FeatureFamily`, `FeatureInputSpec`, `TransformSpec`, `WindowSpec`, `NormalizationSpec`,
   `FeatureSetSpec`, `FeatureMaterializationPlan`, `FeatureValueRecord`, `FeatureVersion`,
   `FeatureRegistryRecord`, `FeatureStore`, `FeatureLineageRecord`, `FeatureQualityReport`,
   `FeatureCoverageReport`, `DuplicateExposureReport`, `EquivalentFeatureGroup`,
   `FeatureDeprecationRecord`, `BBOFeatureSpec`, `SpreadFeatureSpec`, `MicropriceFeatureSpec`,
   `TopBookImbalanceFeatureSpec`, `LiquidityQualityFeatureSpec`.
6. The full Label object set is named and contracted: `LabelSpec`, `LabelFamily`,
   `LabelInputSpec`, `LabelHorizonSpec`, `LabelPathSpec`, `BarrierSpec`, `CostAdjustmentSpec`,
   `LabelMaterializationPlan`, `LabelValueRecord`, `LabelVersion`, `LabelRegistryRecord`,
   `LabelStore`, `LabelLineageRecord`, `LabelQualityReport`, `LabelCoverageReport`,
   `LabelLeakageAuditReport`, `LabelAvailabilityPolicy`.
7. Five feature families are implemented additively (Base OHLCV, BBO/tradability,
   Session/Calendar/Roll, Cross-Market ES/NQ/RTY, Liquidity/Structure) and four label families
   are implemented additively (Fixed-Horizon/Midprice forward, Cost-/Spread-adjusted,
   Path MFE/MAE/Triple-Barrier, Strategy-Agnostic Event), each in disjoint family directories
   on synthetic fixtures.
8. The feature and label **materialization engines, stores, and registries are local-only**;
   feature/label values, registry DBs, and heavy artifacts are **never committed**; neither
   store becomes a dumping ground.
9. **No-lookahead and leakage protections hold**: no label-as-feature; no future/centered
   live-window feature; BBO missingness flagged (`missing_bbo` / `bbo_quarantined`) with no
   silent forward-fill; synthetic dense-grid no-trade rows flagged
   (`has_trade=false`, `synthetic=true`, `no_trade`) and never treated as trade bars.
10. The **StudySpec Input Pack** is a new, additive governance helper that bundles
    `freq_` / `lspec_` / `aspec_` handles + `dataset_scope` and does **not** modify the
    `StudySpec` schema or any existing governance module.
11. No alpha, profitability, tradability, strategy, backtest, portfolio, broker, paper, live,
    order, or account scope or claim is introduced anywhere. The prohibited MVP states
    `ALPHA_VALIDATED`, `STRATEGY_READY`, `LIVE_READY`, `PROFITABLE`, `TRADABLE`,
    `PRODUCTION_READY` are unreachable by any implemented transition.

All 32 phases (`FLF-P00` … `FLF-P31`) are complete with merged verdicts. `FLF-P00` and
`FLF-P29` are GREEN (docs/mechanical, review optional); all other phases are YELLOW and require
fresh Claude Opus review and auto-merge through the serial merge queue. There are **no RED-lane
phases** and **no external provider calls** in this campaign: the data is already pulled, and
the Feature/Label layer consumes only local accepted DatasetVersions.

## Dataset-consumption-level acceptance

* The single sanctioned consumption path is
  `alpha_system.data.foundation.version_registry.resolve_dataset_version(registry_path, id)`,
  wrapped by `src/alpha_system/features/consumption.py`; records are built only via
  `CanonicalBarRecord.from_mapping` / `CanonicalBBORecord.from_mapping` /
  `DenseGridBarRecord.from_mapping`.
* Consumption **refuses to materialize** unless the DatasetVersion is admissible (lifecycle
  state in `{VERSIONED, READY_FOR_RESEARCH}` with non-blocking quality + coverage); a missing
  or inadmissible DatasetVersion blocks the consumer.
* **No raw provider files** (`.dbn`/`.zst`/parquet/arrow/feather/IBKR responses) are ever read
  from feature/label code; the consumption adapter is the only door and it never exposes raw
  provider fields.
* Databento is the **primary deep-history research source** (GLBX.MDP3, ES/NQ/RTY, OHLCV-1m +
  BBO-1m + Definition/Statistics/Status); IBKR is **broker-source recent validation only**;
  Databento and IBKR DatasetVersions are **never merged** into one input.
* Locked-test partition use carries governance contamination metadata via
  `require_governance_metadata_for_locked_partition_use(...)`; the registry path remains
  local-only under `$ALPHA_DATA_ROOT/registry/datasets.sqlite`.

## DAG-wave-scheduler acceptance

* `workflow2.scheduler.mode: dag_wave`, `parallel_execution: true`, `max_parallel_phases: 3`,
  `merge_queue: serial`, `update_active_campaign: coordinator_only`.
* A phase is parallel-safe **only** if it sets `parallel_safe: true`, declares **disjoint
  `allowed_paths`**, sets `must_run_alone: false`, declares no global/coordinator file, and is
  not RED. A phase that omits `parallel_safe: true` or `allowed_paths` **runs alone**.
* Parallel-safe phases are exactly the family/diagnostics fan-out: `FLF-P08`–`FLF-P12`
  (`feature_families`), `FLF-P17`–`FLF-P20` (`label_families`), and `FLF-P24`, `FLF-P25`,
  `FLF-P27`, `FLF-P29` (the `diagnostics_and_packaging` merge group — diagnostics/governance/docs
  fan-out, spanning the `diagnostics_and_tests` and `workflow_and_closeout` gates). Bootstrap, core contracts, both
  materialization tracks, stores/registries, the CLI surface, the dry runs, and closeout
  **run alone**.
* Parallel-safe phases within a wave write **disjoint paths** and never touch shared
  feature/label core; concurrency is conflict-free by construction.
* **Merge is always serial** — one PR at a time through the merge queue — even when phases
  build concurrently in isolated worktrees.
* `ACTIVE_CAMPAIGN.md` is coordinator-owned and is **never written by a phase branch** in
  parallel mode.
* `just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1` (read-only) and
  `just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3` were run before any
  live parallel run, and the planned waves match the intended shape.

## FeatureRequest-level acceptance

* No feature is reachable for implementation without an **approved governance `FeatureRequest`**
  (id prefix `freq_`); `request_gate.py` adapts `alpha_system.governance.feature_request`, it
  does not re-implement it.
* The gate enforces `approval_status` semantics (`PENDING` / `BLOCKED_DUPLICATE` /
  `NEEDS_REVIEW` / `APPROVED`); only `APPROVED` requests permit implementation, and the gate is
  **fail-closed**.
* `requested_inputs`, `formula_sketch`, `availability_assumptions`,
  `duplicate_or_equivalent_exposure_notes`, and `data_requirements` are present and honored;
  duplicate/equivalent exposure is checked and recorded via the governance guard.
* The FeatureRequest implies neither that a feature is implemented, nor that values exist, nor
  that the feature is alpha.

## FeatureSpec-level acceptance

* `FeatureSpec`, `FeatureFamily`, `FeatureInputSpec`, `TransformSpec`, `WindowSpec`,
  `NormalizationSpec`, `FeatureSetSpec`, `FeatureVersion`, and `FeatureLineageRecord` exist as
  immutable, hashable contract objects with a deterministic `FeatureVersion` id.
* `available_ts` is **required** on `FeatureValueRecord`; **future and centered windows are
  contract-forbidden** for live features (centered/future windows are offline-only).
* No `FeatureSpec` → **no feature values**; the contract layer gates materialization.
* The new feature `FeatureSetSpec` **does not collide** with the pre-existing
  `experiments/feature_sets.py` `FeatureSetSpec`; it is namespaced under `features/`.
* A FeatureSpec implies no alpha value, no tradability, and no promotion.

## Feature-materialization-level acceptance

* The `FeatureMaterializationPlan` + engine turn an approved `FeatureSetSpec` into
  `FeatureValueRecord`s for an accepted DatasetVersion + partition: **deterministic,
  no-lookahead, idempotent, local-only**.
* `available_ts` is **propagated** onto every materialized value; partition and locked-test
  gating are enforced; outputs are written only under `$ALPHA_DATA_ROOT`.
* A **dry-run mode** plans without writing; **no feature values are committed**; no external
  provider call and no alpha search occur.
* Materialization implies no research approval and no promotion.

## FeatureStore-level acceptance

* `FeatureStore` + `FeatureRegistry` version, lineage-track, and make discoverable every
  materialized feature via `FeatureRegistryRecord`, `FeatureLineageRecord`, and
  `FeatureDeprecationRecord`.
* The registry DB is **local-only under `$ALPHA_DATA_ROOT` (sqlite) and never committed**;
  tests run against a temp DB with no real data.
* Duplicate-exposure status and deprecation are recorded; the FeatureStore is **not a dumping
  ground** — equivalent/duplicate features are deduplicated, grouped, or deprecated, never
  silently accumulated.
* The store implies no alpha value; a registered feature is not a promoted candidate.

## Duplicate-exposure-level acceptance

* Duplicate/equivalent exposure is detected via the governance `duplicate_exposure` guard
  (consumed, not re-implemented) and surfaced as `DuplicateExposureReport` /
  `EquivalentFeatureGroup` views.
* Adding a feature that duplicates an existing exposure under a new name is **blocked or recorded**
  with an explicit equivalence link; silent duplication is a hard failure.
* The duplicate-exposure record implies no judgment of alpha quality, only of exposure overlap.

## LabelSpec-level acceptance

* `LabelSpec`, `LabelFamily`, `LabelInputSpec`, `LabelHorizonSpec`, `LabelPathSpec`,
  `BarrierSpec`, `CostAdjustmentSpec`, and `LabelVersion` exist as contract objects; the
  `LabelVersion` contracts **bind to the governance `LabelSpec`** (id prefix `lspec_`),
  consuming `horizon`, `path_rules`, `cost_model`, `target_stop_rules`, `availability_time`,
  `forbidden_feature_overlap`, and `leakage_checks` (including `label_as_feature` +
  `availability_time`).
* `label_available_ts` is **required** on `LabelValueRecord`; no `LabelSpec` → **no label
  values**.
* Future data is **legal only for labels** (forward horizons), never for live features; a label
  is never exposed as a feature.
* A LabelSpec implies no alpha value and no tradability.

## Label-materialization-level acceptance

* The `LabelMaterializationPlan` + engine turn an approved label spec into `LabelValueRecord`s
  for an accepted DatasetVersion + partition: **deterministic, local-only, idempotent**, with
  `label_available_ts` propagated onto every value.
* Forward-looking computation is confined to label horizons; **no label value is committed**;
  outputs are written only under `$ALPHA_DATA_ROOT`.
* A dry-run/plan mode exists; no external provider call and no alpha search occur.

## LabelStore-level acceptance

* `LabelStore` + `LabelRegistry` version and lineage-track every materialized label via
  `LabelRegistryRecord` and `LabelLineageRecord`; the registry DB is **local-only and never
  committed**, and tests run against a temp DB.
* `LabelQualityReport` and `LabelCoverageReport` (and a label card where applicable) provide
  fail-closed quality + coverage evidence with blocking vs non-blocking status.
* The store implies no alpha value; a registered label is not a promoted candidate.

## No-lookahead-level acceptance

* Canonical input views key strictly off **`available_ts`**; usability never keys off
  `event_ts`, provider timestamps, or `ingested_at`. `available_ts >= bar_end_ts` is honored.
* The transform/window/normalization **primitives are causal**; centered/future windows are
  offline-only and **blocked from live-feature contracts**.
* The `tests/no_lookahead/feature_label` suite passes and proves: input views are
  `available_ts`-ordered, primitives are causal, label values respect `label_available_ts`, and
  no label leaks into a live feature.
* Every feature value carries `available_ts` and every label value carries `label_available_ts`;
  a feature without `available_ts` or a label without `label_available_ts` is a hard blocker.

## Leakage-audit-level acceptance

* `LabelLeakageAuditReport` is produced by `labels/leakage_audit.py` via the governance
  `label_leakage_guard` (consumed, not re-implemented), enforcing the `label_as_feature` and
  `availability_time` checks for every registered label.
* `forbidden_feature_overlap` is audited; a label that overlaps a forbidden feature, or that is
  reachable as a live feature, **fails closed**.
* Availability ordering is audited for every label; a label whose value would be known before
  `label_available_ts` is a hard failure.
* The leakage audit implies no alpha readiness — only that the label is leakage-safe.

## BBO/tradability-level acceptance

* BBO input views surface `bid`, `ask`, `bid_size`, `ask_size`, `mid`, `spread`, and optional
  `spread_ticks` / `microprice` / `bid_order_count` / `ask_order_count`, with the canonical
  invariants honored (`mid == (bid+ask)/2`, `spread == ask-bid`, `ask >= bid`,
  `bid <= microprice <= ask`).
* **Missing/abnormal BBO is flagged** using the `missing_bbo` and `bbo_quarantined`
  quality-flag tokens; there is **no silent forward-fill**, and the missing-quote condition is
  exposed to families rather than imputed away.
* The BBO tradability family covers at least: `mid`, `spread`, `spread_ticks`, `spread_bps`,
  `spread_zscore`, bid size, ask size, `top_book_depth`, `top_book_imbalance`, `microprice`,
  `microprice_minus_mid`, `missing_bbo_flag`, `bad_quote_flag`, `wide_spread_flag`,
  `low_depth_flag`; `microprice` requires valid bid/ask sizes.
* BBO features describe **tradability quality, not tradability validation** — no claim that any
  instrument is tradable or any strategy executable.

## Cost-adjusted-label-level acceptance

* The Cost-/Spread-adjusted label family produces `cost_adjusted_fwd_ret` and
  `spread_adjusted_fwd_ret` using a `CostAdjustmentSpec` and the governance `LabelSpec`
  `cost_model`; cost/spread adjustment is explicit and reproducible, never assumed away.
* Cost-adjusted labels carry `label_available_ts`, are local-only, and remain **descriptive
  labels, not profitability or net-edge claims**.
* A cost-adjusted label implies no realized PnL, no fill assumption beyond the documented cost
  model, and no tradability.

## Cross-market-feature-level acceptance

* The Cross-Market ES/NQ/RTY family is built from **synchronized, `available_ts`-aligned**
  per-instrument input views and covers at least: synchronized ES/NQ/RTY returns,
  NQ-minus-ES return spread, RTY-minus-ES return spread, rolling beta residual, rolling
  correlation, confirmation/divergence flags, and risk-on/risk-off rotation proxies.
* Cross-market alignment **never introduces lookahead**: a value at time *t* uses only inputs
  available by `available_ts` for every instrument; misaligned or future cross-market data is a
  hard failure.
* Cross-market features describe **co-movement and structure, not alpha** — no claim of a
  tradable cross-market edge.

## Diagnostics-report-level acceptance

* `FeatureQualityReport` / `FeatureCoverageReport` and the Feature/Label diagnostics reports are
  **descriptive and non-promotional**: coverage by symbol/session/partition and quality
  (nan rates, constant features, missing-BBO exposure, label coverage) with **blocking vs
  non-blocking status clearly separated** and a fail-closed status.
* Reports contain **no IC ranking, no alpha scoring, no profitability/tradability claim**;
  cards render without claiming alpha or tradability.
* **No committed report bundles or row-level values** — only curated, row-free summaries may be
  committed; a silent gap or undocumented missing coverage produces a blocking status.

## Governance-integration-level acceptance

* The `StudySpec Input Pack` (`src/alpha_system/governance/study_input_pack.py`) is **new and
  additive**: it bundles `freq_` / `lspec_` / `aspec_` id handles + `dataset_scope` that a
  `StudySpec` references, and validates against the existing `StudySpec` / `LabelSpec` /
  `FeatureRequest` contracts.
* It **does not modify** the `StudySpec` schema or any existing governance module
  (`study_spec.py`, `feature_request.py`, `label_spec.py`, `duplicate_exposure.py`,
  `label_leakage_guard.py`); no parallel study/experiment spec is introduced (R-022).
* The pack implies no study has been run, no alpha validated, and no result produced — it is an
  input bundle only.

## Workflow 2 integration acceptance

* Run-local handoff/review/verdict/checks/repair artifacts remain under `runs/**` and are
  **never committed**; `git ls-files runs` returns empty.
* Commit-eligible handoffs live under `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/**` and
  commit-eligible reviews under `reviews/ALPHA_FEATURE_LABEL_FOUNDATION_V1/**`.
* The Workflow 2 state order
  (`RUN_INIT → CAMPAIGN_LOAD → PHASE_SELECT → SPEC_GENERATE → SPEC_VALIDATE → WORKTREE_CREATE →
  CODEX_EXECUTE → CHECKS_RUN → HANDOFF_VALIDATE → CLAUDE_REVIEW → VERDICT_PARSE → PR_CREATE →
  CI_WAIT → MERGE_GATE → MERGE → DONE_CHECK → NEXT_PHASE → CAMPAIGN_DONE_CHECK → RUN_SUMMARY`),
  STOP/resume semantics, and bounded-repair routing (max 2 attempts by default, recorded under
  `runs/<run_id>/phases/<phase_id>/repair_attempts/`) are honored.
* Parallel-safe phases build concurrently in isolated worktrees but merge **serially**; no phase
  branch writes `ACTIVE_CAMPAIGN.md`; the coordinator owns the pointer.
* The small Databento dry run (`FLF-P26`) and the end-to-end dry run (`FLF-P30`) are local-only,
  make **no external provider call**, commit only curated row-free summaries, and may record a
  truthful `PASS_WITH_WARNINGS` (with the exact operator command documented) when the local
  registry/data is absent on the runner.

## Artifact-policy acceptance

* Feature/label values, raw/canonical market data, provider responses, account info, local
  registries/DBs, and heavy artifacts are **local-only** and never committed; campaign and docs
  files may describe paths but never commit data.
* `git ls-files runs` returns empty; `find data -type f ! -name README.md ! -name .gitkeep`
  returns empty; `find metadata -type f ! -name README.md ! -name .gitkeep` returns empty.
* No `*.parquet` / `*.arrow` / `*.feather` / `*.dbn` / `*.zst` / `*.sqlite` / `*.db` / `*.log`
  outside documented tiny synthetic `tests/fixtures/**`; `find artifacts -type f -size +1M`
  returns empty.
* Explicit staging only; **no `git add .` / `git add -A`**; no force push. The governance
  contract modules are consumed, never edited.

## Review-level acceptance

* Every YELLOW phase has a **fresh Claude Opus 4.8 xhigh review** and a `verdict.json`; merged
  phases are `PASS` or `PASS_WITH_WARNINGS`. `FAIL` / `BLOCKED` / `REWORK` block merge. GREEN
  phases (`FLF-P00`, `FLF-P29`) may skip review.
* The reviewer is **independent**; the implementer cannot self-approve.
* Reviews verify: phase-scope compliance; feature/label object completeness for the phase; no
  raw-provider access; accepted-DatasetVersion-only consumption via `resolve_dataset_version`;
  FeatureRequest gate + duplicate-exposure guard wired to governance (not re-implemented);
  FeatureSpec/LabelSpec required before values; `available_ts` / `label_available_ts` present;
  no label-as-feature and no future/centered live-window feature; BBO missingness flagged with
  no silent forward-fill and synthetic no-trade rows never treated as trades; locked-test
  partition use carries contamination metadata; no FeatureStore/LabelStore dumping ground;
  governance objects consumed not duplicated; **DAG-metadata correctness** (parallel-safe phases
  have disjoint `allowed_paths` and no global files); serial merge queue respected and no phase
  branch writes `ACTIVE_CAMPAIGN.md`; artifact-policy compliance; no broker/live/paper/order/
  account scope; no alpha/profitability/tradability claim and no strategy/backtest/portfolio
  scope; no test weakening; and handoff completeness with semantic done criteria.

## Prohibited shortcuts

The campaign is **not** accepted if any of the following is true:

* raw Databento files read directly by feature code;
* accepted DatasetVersion bypassed;
* features without `available_ts`;
* labels without `label_available_ts`;
* label values used as live features;
* future rolling windows in features;
* centered windows used as live features;
* no FeatureRequest but feature implemented;
* no FeatureSpec but feature materialized;
* no LabelSpec but labels materialized;
* duplicate features added under new names;
* FeatureStore becomes dumping ground;
* missing BBO silently forward-filled;
* no-trade synthetic rows treated as actual trade bars;
* locked-test partition used without contamination metadata;
* alpha/profitability/tradability claims introduced;
* strategy/backtest/portfolio work introduced;
* raw/heavy data committed;
* parallel phase marked safe without disjoint allowed_paths;
* phase branch writes ACTIVE_CAMPAIGN.md in parallel mode;
* merge occurs outside serial merge queue.

## Required final validation commands

```bash
cd ~/projects/alpha_system

# YAML parse + phase-coverage validation of the campaign contract
python -c "import yaml,sys; d=yaml.safe_load(open('campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/campaign.yaml')); ids=[p['id'] for p in d['phases']]; assert ids==[f'FLF-P{n:02d}' for n in range(32)], ids; print('campaign.yaml OK:', len(ids), 'phases')"

# Run state and run-artifact audit (must be empty)
git status --short
git ls-files runs

# Data / metadata / heavy-artifact audits (must be empty outside tiny synthetic fixtures)
find data -type f ! -name README.md ! -name ".gitkeep" -print
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
find . -name "*.arrow" -not -path "./tests/fixtures/*" -print
find . -name "*.feather" -not -path "./tests/fixtures/*" -print

# Test + canary validation
python tools/verify.py --all
python tools/hooks/canary_runner.py

# DAG scheduler read-only plan + mock parallel run (no live merges)
just frontier-plan ALPHA_FEATURE_LABEL_FOUNDATION_V1
just frontier-run-parallel-mock ALPHA_FEATURE_LABEL_FOUNDATION_V1 3
```

## Required semantic done-check

Beyond passing tests, the final done-check (Claude Opus) must affirm that:

* the gates genuinely **block missing prerequisites** (no accepted DatasetVersion, no
  FeatureRequest, no FeatureSpec, no LabelSpec, no quality/coverage report, no leakage audit);
* the **accepted-DatasetVersion boundary is real** — feature/label code never reads raw provider
  files and consumes only admissible DatasetVersions via `resolve_dataset_version`;
* **no-lookahead holds** — input views and primitives key off `available_ts`, centered/future
  windows are offline-only, every feature carries `available_ts`, and every label carries
  `label_available_ts`;
* **no label leaks into a feature** — the label-leakage guard is consumed and fail-closed, and
  `forbidden_feature_overlap` + availability ordering are enforced;
* **BBO and no-trade semantics are correct** — missing/abnormal BBO is flagged
  (`missing_bbo` / `bbo_quarantined`) with no silent forward-fill, and synthetic dense-grid
  no-trade rows are flagged and never treated as trade bars;
* **governance is consumed, not duplicated** — FeatureRequest, LabelSpec, the duplicate-exposure
  guard, the label-leakage guard, and the StudySpec Input Pack integrate with the existing
  governance modules without editing them;
* **neither store is a dumping ground** — duplicate/equivalent exposure is recorded and the
  registries are local-only;
* the **DAG metadata is sound** — parallel-safe phases have disjoint `allowed_paths` and no
  global files, merge is serial, and no phase branch writes `ACTIVE_CAMPAIGN.md`;
* **no prohibited scope or claim** exists (broker/live/paper/order-routing/account, external
  provider call, alpha/profitability/tradability/strategy/backtest/portfolio), and the
  prohibited MVP states are unreachable;
* the **artifact audit is clean** (no `runs/**`, raw, canonical, feature/label value, heavy,
  provider, account, or local-DB artifacts committed).

## Final closeout requirements

* `campaigns/ALPHA_FEATURE_LABEL_FOUNDATION_V1/CLOSEOUT.md` exists and records the final verdict
  and any warnings (written by `FLF-P31`).
* `ACTIVE_CAMPAIGN.md` reflects campaign completion and points at the next campaign or none —
  **updated by the coordinator, never by a phase branch**.
* Durable lessons are added to `project-skill` when applicable.
* Next-campaign readiness is recorded: the substrate is ready for `ALPHA_AGENT_FACTORY_MVP`
  (AI Alpha Researchers consuming FeatureSet + LabelSet via `StudySpec`) and
  `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`, which may consume this substrate only under their own
  authorized contracts and the governance + data-admissibility gates this campaign installs. A
  feature is not alpha; a label is not alpha; a materialized FeatureSet is not a promoted
  candidate.

## Final acceptance verdicts

### `COMPLETE`
All campaign-level criteria met, all Feature/Label gates genuinely block missing prerequisites,
the no-lookahead and leakage protections hold, the semantic done-check is clean, the artifact
audit is clean, and no prohibited scope or claims exist.

### `COMPLETE_WITH_WARNINGS`
All hard criteria met, but non-blocking warnings (e.g. documented deferrals, a Databento or
end-to-end dry run that recorded a truthful `PASS_WITH_WARNINGS` because the local
registry/data was absent on the runner, or minor limitations) are recorded in `CLOSEOUT.md`.

### `BLOCKED`
A hard criterion cannot be met (e.g. a gate cannot be made to fail closed, the no-lookahead or
leakage boundary cannot be guaranteed, the accepted-DatasetVersion boundary cannot be enforced,
or a required object cannot be completed in scope). The blocker is recorded truthfully; fake
completion is forbidden, and a truthful `BLOCKED` is preferred over a false `COMPLETE`.
