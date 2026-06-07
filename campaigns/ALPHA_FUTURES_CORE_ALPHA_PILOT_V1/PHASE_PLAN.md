# PHASE_PLAN — ALPHA_FUTURES_CORE_ALPHA_PILOT_V1

31 phases (`FUTCORE-P00` … `FUTCORE-P30`) over a `dag_wave` scheduler with
`parallel_execution: true`, `max_parallel_phases: 3`, and a **serial merge
queue**. Phase ids, names, lanes, dependencies, and DAG metadata are the source
of truth in `campaign.yaml`; this file mirrors them and adds the human-readable
contract per phase. Any disagreement between the two files is a STOP condition.

## Scheduler Wave Map

```text
Sequential : FUTCORE-P00 -> P01 -> P02 -> P03 -> P04 -> P05 -> P06
Parallel   : FUTCORE-P07 P08 P09 P10 P11           (AlphaSpec batches, path-disjoint)
Sequential : FUTCORE-P12 -> P13 -> P14 -> P15
Parallel   : FUTCORE-P16 P17 P18 P19 P20           (diagnostics, path-disjoint, read-only over locked packs)
Sequential : FUTCORE-P21 -> P22 -> P23 -> P24 -> P25 -> P26 -> P27 -> P28 -> P29 -> P30
```

With `max_parallel_phases: 3` the planner packs P07-P11 as [P07,P08,P09]+[P10,P11]
and P16-P20 as [P16,P17,P18]+[P19,P20]. Ledger/promotion/review/audit/closeout
phases are `must_run_alone`. Merge is always one PR at a time.

## Phase Summary Table

