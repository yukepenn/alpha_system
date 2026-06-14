# ALPHA_IDEA_TO_VERDICT_LOOP_V0 — Goal

## Campaign Identity

- Project: `alpha_system`
- Campaign ID: `ALPHA_IDEA_TO_VERDICT_LOOP_V0`
- Workflow: `workflow2`

> Shape source: this file conforms to the live campaign-bundle contract — the
> `campaigns/000-template/` template (6 files: `GOAL.md`, `PHASE_PLAN.md`,
> `campaign.yaml`, `ACCEPTANCE.md`, `RISK_REGISTER.md`, `RUNBOOK.md`) — and follows
> the comprehensive section style of the conforming `campaigns/DIFFERENTIATED_KILLSHOT_V1/`
> bundle. The single campaign pointer is the root `ACTIVE_CAMPAIGN.md`; there is no
> second `ACTIVE_CAMPAIGN.md` in this directory.

## Mission

The backend is trustworthy but the **product loop is missing**. Today a researcher's idea has no
single front door: governance objects exist but are **disconnected siblings** (`AlphaSpec` links only
to `hypothesis_id`; `MechanismCard`/`SetupSpec` carry no `alpha_spec_id`; `StudySpec`/`TrialLedger`/
`EvidenceBundle`/`PromotionDecision` already key off `alpha_spec_id`), the only fast research bridge
is **hand-wired per campaign** (`tools/differentiated_killshot_v1/dk_p04_track_b_probe.py` hardcoded
to ES_2024; `src/alpha_system/research/first_light.py` frozen to one SSRL idea), and the eight
Track-A mechanism documents (`research/differentiated_substrate_v1/cards/*.json`) are a **legacy
doc-convention schema** that no code consumes.

This campaign assembles that backend into **one front door**: a researcher (human or AI) hands in
**any** idea — price-action, VWAP, IC, event, cross-market — and it becomes **one canonical object
family**, gets **quick-screened on a small existing slice**, and (only if it earns it) becomes a
**human-readable, governed, reproducible verdict with memory**. This is **ALPHA_IDEA_TO_VERDICT_LOOP_V0**
(phase prefix `IVL`).

## What success IS

Success is a **working loop**, not a discovery. The campaign is done when a researcher can run a single
front door — `alpha idea validate | testability | run | gate` — and get back:

1. **One canonical object family** from one `idea.yaml`: an `AlphaSpec` front-door trunk (always minted)
   that **emits** a value-free `EXPLORATORY`-stamped `MechanismCard` sub-object (and an optional
   `SetupSpec` when the idea is shape-bearing), linked at the orchestration layer — never by mutating
   the frozen, content-hashed governance dataclasses.
2. A **pre-test Testability Gate** (`PASS` / `FAIL` / `DATA_GAP`) that fails closed **before** any real
   metric is computed, so an untestable or degenerate idea is identified without spending a shot.
3. A **fast exploratory readout** on a bounded **already-materialized** slice — no new materialization,
   no scaleout driver call, no second value loader — with `promotion_eligible=False` always.
4. A **human-readable `REPORT.md`** verdict (`REJECT` / `DATA_GAP` / `INCONCLUSIVE` / `WATCH` /
   `CANDIDATE`) with class counts, N_eff/MDE, surrogate state, the reason, and the next action.
5. **Memory**: `REJECT` → rejected-idea graveyard, `DATA_GAP` → requeue, `WATCH`/`CANDIDATE` →
   reviewer-gated promotion only (never auto), with `FactorLibrary` remaining survivor-only.

The proof is a **dogfood**: the same DK Track-B idea returns a **pre-test `DATA_GAP`** on the burned
single-class ES_2024 120m slice (shot not spent → requeue) and a **real probe readout + verdict** on
the barrier-resolving two-class ES_2020_120m slice — both through the one front door, with
`promotion_eligible=false` throughout.

## What success IS NOT

- **NOT "find alpha."** This campaign builds the *path* an idea travels; it asserts no edge, no
  profitability, no tradability, no production-readiness. The dogfood readout is a loop-proof, not a
  result. (Survivor count is 0 today and this campaign does not change that.)
- **NOT** a strategy backtester, mining engine, FactorLibrary build-out, AlphaBook, strategy sandbox,
  or PA grammar pack. No downstream module is chartered or built.
- **NOT** a second PnL/value truth. The research probe math stays value-free and in-memory; the only
  value loader (`core.value_store.load_parquet_values`) is **imported** into a new bridge package
  **outside** `src/alpha_system/research/`, never edited, and never crosses the `research/` boundary.

## Final Capabilities

