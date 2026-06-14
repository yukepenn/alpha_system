# DK-P00 — Bootstrap, FDR Active-Subset Restatement, and REUSE-MAP/Scope Lock

---
campaign_id: DIFFERENTIATED_KILLSHOT_V1
phase_id: DK-P00
lane: YELLOW
status: draft
dependencies: []
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Land the campaign control plane and the **two load-bearing pre-registration artifacts** that gate
every later phase, **without writing any code, engine change, or real-data metric**:

1. Confirm the 6-file campaign bundle is present and self-consistent, and confirm the
   coordinator-set `ACTIVE_CAMPAIGN.md` pointer resolves to `DIFFERENTIATED_KILLSHOT_V1`.
2. Write the **FDR active-subset RESTATEMENT** — the *FDR-before-metric* gate. It is a value-free
   pre-registration NOTE that names the active mechanism surface and the effective pooled
   hypothesis count for THIS run, with a `created_at` that **predates the earliest variant
   attempt**. It is explicitly **NOT** a `BudgetAmendmentRecord` (that object is strictly-increasing
   and cannot encode a downward re-scope).
3. Write the **REUSE-MAP + SCOPE lock** — pin the exact machinery later phases must REUSE (not
   rebuild) and the explicit OUT-of-scope list, so no later phase scope-creeps, rebuilds a
   governance object, or inspects a metric before the surface is pre-registered.

This phase is YELLOW (fresh Claude Opus review required) because the FDR restatement is the
load-bearing gate the entire kill-shot's evidence chain depends on: if the active surface or the
pooled count is wrong, every downstream surrogate-FDR and verdict readout is mis-calibrated.

## Context

- **Bundle (already authored by the coordinator, confirmed present):**
  `campaigns/DIFFERENTIATED_KILLSHOT_V1/{GOAL.md, PHASE_PLAN.md, ACCEPTANCE.md, RISK_REGISTER.md,
  RUNBOOK.md, campaign.yaml}` (6 files). `campaign.yaml` is the binding contract; this spec EXPANDS
  the locked `DK-P00` entry and may not add, remove, or change its scope.
- **Pointer:** `ACTIVE_CAMPAIGN.md` currently points at the just-completed
  `STRATEGY_SHAPED_RESEARCH_LANE_V0`. This phase confirms / sets the pointer so
  `grep -q "DIFFERENTIATED_KILLSHOT_V1" ACTIVE_CAMPAIGN.md` passes. The committed pointer describes
  intent and lags the live run; live phase status comes from `tools/frontier/status_doctor.py`, not
  this file.
- **Carried pre-registration inputs (REUSED, not re-derived):**
  - `research/differentiated_substrate_v1/FDR_BUDGET.md` — event-calendar family,
    `family_id = family-differentiated-substrate-v1-event-calendar`, **`family_budget = 6`** pooled
    tests. The carried budget pools `{fomc_drift, cpi_surprise_reversion, opex_pinning,
    month_end_flow}`; the restatement keeps that family-level cap **unchanged** but records that
    `fomc_drift` and `cpi_surprise_reversion` are DEFERRED (needs_paid_data) this run, leaving
    `opex_pinning 1 + month_end_flow 1 = 2` event-calendar tests *active*.
  - `research/differentiated_substrate_v1/FDR_BUDGET_PRIORITY_2_3.md` — flow-seasonality family,
    **`family_budget = 4`**; active here = `day_of_week 1 + roll_week 1 + open_close 2 = 4`.
  - `research/differentiated_substrate_v1/cards/*.json` — MechanismCards exist for
    `day_of_week_effect, opex_pinning, month_end_flow, month_end_rebalance_flow,
    open_close_auction_flow, roll_week_flow, fomc_drift, cpi_surprise_reversion`. The
    `overnight/` directory holds only a design note (`OVERNIGHT_FAMILY_DESIGN_NOTE.md`) and **no
    cards** — confirming the overnight family is not exercised this run.