| Phase | Name | Lane | Deps | parallel_safe | must_run_alone | merge_group | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FUTCORE-P00` | Core Alpha Pilot Campaign Bootstrap | GREEN | — | false | true | bootstrap | bootstrap_and_inputs |
| `FUTCORE-P01` | Preflight: PRE_CORE Hardening, DatasetVersion, Parquet Packs, Runtime, Agent Factory | YELLOW | FUTCORE-P00 | false | true | foundation | bootstrap_and_inputs |
| `FUTCORE-P02` | Pilot Scope, Universe, Sessions, Horizons, and Research Budget | YELLOW | FUTCORE-P01 | false | true | foundation | bootstrap_and_inputs |
| `FUTCORE-P03` | Data / Feature / Label Input Pack Lock | YELLOW | FUTCORE-P02 | false | true | foundation | bootstrap_and_inputs |
| `FUTCORE-P04` | CostModelVersion and Session-Specific Cost Stress Contract | YELLOW | FUTCORE-P03 | false | true | foundation | bootstrap_and_inputs |
| `FUTCORE-P05` | Pilot AlphaSpec Batch Protocol | YELLOW | FUTCORE-P04 | false | true | foundation | bootstrap_and_inputs |
| `FUTCORE-P06` | Research Queue and Agent Assignment Setup | YELLOW | FUTCORE-P05 | false | true | foundation | bootstrap_and_inputs |
| `FUTCORE-P07` | Cross-Market AlphaSpec Batch | YELLOW | FUTCORE-P06 | true | false | alpha_specs | alpha_spec_batches |
| `FUTCORE-P08` | VWAP / Session AlphaSpec Batch | YELLOW | FUTCORE-P06 | true | false | alpha_specs | alpha_spec_batches |
| `FUTCORE-P09` | Regime Momentum/Reversion AlphaSpec Batch | YELLOW | FUTCORE-P06 | true | false | alpha_specs | alpha_spec_batches |
| `FUTCORE-P10` | Liquidity Sweep / PA AlphaSpec Batch | YELLOW | FUTCORE-P06 | true | false | alpha_specs | alpha_spec_batches |
| `FUTCORE-P11` | BBO Tradability AlphaSpec Batch | YELLOW | FUTCORE-P06 | true | false | alpha_specs | alpha_spec_batches |
| `FUTCORE-P12` | AlphaSpec Critic and Family Budget Audit | YELLOW | FUTCORE-P07, FUTCORE-P08, FUTCORE-P09, FUTCORE-P10, FUTCORE-P11 | false | true | spec_audit | spec_audit_and_packs |
| `FUTCORE-P13` | Data Contract / FeaturePack / LabelPack Audit | YELLOW | FUTCORE-P12 | false | true | spec_audit | spec_audit_and_packs |
| `FUTCORE-P14` | Approved StudySpec Pack | YELLOW | FUTCORE-P13 | false | true | spec_audit | spec_audit_and_packs |
| `FUTCORE-P15` | Minimal Missing FeatureRequest / LabelSpec Additions, If Needed | YELLOW | FUTCORE-P14 | false | true | spec_audit | spec_audit_and_packs |
| `FUTCORE-P16` | Cross-Market Diagnostics | YELLOW | FUTCORE-P14, FUTCORE-P15 | true | false | diagnostics | family_diagnostics |
| `FUTCORE-P17` | VWAP / Session Diagnostics | YELLOW | FUTCORE-P14, FUTCORE-P15 | true | false | diagnostics | family_diagnostics |
| `FUTCORE-P18` | Regime Momentum/Reversion Diagnostics | YELLOW | FUTCORE-P14, FUTCORE-P15 | true | false | diagnostics | family_diagnostics |
| `FUTCORE-P19` | Liquidity Sweep / PA Diagnostics | YELLOW | FUTCORE-P14, FUTCORE-P15 | true | false | diagnostics | family_diagnostics |
| `FUTCORE-P20` | BBO Tradability Diagnostics | YELLOW | FUTCORE-P14, FUTCORE-P15 | true | false | diagnostics | family_diagnostics |
| `FUTCORE-P21` | Cost Stress and Thin-Session Stress Consolidation | YELLOW | FUTCORE-P16, FUTCORE-P17, FUTCORE-P18, FUTCORE-P19, FUTCORE-P20 | false | true | consolidation | consolidation_and_audits |
| `FUTCORE-P22` | Session / Horizon / Regime Matrix Consolidation | YELLOW | FUTCORE-P21 | false | true | consolidation | consolidation_and_audits |
| `FUTCORE-P23` | No-Lookahead / Label Leakage / Same-Bar Optimism Audit | YELLOW | FUTCORE-P22 | false | true | consolidation | consolidation_and_audits |
| `FUTCORE-P24` | Bounded Grid / Variant Budget Audit | YELLOW | FUTCORE-P23 | false | true | consolidation | consolidation_and_audits |
| `FUTCORE-P25` | Statistical Reviewer Verdicts | YELLOW | FUTCORE-P24 | false | true | evidence | evidence_ledger_promotion |
| `FUTCORE-P26` | TrialLedger / RejectedIdeaLedger Recording | YELLOW | FUTCORE-P25 | false | true | evidence | evidence_ledger_promotion |
| `FUTCORE-P27` | EvidenceDraft and ReferenceCandidateHandoff for Survivors | YELLOW | FUTCORE-P26 | false | true | evidence | evidence_ledger_promotion |
| `FUTCORE-P28` | PromotionDecision: Reject / Inconclusive / Watch / CandidateResearch | YELLOW | FUTCORE-P27 | false | true | evidence | evidence_ledger_promotion |
| `FUTCORE-P29` | Failure-Mode Handoff for Validation Governance / FactorLibrary / Strategy Reference | YELLOW | FUTCORE-P28 | false | true | closeout | handoff_and_closeout |
| `FUTCORE-P30` | Acceptance Audit and Closeout | YELLOW | FUTCORE-P29 | false | true | closeout | handoff_and_closeout |

## Per-Phase Contracts

### FUTCORE-P00 — Core Alpha Pilot Campaign Bootstrap

- **Lane**: GREEN
- **Dependencies**: none (entry phase)
- **Purpose**: Land the campaign contract bundle, the root active pointer, and the pilot artifact/doc scaffolding so Workflow 2 can plan and schedule.
- **Scope**:
  - Confirm the 6-file campaign bundle is present and internally consistent.
  - Create the pilot docs index and the value-free research evidence directory skeleton.
  - Update the root ACTIVE_CAMPAIGN.md pointer (coordinator-owned).
- **Non-goals**:
  - Any alpha research, AlphaSpec drafting, or diagnostics.
  - Any code under src/alpha_system primitives.
- **Expected files / directories** (allowed_paths):
  - `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/**`
  - `docs/futures_core_alpha_pilot/README.md`
  - `docs/futures_core_alpha_pilot/OVERVIEW.md`
  - `research/futures_core_alpha_pilot_v1/README.md`
  - `research/futures_core_alpha_pilot_v1/.gitkeep`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P00.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P00/**`
  - `runs/**`
  - `ACTIVE_CAMPAIGN.md`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `test -f ACTIVE_CAMPAIGN.md`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/GOAL.md`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/PHASE_PLAN.md`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/campaign.yaml`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACCEPTANCE.md`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RISK_REGISTER.md`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/RUNBOOK.md`
  - `test '!' -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/ACTIVE_CAMPAIGN.md`
  - `test -f handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P00.md`
  - `grep -q "ALPHA_FUTURES_CORE_ALPHA_PILOT_V1" ACTIVE_CAMPAIGN.md`
  - `python tools/verify.py --smoke`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only campaign control + overview docs; value-free research evidence directory skeleton; commit-eligible handoff. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Bundle present and consistent; root pointer selects this campaign; no campaign-local ACTIVE_CAMPAIGN.md; smoke passes; runs/ untracked.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P00.md`
- **Review required**: optional (Green lane)
- **Auto-merge eligibility**: yes (Green, auto-merge after checks)

### FUTCORE-P01 — Preflight: PRE_CORE Hardening, DatasetVersion, Parquet Packs, Runtime, Agent Factory

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P00`
- **Purpose**: Record the preflight readiness contract proving every entry gate that lets the pilot start.
- **Scope**:
  - Verify the consumed primitives import and the runtime real-data smoke status.
  - Record FEATURE_LABEL_PARQUET_SINK_V1 and SESSION_LABEL_GUARD_FIX_V1 as complete (or block).
  - Record accepted DatasetVersion / Parquet FeaturePack / LabelPack availability and Agent Factory preflight.
- **Non-goals**:
  - Editing the consumed primitives.
  - Drafting AlphaSpecs or running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `docs/futures_core_alpha_pilot/PREFLIGHT.md`
  - `research/futures_core_alpha_pilot_v1/preflight/**`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P01.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P01/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.governance, alpha_system.runtime, alpha_system.agent_factory"`
  - `python tools/verify.py --smoke`
  - `test -f docs/futures_core_alpha_pilot/PREFLIGHT.md`
  - `test -f research/futures_core_alpha_pilot_v1/preflight/preflight_report.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only preflight readiness contract (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Every entry gate recorded with status; blockers escalate rather than proceed; no consumed primitive edited.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P01.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P02 — Pilot Scope, Universe, Sessions, Horizons, and Research Budget

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P01`
- **Purpose**: Pin the bounded scope contract — universe, session views, horizon policy, family budgets, and finite research budget.
- **Scope**:
  - Record ES/NQ/RTY universe and deferred universe.
  - Record session views, horizon zones, and the family budget split.
  - Record finite idea/AlphaSpec/variant/survivor budgets.
- **Non-goals**:
  - Drafting AlphaSpecs.
  - Expanding universe or family budget.
- **Expected files / directories** (allowed_paths):
  - `docs/futures_core_alpha_pilot/SCOPE.md`
  - `research/futures_core_alpha_pilot_v1/scope/**`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P02.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P02/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -f docs/futures_core_alpha_pilot/SCOPE.md`
  - `test -f research/futures_core_alpha_pilot_v1/scope/scope_contract.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only scope/universe/session/horizon/budget contract (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Scope contract complete, finite, and matches campaign.yaml policy blocks.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P02.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P03 — Data / Feature / Label Input Pack Lock

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P02`
- **Purpose**: Lock the registry-resolved DatasetVersion, Parquet FeaturePack, and LabelPack the pilot will consume, by reference only.
- **Scope**:
  - Record accepted DatasetVersion id(s) and Parquet FeaturePack/LabelPack ids via registry tools.
  - Record value_store_format/parquet_path/value_content_hash/value_schema_version references.
- **Non-goals**:
  - Committing any value data, Parquet, or SQLite.
  - Reading raw provider files.
- **Expected files / directories** (allowed_paths):
  - `docs/futures_core_alpha_pilot/INPUT_PACK.md`
  - `research/futures_core_alpha_pilot_v1/input_pack/**`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/input_pack/input_pack_lock.md`
  - `test -f docs/futures_core_alpha_pilot/INPUT_PACK.md`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet' '**/*.sqlite'`