- A canonical idea-object hierarchy, recorded as an ADR and a schema map: `idea.yaml` (IdeaDraft, the
  new home of the optional `study_kind` discriminator) → **AlphaSpec front-door trunk** → emitted
  `MechanismCard` (+ optional `SetupSpec`) → `FeatureRequest`/`LabelSpec` → `StudySpec` →
  `EvidenceBundle`/`ReviewerVerdict`/`TrialLedger` → `Rejected`/`Requeue`/`Candidate`/`FactorLibrary`
  (survivor-only, gated).
- An `alpha idea` CLI front door (`validate`, `testability`, `run`, `gate`) registered the same way as
  every existing per-domain CLI module.
- The eight Track-A mechanism documents migrated into the canonical line (content-map + structural
  enrichment, minting real `mech_<hash>` ids and preserving the kebab slug as lineage `source`), with
  a parity test — **not** a parallel card class.
- A reusable five-check Executable Testability Gate that returns a pre-test `PASS`/`FAIL`/`DATA_GAP`,
  including a new `>=2`-distinct-class precondition.
- One generic, slice-bounded fast exploratory lane bridge (`fast_probe`) that generalizes the two
  bespoke bridges and feeds the unchanged research probe engines in-memory.
- A human-readable verdict `REPORT.md` renderer and verdict→memory wiring through the existing
  governance kill-trunk.
- A dogfood that exercises the whole loop end-to-end on existing data with no new mechanism, feature,
  label, data, geometry sweep, or promotion.

## Non-Goals

- No discovery claim; no alpha/profit/tradability/production language anywhere.
- No downstream module: no Mining V2, FactorLibrary build-out, AlphaBook, Strategy Sandbox, or PA
  grammar pack.
- No new value loader, no second PnL truth, no edit to `core/value_store.py`, no research→reference-sim
  bridge inside `src/alpha_system/research/`.
- No materialization, no scaleout driver call, no registry write, no `feature`/`label materialize`,
  no `--force-recompute` — the loop reads already-materialized slices load-only.
- No mutation of the frozen, content-hashed `AlphaSpec` / `MechanismCard` / `SetupSpec` schemas
  (`study_kind` lives only on the new IdeaDraft intake wrapper).
- No deletion of the Track-A cards on suspicion: migrate-then-retire with a parity test, and only after
  the canonical line subsumes them (retirement is a later phase, not this V0).
- No touching the STOPPED campaigns: `research/futures_substrate_scaleout_v1/**`,
  `research/futures_core_alpha_pilot_v1/**`, and `tools/differentiated_killshot_v1/**` and
  `src/alpha_system/research/track_a_scorer.py` are read-only references, never edited.
- No `fomc`/`cpi` card testing — those are `needs_paid_data`, deferred, migrated as records only.

## Automation Authority

- Lanes: **GREEN and YELLOW only**. Every phase is YELLOW (material engineering/research requiring a
  fresh Claude Opus review), including the doc-only ADR phase (IVL-P00), because the ADR is the
  load-bearing architecture the whole bundle depends on.
- **NO RED lane**: no paid data, no broker, no live or paper trading, no orders, no new universe, no
  capital. RED scope variables (`PROJECT_OP_AUTHORIZED`/`PROJECT_OP_SCOPE`/`PROJECT_OP_EXPIRES`) are
  not required and must not be armed for this campaign.
- Merge policy: human-gated; `yellow_requires_claude_review: true`, `red_auto_merge: false`. No
  autonomous merge or deploy.
- `runs/**` is local-only runtime state; it must never be staged or committed. Commit-eligible handoffs
  live under `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>.md`; review artifacts under
  `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>/**`.

## Definition of Campaign Done

All seven phases (IVL-P00..P06) complete and independently reviewed; the canonical hierarchy is
recorded as an ADR + schema map; `alpha idea validate | testability | run | gate` is registered and
exercised; the eight Track-A cards are migrated with a parity test (kebab slug preserved as lineage,
real `mech_<hash>` minted); the five-check Testability Gate returns pre-test `PASS`/`FAIL`/`DATA_GAP`
with the `>=2`-class precondition; one generic `fast_probe` bridge feeds the unchanged probe engines
in-memory with `promotion_eligible=False`; the `REPORT.md` renderer and verdict→memory wiring use the
existing kill-trunk; the DK Track-B dogfood yields a pre-test `DATA_GAP` on the burned single-class
ES_2024 120m slice and a real readout + verdict on ES_2020_120m, with a `REPORT.md` emitted and memory
written and `promotion_eligible=false` throughout; all invariants hold; no FUTSUB/DK producer is
touched; `git ls-files runs` stays empty; a campaign `RUN_SUMMARY` exists; research-only language is
maintained throughout.

## Final Acceptance Pointer

See `ACCEPTANCE.md`.