- **Relevant HARD INVARIANTS (this phase is the gate that arms them):**
  - **FDR before metric.** No real-data metric is inspected before (a) this restatement is committed
    (predating any variant attempt) AND (b) the DK-P02 surrogate-FDR calibration yields
    `ZERO_PASS_MET`. This phase produces (a).
  - **Downward re-scope is a NOTE, not a BudgetAmendmentRecord.**
    `governance/variant_ledger.py:create_budget_amendment_record(... prior_budget, new_budget ...)`
    enforces a strictly-increasing budget (`new_budget > prior_budget`); it structurally cannot
    encode a downward restatement, so the restatement is a plain value-free Markdown pre-registration
    note. This must be stated explicitly in the artifact.
  - **Bounded surface.** event-calendar `family_budget = 6` and flow-seasonality `family_budget = 4`
    are carried UNCHANGED; per-mechanism `variant_budget = horizon count`; instrument-pooled
    (ES/NQ/RTY) is ONE test per mechanism; NO grid, NO horizon sweep, NO per-instrument split.
  - **Single-factor path byte-unchanged; strictly additive.** Nothing in this phase edits
    `strategies/templates.py`, the value engine, or any FUTSUB / core-pilot artifact.
  - **Research-only language; allowed outputs only.** No alpha/tradability/profitability claim; no
    promotion. Allowed outputs are REJECT / INCONCLUSIVE+reason_code / WATCH / CANDIDATE_RESEARCH.
  - **`git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.**

## Scope

Locked from `campaign.yaml` `DK-P00.scope`; expanded here with concrete, executor-actionable detail.
**This phase writes documents only — no code, no engine change, no metric.**

1. **Confirm the bundle + pointer.**
   - Verify the 6 bundle files exist under `campaigns/DIFFERENTIATED_KILLSHOT_V1/` and that
     `campaign.yaml` parses (`yaml.safe_load`). Verify GOAL/PHASE_PLAN/ACCEPTANCE/campaign.yaml agree
     on the 6-phase plan (DK-P00..DK-P05), the two tracks, and the active-subset arithmetic; record
     any inconsistency in the handoff (do not silently "fix" the contract).
   - Confirm/set the `ACTIVE_CAMPAIGN.md` pointer so it names `DIFFERENTIATED_KILLSHOT_V1` (the
     `grep -q` check passes). Keep the pointer factual and research-only; it is intent, not live
     status.

2. **Write `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md`** — value-free,
   NO metric/IC/return/diagnostic value. It RESTATES the active surface for THIS run:
   - **Active mechanisms (5):** `day_of_week_effect`, `opex_pinning`, `month_end_flow`
     (`month_end_rebalance_flow` folded into `month_end_flow`), `roll_week_flow`,
     `open_close_auction_flow`.
   - **DEFERRED (needs_paid_data, OUT this round):** `fomc_drift`, `cpi_surprise_reversion`.
   - **Not exercised (no cards this round):** the governed-overnight family.
   - **Per-mechanism `variant_budget` = horizon count:** day_of_week `1`, opex `1`, month_end `1`,
     roll_week `1`, open_close `2`.
   - **Per-family budgets carried UNCHANGED** from the FDR budget docs: event-calendar
     `family_budget = 6` (from `FDR_BUDGET.md`), flow-seasonality `family_budget = 4` (from
     `FDR_BUDGET_PRIORITY_2_3.md`). The family caps do not move; only the *active* subset is restated.
   - **Active effective pooled surface = 6:** event-calendar `{opex 1 + month_end 1} = 2` +
     flow-seasonality `{day_of_week 1 + roll_week 1 + open_close 2} = 4` = **6** active pooled tests.
     The arithmetic must appear explicitly and reconcile against the per-mechanism counts.
   - **Provenance + ordering:** include provenance (which carried docs/cards this restates, with
     paths) and a `created_at` timestamp that **predates any variant attempt** (this phase runs
     before DK-P01 builds flags and before DK-P02 authors any StudySpec). State that this ordering is
     the FDR-before-metric guarantee.
   - **Why no BudgetAmendmentRecord:** include an explicit paragraph stating the restatement is a
     value-free pre-registration NOTE, NOT a `BudgetAmendmentRecord`, because
     `create_budget_amendment_record` (`governance/variant_ledger.py`) requires
     `new_budget > prior_budget` (strictly increasing) and therefore cannot represent a *downward*
     re-scope of the carried family budgets to the active subset.

3. **Write `docs/differentiated_killshot_v1/REUSE_MAP.md` + `docs/differentiated_killshot_v1/SCOPE.md`.**
   - **REUSE_MAP.md** pins the REUSED machinery (REUSE before build — never rebuild a governance
     object):
     - Governance: `governance/study_spec.py`, `governance/variant_ledger.py`,
       `governance/surrogate_run.py`, `governance/setup_spec.py`, `governance/mechanism_card.py`,
       `research/conditional_probe.py`, `governance/trial_ledger.py`,
       `governance/pooled_hypothesis.py`, `governance/feature_request.py`.
     - Features: `features/families/session/**` (existing day_of_week / open-close members reused;
       DK-P01 ADDS five new SESSION_CALENDAR_ROLL flags additively, not a new family).
     - Labels: `labels/roll_guard.py` (`classify_roll_window` for the in-roll-window flag).
     - Tooling: `tools/discovery_rigor_floor/run_real_surrogate_calibration.py` (surrogate-FDR
       zero-pass calibration runner).
     - Diagnostics: the runtime factor diagnostics (directional / point-biserial IC, buckets,
       walk-forward) used by DK-P03.
     - Value loading: `core/value_store.load_parquet_values` is a **tools/runtime-only** loader —
       `research/` NEVER imports it; values are loaded by `tools/`/`runtime/` and INJECTED into the
       pure research probe (no research→reference-sim bridge, no second PnL truth).
     For each reused object, name the file/symbol and the phase that consumes it; do not copy or fork
     any of them.
   - **SCOPE.md** pins the explicit OUT-of-scope list:
     - `fomc_drift`, `cpi_surprise_reversion` (DEFERRED until a feed is onboarded — needs_paid_data).
     - The governed-overnight family (no cards this round).
     - Per-instrument (ES/NQ/RTY) splits — pooled is ONE test per mechanism.
     - Geometry / horizon sweeps and grids.
     - Any edit to the single-factor template (`SINGLE_FACTOR_THRESHOLD_TEMPLATE` /
       `strategies/templates.py`) or `StudyConfig.factor_id`.
     - Any edit to FUTSUB / core-pilot research artifacts
       (`research/futures_substrate_scaleout_v1/**`, `research/futures_core_alpha_pilot_v1/**`).
     SCOPE.md also restates the closed verdict taxonomy (REJECT / INCONCLUSIVE+code / WATCH /
     CANDIDATE_RESEARCH) and the research-only / no-promotion stance.

## Non-Goals

Locked from `campaign.yaml` `DK-P00.non_goals`, plus the structurally-implied guards:

- **Any code; any engine change; ANY real-data metric, IC, return, or diagnostic value.** This phase
  is documents only.
- Authoring StudySpecs (DK-P02), building calendar flags (DK-P01), running diagnostics (DK-P03), or
  the Track B probe (DK-P04) — those are later phases.
- Creating or amending any `BudgetAmendmentRecord`, VariantLedger record, or surrogate run — the
  restatement is a plain note, and no ledger object is written here.
- Editing the carried FDR budget docs (`FDR_BUDGET.md`, `FDR_BUDGET_PRIORITY_2_3.md`) or any
  MechanismCard JSON — they are inputs, reused unchanged; the restatement references them.
- Modifying `SINGLE_FACTOR_THRESHOLD_TEMPLATE`, the value engine, or any FUTSUB / core-pilot
  artifact.
- Any promotion, FactorLibrary entry, AlphaBook/Strategy-Reference, or paper/live/broker action.
- Adding any runtime dependency (`numpy`/`pandas`/`polars` stay unimportable) or any new paid data.

## Expected Files (illustrative, not prescriptive)

- `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md` — new (the FDR-before-metric
  gate; value-free; active surface = 6; provenance + pre-variant `created_at`; explicit no-amendment
  rationale).
- `docs/differentiated_killshot_v1/REUSE_MAP.md` — new (pinned reused machinery, per-symbol + per-phase).
- `docs/differentiated_killshot_v1/SCOPE.md` — new (explicit OUT-of-scope list + verdict taxonomy +
  research-only stance).
- `ACTIVE_CAMPAIGN.md` — edit (point at `DIFFERENTIATED_KILLSHOT_V1`).
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P00.md` — new (commit-eligible handoff).
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P00/**` — new (commit-eligible YELLOW review artifacts).

No `runs/` path appears in this list; run-local artifacts stay local-only (see Artifact Policy).

## Interfaces / Contracts

- **FDR restatement is a NOTE, structurally distinct from a ledger amendment.** It is Markdown, not a
  `BudgetAmendmentRecord`. `governance/variant_ledger.py:create_budget_amendment_record(payload …
  prior_budget, new_budget …)` validates strictly-increasing budgets, so a downward active-subset
  restatement cannot be expressed as an amendment; the note records the active subset declaratively.
- **Arithmetic contract (must reconcile exactly):** active mechanisms `{day_of_week, opex, month_end,
  roll_week, open_close}`; per-mechanism `variant_budget = {1, 1, 1, 1, 2}`; event-calendar active
  `{opex 1 + month_end 1} = 2` against carried `family_budget = 6`; flow-seasonality active
  `{day_of_week 1 + roll_week 1 + open_close 2} = 4` against carried `family_budget = 4`; **active
  effective pooled surface = 2 + 4 = 6**. The restatement states both the carried family caps and the
  active subset and shows they reconcile.
- **Ordering contract:** `created_at` in the restatement predates any variant attempt; DK-P01 and
  DK-P02 may not author a variant before this note is committed. This is the FDR-before-metric
  precondition the ACCEPTANCE invariant names.
- **REUSE-MAP contract:** every later phase resolves its machinery to the symbols pinned here;
  `core/value_store.load_parquet_values` is reachable only from `tools/`/`runtime/`, never imported
  by `research/` (the no-second-PnL-truth boundary).
- The bundle/pointer checks are pure file/parse/grep assertions — no provider, network, merge, or
  external calls.

## Forbidden Changes

- Editing any path under `forbidden_paths` (`src/alpha_system/execution/**`, `broker/**`, `live/**`,
  `portfolio/**`, `management/**`, `backtest/**`, `l2/**`, `agent_factory/**`,
  `core/value_store.py`, `strategies/templates.py`, `research/futures_substrate_scaleout_v1/**`,
  `research/futures_core_alpha_pilot_v1/**`, all `data/**`, any
  `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`).
- Writing any code, engine change, or test in this phase (DK-P00 is documents-only).
- Inspecting, computing, or recording ANY real-data metric, IC, return, bucket, or diagnostic value
  in the restatement or any artifact — the restatement is value-free by contract.
- Encoding the downward active-subset restatement as a `BudgetAmendmentRecord` or any
  ledger/amendment object (it is strictly-increasing and cannot re-scope down) — it must be a plain
  value-free pre-registration NOTE.
- Changing the carried family budgets (event-calendar 6, flow-seasonality 4), expanding the mechanism
  surface, or adding any grid / horizon sweep / per-instrument split.
- Promoting fomc/cpi off DEFERRED, adding paid data, or exercising the overnight family.
- Adding a runtime dependency (`numpy`/`pandas`/`polars`); committing secrets, raw/canonical/factor/
  label data, caches, DBs, or heavy artifacts.
- `git add .`, `git add -A`, force push, auto-merge, deployment, or any broker/live call.
- Any alpha/tradability/profitability claim, FactorLibrary promotion, or second PnL truth.

## Validation

Run from the repo root. All commands are local-only, safe, and make **no** provider, network, merge,
or external calls. These mirror `campaign.yaml` `DK-P00.checks`.

```bash
# 1) Bundle present + parses.
test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/GOAL.md
test -f campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml
python -c "import yaml; yaml.safe_load(open('campaigns/DIFFERENTIATED_KILLSHOT_V1/campaign.yaml'))"

# 2) FDR restatement committed.
test -f research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md

# 3) Pointer set.
grep -q "DIFFERENTIATED_KILLSHOT_V1" ACTIVE_CAMPAIGN.md

# 4) Repo smoke.
python tools/verify.py --smoke

# 5) Safety canaries must remain all-PASS (planted_fake_alpha, true-alpha pair,
#    forbidden_second_pnl_truth, forbidden_exploratory_promotion, governance_random_target,
#    forbidden_scope_drift).
python tools/hooks/canary_runner.py

# 6) Run-artifact discipline: must print nothing.
git ls-files runs
```

Additional manual confirmations for this documents-only phase (record results in the handoff):

```bash
# REUSE-MAP + SCOPE present.
test -f docs/differentiated_killshot_v1/REUSE_MAP.md
test -f docs/differentiated_killshot_v1/SCOPE.md

# Value-free guarantee: the restatement carries no metric/IC/return numerals beyond the
# pre-registered budget/horizon counts. Reviewer reads the file adversarially for any leaked value.
```

Broaden to the authoritative suite (`python tools/verify.py --all`) only if a shared check appears
affected; run it in a clean shell with `FRONTIER_*` env unset to avoid the known driver-env false
negative. Record any skipped check and its reason in the handoff.

## Artifact Policy

Run artifacts are local-only and must never be committed:

- `runs/**` is **local-only runtime state** (run state, events, costs, STOP, run-local
  `handoff.md`/`review.md`/`verdict.json`, checks, repair attempts) — local audit and resume only.
- The run-local `handoff.md`/`review.md`/`verdict.json` under `runs/<run_id>/...` must **never** be
  staged or committed.
- The commit-eligible handoff goes under `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P00.md`.
- Commit-eligible review notes + verdict go under `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P00/**`.
- `runs/.gitkeep`, `runs/README.md`, and `runs/**` must **not** appear in Allowed Paths.
- `git ls-files runs` must return empty.
- Never commit: `runs/**`, any `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`,
  `data/raw/**`, `data/canonical/**`, `secrets/**`, `**/*.key`.

### Allowed Paths (commit-eligible — explicit staging only)

These are the **only** paths this phase may stage and commit. Stage by explicit path; never
`git add .` / `git add -A`; never force push.

- `campaigns/DIFFERENTIATED_KILLSHOT_V1/**`
- `research/differentiated_substrate_v1/**`
- `docs/differentiated_killshot_v1/**`
- `ACTIVE_CAMPAIGN.md`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P00.md`
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P00/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` — local audit and resume only. **No `runs/` path appears under Allowed Paths above.**

## Allowed Paths

(See Artifact Policy → Allowed Paths above. Mirrors `campaign.yaml` `DK-P00.allowed_paths`, minus
`runs/**`, which is local-only and never staged.)

## Allowed Test Paths

- None. DK-P00 is documents-only and adds no tests. The validation commands above are the existing
  smoke + canary + bundle/parse/grep checks; do not weaken, skip, or add visible test-only branches
  to any existing test or canary.

## Done Criteria

Locked from `campaign.yaml` `DK-P00.done_criteria`:

- Bundle consistent (6 files present, GOAL/PHASE_PLAN/ACCEPTANCE/campaign.yaml agree); pointer set
  (`grep -q "DIFFERENTIATED_KILLSHOT_V1" ACTIVE_CAMPAIGN.md` passes); `campaign.yaml` parses.
- `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md` committed — value-free,
  `created_at` predates any variant attempt, fomc/cpi DEFERRED, overnight not exercised, arithmetic
  reconciles to **active surface = 6** (event-calendar 2 + flow-seasonality 4), and it states
  explicitly why a `BudgetAmendmentRecord` is not used (strictly-increasing).
- `docs/differentiated_killshot_v1/REUSE_MAP.md` + `SCOPE.md` committed (reused machinery pinned per
  symbol/phase; OUT-of-scope list explicit; `load_parquet_values` marked tools/runtime-only).
- `python tools/verify.py --smoke` and `python tools/hooks/canary_runner.py` pass.
- `git ls-files runs` returns empty; explicit staging only; no edits under `forbidden_paths`; no
  code/engine/metric change.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write the commit-eligible handoff at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P00.md`: scope
delivered; exact validation commands run with results; any skipped check + reason; files changed by
path; and explicit confirmation that (a) no code/engine/metric was written and the restatement is
value-free, (b) the restatement's `created_at` predates any variant attempt and the artifact states
why a `BudgetAmendmentRecord` is not used, (c) the active-surface arithmetic reconciles to 6
(event-calendar 2 + flow-seasonality 4) and fomc/cpi are DEFERRED / overnight not exercised, (d) the
REUSE_MAP pins the reused symbols and marks `load_parquet_values` tools/runtime-only, (e) the
`ACTIVE_CAMPAIGN.md` pointer names the campaign, (f) `git ls-files runs` is empty and staging was
explicit with no edits under `forbidden_paths`. The run-local `runs/<run_id>/.../handoff.md` stays
local-only and must not be staged.

## Review Requirements

YELLOW lane requires a fresh Claude Opus review. Commit-eligible review notes + verdict belong under
`reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P00/**`; run-local `review.md`/`verdict.json` stay under
`runs/<run_id>/...` and are not committed. The reviewer must adversarially confirm: the restatement
is genuinely value-free (no leaked IC/return/diagnostic numeral); the active surface and arithmetic
are correct (5 active mechanisms, per-mechanism variant_budget = horizon count, active pooled = 6,
carried family budgets unchanged at 6 / 4); `created_at` predates any variant and the FDR-before-metric
ordering is explicit; the artifact is a NOTE not a `BudgetAmendmentRecord` with the strictly-increasing
rationale stated; fomc/cpi are DEFERRED (needs_paid_data) and overnight is not exercised; the
REUSE_MAP pins reused machinery (not rebuilds) with `load_parquet_values` tools/runtime-only and the
no-research→sim-bridge boundary; SCOPE's OUT-of-scope list bars fomc/cpi, overnight, per-instrument
splits, geometry/horizon sweeps, and single-factor-template / FUTSUB-artifact edits; smoke + canaries
pass; `git ls-files runs` empty; explicit staging; no edits under `forbidden_paths`; research-only
language with no promotion/alpha/tradability claim.

## Auto-Merge / Review Policy

This spec authorizes no PR creation, no auto-merge, and no deployment. Merge gating is the Ralph
driver's responsibility under the YELLOW lane policy (`review_required: true`; block on critical /
test-tamper / boundary violation) and human authorization — not this spec. `auto_pr` / `auto_merge`
in `campaign.yaml` are driver-loop hints, not a grant for this spec to self-approve or merge.

## Repair-or-Rollback

- **In-scope repair only:** fix the restatement arithmetic/provenance/ordering, the REUSE_MAP/SCOPE
  content, or the pointer within the Allowed Paths; do not expand scope to fix unrelated findings.
- **Rollback:** every change is a Markdown document or the pointer edit; revert
  `FDR_ACTIVE_SUBSET_RESTATEMENT.md`, `REUSE_MAP.md`, `SCOPE.md`, and the `ACTIVE_CAMPAIGN.md` edit to
  restore the prior state with no code, migration, or data change.
- **STOP / escalate (do not auto-proceed):** any pressure to write code/metrics in this phase, encode
  the restatement as a `BudgetAmendmentRecord`, change the carried family budgets, expand the active
  mechanism surface (un-defer fomc/cpi, add the overnight family, split per-instrument, add a sweep),
  edit the single-factor template / value engine / FUTSUB artifacts, add a dependency, or commit a
  `runs/`/data/secret artifact — treat as out-of-scope and surface to the user. A detected bundle
  inconsistency in `campaign.yaml` is reported in the handoff, not silently patched.