- **Artifact policy**: explicit staging only; commit only input pack lock by reference (ids/hashes only, value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Pack lock references registry-resolved ids/hashes only; no value data staged.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P03.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P04 — CostModelVersion and Session-Specific Cost Stress Contract

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P03`
- **Purpose**: Pin the three-layer cost model and the cost stress profiles (including thin-session penalties) the pilot will apply.
- **Scope**:
  - Record hard transaction cost, spread crossing, and slippage proxy layers.
  - Record zero_cost/base/stress_1/stress_2/double_cost profiles and thin-session stress rules.
- **Non-goals**:
  - Treating zero-cost as a promotion basis.
  - Running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `docs/futures_core_alpha_pilot/COST_MODEL.md`
  - `research/futures_core_alpha_pilot_v1/cost_model/**`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/cost_model/cost_model_contract.md`
  - `test -f docs/futures_core_alpha_pilot/COST_MODEL.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only cost model + stress profile contract (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: All cost layers and stress profiles defined; zero-cost flagged diagnostic-only.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P04.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P05 — Pilot AlphaSpec Batch Protocol

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P04`
- **Purpose**: Define the AlphaSpec drafting protocol, schema usage, and per-family quotas so batches are uniform and bounded.
- **Scope**:
  - Record the AlphaSpec template, required fields, and per-family draft quotas honoring the family budget.
  - Record the critique/independence rules drafts must satisfy.
- **Non-goals**:
  - Drafting the actual family AlphaSpecs (P07-P11).
- **Expected files / directories** (allowed_paths):
  - `docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md`
  - `research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`
  - `research/futures_core_alpha_pilot_v1/alpha_specs/README.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P05.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P05/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.governance.alpha_spec"`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/alpha_specs/PROTOCOL.md`
  - `test -f docs/futures_core_alpha_pilot/ALPHASPEC_PROTOCOL.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only AlphaSpec batch protocol (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Protocol pins schema, per-family quotas, and independence rules consistent with the family budget.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P05.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P06 — Research Queue and Agent Assignment Setup

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P05`
- **Purpose**: Seed the bounded research queue and the role assignment / separation-of-duties map for the pilot via Agent Factory contracts.
- **Scope**:
  - Record the ResearchTask queue entries and per-task role assignments.
  - Record separation-of-duties bindings (drafter != critic != reviewer != promoter).
- **Non-goals**:
  - Instantiating autonomous agents or running a continuous runner.
- **Expected files / directories** (allowed_paths):
  - `docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md`
  - `research/futures_core_alpha_pilot_v1/queue/**`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P06.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P06/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.agent_factory.queue.models"`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/queue/research_queue.md`
  - `test -f docs/futures_core_alpha_pilot/RESEARCH_QUEUE.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only research queue + role assignment map (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Queue is finite, roles assigned, separation-of-duties encoded; no agent instantiated.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P06.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P07 — Cross-Market AlphaSpec Batch

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P06`
- **Purpose**: Draft the cross-market / relative-value AlphaSpecs (40% budget) using the P05 protocol.
- **Scope**:
  - Draft ES/NQ/RTY lead-lag, beta-residual, rotation, and confirmation/divergence AlphaSpecs.
  - Each AlphaSpec must declare timestamp-alignment and cross-market missingness diagnostics.
- **Non-goals**:
  - Approving or implementing the specs; running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/alpha_specs/cross_market/**`
  - `docs/futures_core_alpha_pilot/alpha_specs/cross_market.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P07.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P07/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/alpha_specs/cross_market`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only cross-market AlphaSpec drafts (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Family AlphaSpec drafts within quota; alignment/missingness diagnostics declared.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P07.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P08 — VWAP / Session AlphaSpec Batch

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P06`
- **Purpose**: Draft the VWAP / session-auction AlphaSpecs (20% budget) using the P05 protocol.
- **Scope**:
  - Draft VWAP reclaim/reject, distance-to-VWAP, opening range, overnight high/low, gap, and RTH-open-vs-ETH AlphaSpecs.
  - Each spec must distinguish running point-in-time VWAP from final-session VWAP.
- **Non-goals**:
  - Approving or implementing the specs; running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session/**`
  - `docs/futures_core_alpha_pilot/alpha_specs/vwap_session.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P08.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P08/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/alpha_specs/vwap_session`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only VWAP/session AlphaSpec drafts (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Family AlphaSpec drafts within quota; running-vs-final VWAP distinction declared.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P08.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P09 — Regime Momentum/Reversion AlphaSpec Batch

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P06`
- **Purpose**: Draft the regime-gated momentum-vs-reversion AlphaSpecs (15% budget) using the P05 protocol.
- **Scope**:
  - Draft trendiness/volatility/range-compression regime AlphaSpecs that gate momentum vs reversion.
  - Each spec must state which regime activates momentum vs reversion, not a global choice.
- **Non-goals**:
  - Approving or implementing the specs; running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/alpha_specs/regime/**`
  - `docs/futures_core_alpha_pilot/alpha_specs/regime.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P09.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P09/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/alpha_specs/regime`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only regime AlphaSpec drafts (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Family AlphaSpec drafts within quota; regime activation logic declared.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P09.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P10 — Liquidity Sweep / PA AlphaSpec Batch

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P06`
- **Purpose**: Draft the liquidity-sweep / failed-breakout / objective price-action AlphaSpecs (15% budget) using the P05 protocol.
- **Scope**:
  - Draft prior high/low sweep, close-back-inside, wick rejection, displacement, compression breakout, and failed-breakout AlphaSpecs.
  - All definitions must be objective and computable; vague PA language must be translated into explicit rules.
- **Non-goals**:
  - Approving or implementing the specs; running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa/**`
  - `docs/futures_core_alpha_pilot/alpha_specs/liquidity_pa.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/alpha_specs/liquidity_pa`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only liquidity/PA AlphaSpec drafts (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Family AlphaSpec drafts within quota; all PA definitions objective and computable.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P10.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P11 — BBO Tradability AlphaSpec Batch

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P06`
- **Purpose**: Draft the BBO tradability / top-book confirmation AlphaSpecs (10% budget) using the P05 protocol.
- **Scope**:
  - Draft spread_zscore, microprice_minus_mid, top_book_imbalance/depth, bad_quote/missing_bbo, and spread/depth filter AlphaSpecs.
  - Frame this family primarily as tradability/risk/confirmation evidence, not executable edge proof.
- **Non-goals**:
  - Approving or implementing the specs; running diagnostics.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability/**`
  - `docs/futures_core_alpha_pilot/alpha_specs/bbo_tradability.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/alpha_specs/bbo_tradability`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only BBO tradability AlphaSpec drafts (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Family AlphaSpec drafts within quota; framed as tradability/confirmation evidence.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P11.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P12 — AlphaSpec Critic and Family Budget Audit

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P07`, `FUTCORE-P08`, `FUTCORE-P09`, `FUTCORE-P10`, `FUTCORE-P11`
- **Purpose**: Critique all family AlphaSpec drafts independently and audit them against the family budget and finite quotas.
- **Scope**:
  - Record AlphaSpec critique decisions (reject / revise / accept-for-StudySpec) by an independent critic.
  - Audit family budget adherence and total approved count against the budget caps.
- **Non-goals**:
  - Self-approving any spec the critic drafted; implementing or promoting.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/critiques/**`
  - `research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`
  - `docs/futures_core_alpha_pilot/CRITIQUE_AND_BUDGET.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P12.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P12/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/critiques`
  - `test -f research/futures_core_alpha_pilot_v1/alpha_specs/BUDGET_AUDIT.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only AlphaSpec critique records + budget audit (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Every draft critiqued by an independent critic; family budget and quota caps respected.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P12.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P13 — Data Contract / FeaturePack / LabelPack Audit

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P12`
- **Purpose**: Audit that every accepted AlphaSpec's required features/labels exist in the locked Parquet packs with valid available_ts, flagging gaps for P15.
- **Scope**:
  - Map each accepted AlphaSpec to required feature/label primitives and confirm availability via registry tools.
  - Produce a minimal gap list (only truly missing primitives) for P15.
- **Non-goals**:
  - Implementing primitives (that is P15); reading raw provider data.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/audits/data_contract/**`
  - `docs/futures_core_alpha_pilot/DATA_CONTRACT_AUDIT.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.governance.study_input_pack"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/audits/data_contract`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only data contract / pack audit + gap list (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Each accepted AlphaSpec mapped to available primitives; minimal gap list produced; available_ts validity confirmed.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P13.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P14 — Approved StudySpec Pack

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P13`
- **Purpose**: Bind accepted AlphaSpecs to runnable StudySpecs (inputs, horizons, sessions, cost profiles, variant budget) by reference only.
- **Scope**:
  - Author one StudySpec per accepted AlphaSpec using governance StudySpec schema.
  - Bind locked packs, session/horizon matrix, cost profiles, and finite variant budgets.
- **Non-goals**:
  - Running diagnostics; editing runtime/governance code.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/study_specs/**`
  - `docs/futures_core_alpha_pilot/STUDY_SPECS.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.governance.study_spec"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/study_specs`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only approved StudySpec pack (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: One StudySpec per accepted AlphaSpec, each binding packs/sessions/horizons/cost/variant-budget.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P14.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P15 — Minimal Missing FeatureRequest / LabelSpec Additions, If Needed

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P14`
- **Purpose**: Add only the minimal, justified missing feature/label primitives the P13 gap list demands, each via FeatureRequest/LabelSpec.
- **Scope**:
  - For each gap, record a FeatureRequest or LabelSpec and add the minimal point-in-time primitive with available_ts/label_available_ts.
  - If no gaps exist, record a no-op decision (preferred outcome).
- **Non-goals**:
  - Building a feature zoo; committing any value data; editing runtime/governance/agent_factory code.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/feature_requests/**`
  - `research/futures_core_alpha_pilot_v1/label_specs/**`
  - `src/alpha_system/features/**`
  - `src/alpha_system/labels/**`
  - `tests/unit/features/**`
  - `tests/unit/labels/**`
  - `docs/futures_core_alpha_pilot/PRIMITIVE_ADDITIONS.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. `FUTCORE-P15` additionally **permits** `src/alpha_system/features/**` and `src/alpha_system/labels/**` for minimal justified primitives only.
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `python tools/verify.py --all`
  - `python tools/hooks/canary_runner.py`
  - `test -f research/futures_core_alpha_pilot_v1/feature_requests/DECISION.md`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet' '**/*.sqlite'`
- **Artifact policy**: explicit staging only; commit only minimal feature/label primitive code with FeatureRequest/LabelSpec records; tests; docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Either a no-op decision recorded, or <=5 minimal primitives added with records, tests, available_ts; verify.py --all and canaries pass.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P15.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P16 — Cross-Market Diagnostics

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P14`, `FUTCORE-P15`
- **Purpose**: Run cross-market StudySpec diagnostics via the runtime tool surface and record value-free reports.
- **Scope**:
  - Run factor/label/signal-probe/cost diagnostics for cross-market StudySpecs through runtime tools over locked Parquet packs.
  - Record summary RuntimeRunSummary/DiagnosticsReport including timestamp-alignment and cross-market missingness splits.
- **Non-goals**:
  - Promoting any idea; editing runtime; committing value data.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market/**`
  - `docs/futures_core_alpha_pilot/diagnostics/cross_market.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.tool_results"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/cross_market`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet'`
- **Artifact policy**: explicit staging only; commit only cross-market diagnostics reports (summary statistics/metadata only, value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Diagnostics run via runtime tools; reports value-free; alignment/missingness splits present.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P16.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P17 — VWAP / Session Diagnostics

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P14`, `FUTCORE-P15`
- **Purpose**: Run VWAP/session StudySpec diagnostics via the runtime tool surface and record value-free reports.
- **Scope**:
  - Run factor/label/signal-probe/cost diagnostics for VWAP/session StudySpecs through runtime tools.
  - Record per-session and session-x-horizon splits; distinguish running vs final VWAP.
- **Non-goals**:
  - Promoting any idea; editing runtime; committing value data.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/**`
  - `docs/futures_core_alpha_pilot/diagnostics/vwap_session.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.tool_results"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet'`
- **Artifact policy**: explicit staging only; commit only VWAP/session diagnostics reports (summary statistics/metadata only, value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Diagnostics run via runtime tools; session splits present; running-vs-final VWAP respected.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P17.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P18 — Regime Momentum/Reversion Diagnostics

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P14`, `FUTCORE-P15`
- **Purpose**: Run regime momentum/reversion StudySpec diagnostics via the runtime tool surface and record value-free reports.
- **Scope**:
  - Run factor/label/signal-probe/cost diagnostics for regime StudySpecs through runtime tools.
  - Record regime splits and parameter-neighborhood stability.
- **Non-goals**:
  - Promoting any idea; editing runtime; committing value data.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/**`
  - `docs/futures_core_alpha_pilot/diagnostics/regime.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P18.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P18/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.tool_results"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/regime`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet'`
- **Artifact policy**: explicit staging only; commit only regime diagnostics reports (summary statistics/metadata only, value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Diagnostics run via runtime tools; regime splits and stability present.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P18.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P19 — Liquidity Sweep / PA Diagnostics

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P14`, `FUTCORE-P15`
- **Purpose**: Run liquidity-sweep / PA StudySpec diagnostics via the runtime tool surface and record value-free reports.
- **Scope**:
  - Run factor/label/signal-probe/cost diagnostics for liquidity/PA StudySpecs through runtime tools.
  - Record spread/liquidity splits and objective-rule trigger counts.
- **Non-goals**:
  - Promoting any idea; editing runtime; committing value data.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/**`
  - `docs/futures_core_alpha_pilot/diagnostics/liquidity_pa.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P19.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P19/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.tool_results"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet'`
- **Artifact policy**: explicit staging only; commit only liquidity/PA diagnostics reports (summary statistics/metadata only, value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Diagnostics run via runtime tools; spread/liquidity splits present; objective triggers counted.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P19.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P20 — BBO Tradability Diagnostics

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P14`, `FUTCORE-P15`
- **Purpose**: Run BBO tradability StudySpec diagnostics via the runtime tool surface and record value-free reports.
- **Scope**:
  - Run factor/label/signal-probe/cost diagnostics for BBO StudySpecs through runtime tools.
  - Record BBO missingness / bad-quote splits and confirmation value rather than standalone edge.
- **Non-goals**:
  - Promoting any idea; editing runtime; committing value data.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability/**`
  - `docs/futures_core_alpha_pilot/diagnostics/bbo_tradability.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.tool_results"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/diagnostics_reports/bbo_tradability`
  - `git ls-files runs`
  - `git ls-files '**/*.parquet'`
- **Artifact policy**: explicit staging only; commit only BBO tradability diagnostics reports (summary statistics/metadata only, value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Diagnostics run via runtime tools; BBO missingness/bad-quote splits present.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P20.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P21 — Cost Stress and Thin-Session Stress Consolidation

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P16`, `FUTCORE-P17`, `FUTCORE-P18`, `FUTCORE-P19`, `FUTCORE-P20`
- **Purpose**: Consolidate cost-stress and thin-session-stress results across all families into a single CostSensitivityReport.
- **Scope**:
  - Aggregate zero_cost/base/stress_1/stress_2/double_cost outcomes per idea.
  - Flag ideas surviving only under zero/under-stressed cost and thin-session fragility.
- **Non-goals**:
  - Promoting any idea on a zero-cost basis.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/cost/**`
  - `docs/futures_core_alpha_pilot/COST_SENSITIVITY.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P21.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P21/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/cost/cost_sensitivity_report.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only cost sensitivity + thin-session report (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: All cost profiles consolidated; zero-cost-only and thin-session-fragile survivors flagged.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P21.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P22 — Session / Horizon / Regime Matrix Consolidation

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P21`
- **Purpose**: Consolidate the session x horizon x regime stability matrix across all families.
- **Scope**:
  - Build the session-x-horizon matrix and regime-split summary per surviving idea.
  - Flag ideas stable only in a narrow session/horizon/regime cell.
- **Non-goals**:
  - Promoting any idea.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/matrix/**`
  - `docs/futures_core_alpha_pilot/MATRIX.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P22.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P22/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/matrix/session_horizon_regime_matrix.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only session/horizon/regime matrix (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Matrix complete; narrow-cell-only survivors flagged.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P22.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P23 — No-Lookahead / Label Leakage / Same-Bar Optimism Audit

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P22`
- **Purpose**: Independently audit surviving ideas for lookahead, label leakage, same-bar optimism, and cross-instrument availability.
- **Scope**:
  - Verify available_ts / label_available_ts validity and no use of final-session aggregates intraday.
  - Verify cross-instrument availability for cross-market ideas and flag any leakage.
- **Non-goals**:
  - Promoting any idea; weakening audits.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/audits/no_lookahead/**`
  - `docs/futures_core_alpha_pilot/NO_LOOKAHEAD_AUDIT.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P23.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P23/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `python tools/hooks/canary_runner.py`
  - `test -f research/futures_core_alpha_pilot_v1/audits/no_lookahead/no_lookahead_audit.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only no-lookahead / leakage / same-bar audit (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Audit covers every surviving idea; leakage/same-bar/cross-instrument issues flagged; canaries pass.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P23.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P24 — Bounded Grid / Variant Budget Audit

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P23`
- **Purpose**: Audit that every study honored its finite variant budget with no locked-test tuning and no repeated OOS selection.
- **Scope**:
  - Reconcile actual variant/grid counts against the declared VariantBudget per study.
  - Confirm no locked-test tuning and no repeated selection on the same OOS.
- **Non-goals**:
  - Promoting any idea.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/audits/variant_budget/**`
  - `docs/futures_core_alpha_pilot/VARIANT_BUDGET_AUDIT.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -f research/futures_core_alpha_pilot_v1/audits/variant_budget/variant_budget_audit.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only variant budget audit (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Every study reconciled against its variant budget; no locked-test tuning or repeated OOS selection.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P24.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P25 — Statistical Reviewer Verdicts

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P24`
- **Purpose**: Produce independent Statistical Reviewer verdicts per surviving idea, independent of the implementer.
- **Scope**:
  - Record ReviewerVerdict per idea citing diagnostics, cost stress, stability, and audits.
  - Enforce reviewer independence from the drafter/implementer/runner.
- **Non-goals**:
  - Self-review; promoting to paper/live.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/reviewer_verdicts/**`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/statistical/**`
  - `docs/futures_core_alpha_pilot/REVIEWER_VERDICTS.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P25.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P25/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/reviewer_verdicts`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only independent statistical reviewer verdicts (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: One independent verdict per surviving idea, citing evidence; reviewer independence enforced.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P25.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P26 — TrialLedger / RejectedIdeaLedger Recording

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P25`
- **Purpose**: Record every run in the TrialLedger and every rejection in the RejectedIdeaLedger so failures are visible.
- **Scope**:
  - Populate TrialLedger records for all studies and RejectedIdea records for all rejections with reasons.
  - Record duplicate-exposure group hints.
- **Non-goals**:
  - Hiding failed ideas; promoting.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/ledgers/**`
  - `docs/futures_core_alpha_pilot/LEDGERS.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.governance.trial_ledger, alpha_system.governance.rejected_idea"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/ledgers`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only TrialLedger + RejectedIdeaLedger records (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: All runs and rejections recorded with reasons; duplicate-exposure hints present.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P26.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P27 — EvidenceDraft and ReferenceCandidateHandoff for Survivors

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P26`
- **Purpose**: Assemble EvidenceDrafts and FactorLibrary-ready ReferenceCandidateHandoffs for survivors only.
- **Scope**:
  - Build EvidenceDraft per survivor (refs to diagnostics, cost, stability, audits, verdict, rejected-idea links).
  - Build FactorCard draft + ReferenceCandidateHandoff for survivors; none if zero survivors.
- **Non-goals**:
  - Treating an EvidenceDraft as a candidate or Reference validation.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/evidence/**`
  - `docs/futures_core_alpha_pilot/EVIDENCE.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P27.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P27/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.evidence.draft, alpha_system.runtime.handoff.reference"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/evidence`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only EvidenceDraft + FactorCard draft + ReferenceCandidateHandoff for survivors (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: EvidenceDrafts complete and FactorLibrary-ready for survivors only; clearly not candidates/Reference validation.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P27.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P28 — PromotionDecision: Reject / Inconclusive / Watch / CandidateResearch

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P27`
- **Purpose**: Record the bounded PromotionDecision per idea using only the allowed states and only with a reviewer verdict for WATCH/CANDIDATE_RESEARCH.
- **Scope**:
  - Assign REJECT / INCONCLUSIVE / WATCH / CANDIDATE_RESEARCH per idea with rationale.
  - Enforce <=2 WATCH/CANDIDATE_RESEARCH and reviewer-verdict prerequisite.
- **Non-goals**:
  - Any forbidden promotion state or capital/live decision.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/promotion/**`
  - `docs/futures_core_alpha_pilot/PROMOTION_DECISIONS.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python -c "import alpha_system.runtime.decisions.states, alpha_system.governance.promotion_gate"`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/promotion`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only PromotionDecision records (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Every idea has an allowed-state decision; WATCH/CANDIDATE require a reviewer verdict; <=2 survivors; no forbidden state.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P28.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P29 — Failure-Mode Handoff for Validation Governance / FactorLibrary / Strategy Reference

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P28`
- **Purpose**: Distill concrete failure modes and survivor handoffs into requirements for the next campaigns.
- **Scope**:
  - Write failure-mode handoffs to ALPHA_VALIDATION_GOVERNANCE_V1, ALPHA_FACTOR_LIBRARY_V1, ALPHA_STRATEGY_REFERENCE_VALIDATION_V1.
  - Translate observed failure modes into concrete next-campaign requirements.
- **Non-goals**:
  - Implementing any next campaign; promoting.
- **Expected files / directories** (allowed_paths):
  - `research/futures_core_alpha_pilot_v1/downstream_handoffs/**`
  - `docs/futures_core_alpha_pilot/DOWNSTREAM_HANDOFFS.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P29.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P29/**`
  - `runs/**`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --smoke`
  - `test -d research/futures_core_alpha_pilot_v1/downstream_handoffs`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only downstream failure-mode handoffs (value-free); docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Concrete failure-mode handoffs for the three next campaigns produced.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P29.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

### FUTCORE-P30 — Acceptance Audit and Closeout

- **Lane**: YELLOW
- **Dependencies**: `FUTCORE-P29`
- **Purpose**: Run the acceptance audit and semantic done-check, record the final verdict, and update the coordinator pointer.
- **Scope**:
  - Verify every acceptance gate, artifact policy, and promotion boundary.
  - Write CLOSEOUT.md with the final verdict and update ACTIVE_CAMPAIGN.md (coordinator).
- **Non-goals**:
  - Any new research; any forbidden claim.
- **Expected files / directories** (allowed_paths):
  - `campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
  - `research/futures_core_alpha_pilot_v1/closeout/**`
  - `docs/futures_core_alpha_pilot/CLOSEOUT.md`
  - `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`
  - `reviews/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30/**`
  - `runs/**`
  - `ACTIVE_CAMPAIGN.md`
- **Forbidden changes**: consumed `src/alpha_system` primitives (runtime/governance/agent_factory/research/experiments/backtest/data/core/signals/strategies/portfolio/management/l2/reports/factors/cli), broker/live/paper/order, raw/canonical data, heavy artifacts (parquet/arrow/feather/dbn/zst), and local DB files. Features/labels are forbidden here (added only in `FUTCORE-P15`).
- **Validation commands**:
  - `git status --short`
  - `python tools/verify.py --all`
  - `python tools/hooks/canary_runner.py`
  - `test -f campaigns/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/CLOSEOUT.md`
  - `grep -q "ALPHA_FUTURES_CORE_ALPHA_PILOT_V1" ACTIVE_CAMPAIGN.md`
  - `git ls-files runs`
- **Artifact policy**: explicit staging only; commit only closeout + final verdict + coordinator pointer update; docs; commit-eligible handoff/review. Never commit `runs/**`, raw/canonical/feature/label values, provider responses, heavy artifacts, or local DB files.
- **Done criteria**: Acceptance audit + semantic done-check pass; final verdict recorded; pointer updated; verify.py --all and canaries pass.
- **Handoff required**: yes — `handoffs/ALPHA_FUTURES_CORE_ALPHA_PILOT_V1/FUTCORE-P30.md`
- **Review required**: required — fresh Claude Opus 4.8 review (Yellow lane)
- **Auto-merge eligibility**: yes (Yellow, auto-merge after PASS/PASS_WITH_WARNINGS review)

