# PHASE_PLAN — ALPHA_IDEA_TO_VERDICT_LOOP_V0

7 phases (`IVL-P00` … `IVL-P06`) on a `dag_wave` scheduler with `max_parallel_phases: 1` and a
serial merge queue. Phases have a **linear** dependency chain (`P00 → P01 → P02 → P03 → P04 →
P05 → P06`) and overlapping `src/alpha_system/cli/`, `src/alpha_system/research_lane/`, and
`tests/` footprints, so the DAG **linearizes to sequential** — no two phases are merge-safe to run
in parallel in this first run. Phase ids / lanes / dependencies / `allowed_paths` are authoritative
in `campaign.yaml`; this file mirrors them and the shape is copied from `campaigns/000-template/`
(the 14-field per-phase contract) and from the conforming `campaigns/DIFFERENTIATED_KILLSHOT_V1/`
bundle (rich wave-map + per-phase prose). Any disagreement between this file and `campaign.yaml` is
a STOP condition.

This is a **research-only** assembly/consolidation campaign: it wires the existing trusted backend
(governance schemas, the value-free probe math, the memory machine) into one canonical idea→verdict
product loop. It adds **no** alpha/profit/tradability/production claim, charters **no** downstream
module (Mining V2, FactorLibrary, AlphaBook, Strategy Sandbox, PA grammar), and touches **no**
FUTSUB-stamped or DIFFERENTIATED_KILLSHOT tooling (those are STOPPED). Lanes are **GREEN/YELLOW
only** — no RED (no paid data, broker, live, paper, order, or new universe; the `needs_paid_data`
fomc/cpi cards migrate as records only and are never tested in V0).

## DAG and parallelism note

The logical dependency is a strict chain because each phase consumes the artifact the previous one
produced: P01 needs the ADR's canonical role contract (P00); P02 needs the emitted canonical objects
(P01); P03 needs the testability gate's PASS precondition (P02); P04 renders P03's readout; P05 wires
P04's verdict into memory; P06 dogfoods the whole P01–P05 loop end to end. Because P01, P02, P03,
P04, P05 all edit `src/alpha_system/cli/idea.py` and/or the shared `src/alpha_system/research_lane/`
package and `tests/unit/cli/test_idea_cli.py`, their footprints **collide**, so they merge serially.
There is **no** parallelizable wave in this run. Merge order equals the wave order.

## Scheduler Wave Map

```text
Wave 0 : IVL-P00  Role-unification ADR + canonical schema map (YELLOW, doc/ADR only, no behavior change)
Wave 1 : IVL-P01  Intake validator + `alpha idea validate` — emit canonical objects + study_kind; migrate 8 Track-A cards (YELLOW)
Wave 2 : IVL-P02  Executable Testability Gate + `alpha idea testability` — 5 fail-closed checks → PASS/FAIL/DATA_GAP, PRE-TEST (YELLOW)
Wave 3 : IVL-P03  Fast exploratory lane bridge — one generic fast_probe(card, setup, slice_spec), outside research/ (YELLOW)
Wave 4 : IVL-P04  Human-readable verdict REPORT.md renderer (YELLOW)
Wave 5 : IVL-P05  Memory wiring + `alpha idea run` end-to-end (YELLOW)
Wave 6 : IVL-P06  Front-door slice passthrough fix + Dogfood DK Track B — degenerate→DATA_GAP, ES_2020_120m→PASS (YELLOW)
```

## Phase contracts

### IVL-P00 — Role-unification ADR + canonical schema map (YELLOW)

- **Lane:** yellow
- **Dependencies:** none
- **Purpose:** record the decided canonical idea-object hierarchy as a durable decision so every
  later phase has one authoritative role contract to build against. Establish that **AlphaSpec is
  the front-door trunk** (the "most ideas killed" machine is already keyed off `alpha_spec_id` in
  `TrialLedger`/`EvidenceBundle`/`PromotionDecision`), that **MechanismCard/SetupSpec are emitted
  sub-objects** carried as lineage sidecars, and that objects are linked at the
  intake/orchestration layer — **not** by mutating the frozen, closed-schema, content-hash-ID
  governance dataclasses.
- **Scope:**
  - Author `ADR-IVL-0001` recording: per-object role contract; AlphaSpec-always-minted front-door
    rule; the three conflict resolutions (`study_kind` lives only on the new IdeaDraft wrapper, not
    on MechanismCard/SetupSpec/AlphaSpec, because their deterministic content-hash IDs hash every
    non-id field; shape-bearing ideas still ride the AlphaSpec trunk with MechanismCard/SetupSpec as
    sidecars; the `RejectedIdea` graveyard accepts only AlphaSpec/HypothesisCard IDs so an AlphaSpec
    must exist before any REJECT write).
  - Author `IDEA_TO_VERDICT_SCHEMA_MAP.md` recording the full Track-A → canonical field map, the
    four fail-closed gaps (`source`, `cost_sensitivity`, `variant_budget`, `duplicate_exposure`),
    the `mechanism_id` lineage rule (canonical `mech_<24-hex>` minted fresh; kebab slug demoted to
    `MechanismCard.source = track_a:<slug>`), and the `data_dependency.class` partition
    (`existing_substrate` = live exemplar; `derivable_from_exchange_calendar` ×5 → DATA_GAP/requeue;
    `needs_paid_data` ×2 → record-only/RED-deferred).
  - Mark the 8 `research/differentiated_substrate_v1/cards/*.json` as a **legacy doc-convention
    schema, migrate-then-retire**.
- **Non-goals:**
  - No code, no schema mutation, no behavior change.
  - No second card class; no `study_kind` field added to any governance dataclass.
  - No retirement/deletion of the legacy cards (that is later, test-gated work).
- **Expected files:**
  - `decisions/ADR-IVL-0001-role-unification.md`
  - `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00-role-unification-adr.md`
- **Forbidden changes:** any `src/`/`tests/` file; the legacy cards; `forbidden_paths` (FUTSUB,
  core-pilot, DK tooling, `core/value_store.py`); secrets; raw data.
- **Validation:** `python tools/verify.py --smoke`; `just frontier-plan ALPHA_IDEA_TO_VERDICT_LOOP_V0`;
  `git diff --stat` shows only `decisions/` + `docs/` + `specs/` changes (REUSE-MAP verifies every
  cited symbol exists in current code).
- **Artifact policy:** commit docs, decisions, and the spec only.
- **Done criteria:** ADR + schema map committed; the three conflict resolutions and the Track-A field
  map/gaps/partition recorded; REUSE-MAP confirms cited symbols; no behavior change; handoff + review
  present.
- **Reuse vs build-new:** **Doc/ADR only.** Reuse: ground-truth re-verification of the live governance
  schemas. Build-new: nothing.
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P00/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

### IVL-P01 — Intake validator + `alpha idea validate` (YELLOW)

- **Lane:** yellow
- **Dependencies:** IVL-P00
- **Purpose:** stand up the front door. `alpha idea validate <idea.yaml>` emits a canonical AlphaSpec
  + MechanismCard (+ SetupSpec when `study_kind=context_not_equal_trigger`), validates the optional
  `study_kind` discriminator on a new IdeaDraft wrapper, and migrates the 8 Track-A cards' content
  into canonical fields as the `main_effect` exemplar set — failing closed if any canonical field
  cannot be populated.
- **Scope:**
  - New `IdeaDraft` wrapper object (greenfield) holding `study_kind`
    (`main_effect | context_not_equal_trigger`) + lineage; `study_kind` validated here, **not** added
    to any frozen governance dataclass.
  - New `cli/idea.py` exposing `register_subparser(subparsers)` with the `validate` subcommand,
    registered via one import alias + one call in `cli/main.py:build_parser()` (mirror `cli/study.py`
    exactly). Handlers delegate to existing validators and wrap domain errors → exit 2.
  - Track-A migration mapper: emit canonical MechanismCard + AlphaSpec per card; mint `mech_<hex>`
    via `create_mechanism_card`/`generate_mechanism_id`; demote kebab slug to `source`; collapse
    `expected_horizon[list] → horizon[str]` (one card per horizon or pre-registered primary); flatten
    `required_features.existing`/`required_labels.existing` to `list[str]`; fail closed on the four
    gap fields. Migration outputs land under a **new canonical dir**, not by editing the legacy cards.
- **Non-goals:**
  - No mutation of MechanismCard/SetupSpec/AlphaSpec dataclasses or their IDs.
  - No retirement of the legacy cards; no `FeatureRequest` implementation or paid-data sourcing for
    `derivable_from_exchange_calendar` / `needs_paid_data` cards.
  - No real-data metric; no probe execution.
- **Expected files:**
  - `src/alpha_system/cli/idea.py`
  - `src/alpha_system/cli/main.py`
  - `src/alpha_system/governance/idea_draft.py`
  - `tests/unit/cli/test_idea_cli.py`
  - `tests/unit/governance/test_idea_draft.py`
  - `tests/unit/governance/test_track_a_migration.py`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01-intake-validator.md`
- **Forbidden changes:** the frozen governance dataclasses' schema/ID logic; the legacy
  `research/differentiated_substrate_v1/cards/*.json` (read-only reference); `forbidden_paths`;
  secrets; raw data.
- **Validation:** narrowest first — `python -m pytest tests/unit/governance/test_idea_draft.py
  tests/unit/governance/test_track_a_migration.py tests/unit/cli/test_idea_cli.py`; then
  `python tools/verify.py --smoke`; `python tools/hooks/canary_runner.py`.
- **Artifact policy:** commit source, curated tests, and the spec only.
- **Done criteria:** `alpha idea validate` registered and emits the canonical object set; `study_kind`
  validated on the wrapper; all 8 cards migrate (day_of_week as `main_effect` exemplar, `mech_<hex>`
  minted, slug→`source`); fails closed on missing `source`/`cost_sensitivity`/`variant_budget`/
  `duplicate_exposure`; a parity test asserts the canonical-vs-card field map; canaries green; handoff
  + review present.
- **Reuse vs build-new:** **Reuse:** `create/validate_mechanism_card`, `create/validate_setup_spec`,
  `validate_alpha_spec`, `generate_mechanism_id`; CLI registration pattern from `cli/study.py` +
  `cli/main.py`. **Build-new:** the `IdeaDraft` wrapper (carries `study_kind` + lineage), `cli/idea.py`,
  the Track-A migration mapper.
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P01/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

### IVL-P02 — Executable Testability Gate + `alpha idea testability` (YELLOW)

- **Lane:** yellow
- **Dependencies:** IVL-P01
- **Purpose:** gate every idea **before** any real metric is computed. `alpha idea testability
  <idea.yaml>` runs five fail-closed checks and returns PASS / FAIL / **DATA_GAP** (a PRE-TEST
  verdict — the shot is not spent on a DATA_GAP).
- **Scope:**
  - New `testability_gate` module under a package **outside** `src/alpha_system/research/` (e.g.
    `src/alpha_system/research_lane/`) so the research no-value-engine boundary test stays green.
  - Five checks: (1) features materialized; (2) labels / path-labels exist; (3) path-label
    **≥2-distinct-class non-degeneracy**; (4) N_eff / MDE plausible; (5) dedup known +
    no-lookahead/`available_ts` satisfiable + surrogate-FDR requirement known.
  - Add the **≥2-distinct-class precondition** to `conditional_probe.py` (today it has only empty-set
    guards), reusing the label-runtime class-count logic (`_distribution_summary` /
    `_class_balance_summary`, which emit `class_count` / `majority_class_count` /
    `minority_class_count`).
  - Wire the `testability` subcommand into `cli/idea.py`.
- **Non-goals:**
  - No real-data metric; no probe scoring (the gate runs BEFORE the metric).
  - No second value loader; no materialization; the gate inspects presence/shape only.
- **Expected files:**
  - `src/alpha_system/research_lane/testability_gate.py`
  - `src/alpha_system/research/conditional_probe.py` (add the ≥2-class guard only)
  - `src/alpha_system/cli/idea.py`
  - `tests/unit/research_lane/test_testability_gate.py`
  - `tests/unit/research/test_conditional_probe_class_guard.py`
  - `tests/unit/cli/test_idea_cli.py`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02-testability-gate.md`
- **Forbidden changes:** placing any new value-loading or gate module under
  `src/alpha_system/research/`; `forbidden_paths`; secrets; raw data.
- **Validation:** `python -m pytest tests/unit/research_lane/test_testability_gate.py
  tests/unit/research/test_conditional_probe_class_guard.py
  tests/unit/research/test_research_no_value_engine.py tests/unit/cli/test_idea_cli.py`; then
  `python tools/verify.py --smoke`; `python tools/hooks/canary_runner.py`.
- **Artifact policy:** commit source, curated tests, and the spec only.
- **Done criteria:** five checks implemented and fail-closed; PASS/FAIL/DATA_GAP returned;
  DATA_GAP is a PRE-TEST verdict (shot not spent); ≥2-class guard added to `conditional_probe.py`;
  research no-value-engine boundary test still green; canaries green; handoff + review present.
- **Reuse vs build-new:** **Reuse:** `_distribution_summary` / `_class_balance_summary` from
  `runtime/diagnostics/label/runtime.py`; the existing `ConditionalProbeError` empty-set guards.
  **Build-new:** the five-check gate orchestrator (in `research_lane/`, never under `research/`).
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P02/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

### IVL-P03 — Fast exploratory lane bridge (YELLOW)

- **Lane:** yellow
- **Dependencies:** IVL-P02
- **Purpose:** build the single missing piece — one generic `fast_probe(card, setup, slice_spec)` that
  loads a bounded **existing** materialized slice and feeds the unchanged value-free probe math
  in-memory, with `promotion_eligible=False`. This generalizes the frozen-to-one-idea `first_light.py`
  and folds the hardcoded ES_2024 `dk_p04_track_b_probe.py` bridge into one parameterized lane.
- **Scope:**
  - New `fast_probe` + `slice_spec` modules under `src/alpha_system/research_lane/` (a package
    **outside** `research/`). The bridge imports `core.value_store.load_parquet_values` (import only;
    no edit to `core/value_store.py`) and uses `runtime.input_resolver.FeatureLabelPackResolver` for
    governed pack-ref → handle resolution, then loads the bounded slice rows and maps the value-store
    schema onto the governance row schema.
  - Feed `build_factor_diagnostics_run` (main_effect) or `evaluate_setup_conditional_probe`
    (context_not_equal_trigger) **in-memory** via their `Iterable[Mapping]` signatures.
  - De-hardcode the ES_2024 paths / instrument / session / label-version map into `slice_spec` inputs.
  - Fail closed with an honest DATA_GAP (no fabricated values) when polars is absent or rows cannot be
    loaded — reusing the `first_light.py` DATA_GAP-vs-probe branch pattern.
- **Non-goals:**
  - No materialization, no scaleout-driver call, no second value loader, no edit to
    `core/value_store.py`.
  - No bypass of the surrogate `ZERO_PASS_MET` gate or the family-budget gate (both are hard
    preconditions inside `evaluate_setup_conditional_probe` and must be satisfied, not removed).
  - No retirement of `first_light.py` / `dk_p04_track_b_probe.py` yet (migrate-then-retire; P06 is the
    subsumption proof). Do not edit the STOPPED DK tool.
- **Expected files:**
  - `src/alpha_system/research_lane/fast_probe.py`
  - `src/alpha_system/research_lane/slice_spec.py`
  - `tests/unit/research_lane/test_fast_probe.py`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03-fast-probe-bridge.md`
- **Forbidden changes:** placing the bridge under `src/alpha_system/research/`; editing
  `core/value_store.py`; importing the value engine from `research/`; `forbidden_paths`; secrets;
  raw data.
- **Validation:** `python -m pytest tests/unit/research_lane/test_fast_probe.py
  tests/unit/research/test_research_no_value_engine.py`; then `python tools/verify.py --smoke`;
  `python tools/hooks/canary_runner.py`.
- **Artifact policy:** commit source, curated tests, and the spec only.
- **Done criteria:** one generic `fast_probe` loads a bounded existing slice and feeds the unchanged
  probe engines in-memory; `promotion_eligible=False`; no materialization / scaleout / second loader;
  honest DATA_GAP on missing data/polars; research no-value-engine boundary test still green; canaries
  green; handoff + review present.
- **Reuse vs build-new:** **Reuse:** `load_parquet_values`, `FeatureLabelPackResolver`, the unchanged
  loader-free probe engines (`build_factor_diagnostics_run`, `evaluate_setup_conditional_probe`), the
  `first_light.py` DATA_GAP branch. **Build-new:** the generic `fast_probe` + `slice_spec` (must live
  outside `research/`).
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P03/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

### IVL-P04 — Human-readable verdict REPORT.md renderer (YELLOW)

- **Lane:** yellow
- **Dependencies:** IVL-P03
- **Purpose:** turn a probe readout + gate outcomes into a governed, human-readable `REPORT.md` so the
  result of any idea is legible at a glance.
- **Scope:**
  - New `verdict_report` renderer under `src/alpha_system/research_lane/`.
  - Render: idea summary; `study_kind`; slice; data/features/labels used; dedup outcome; the five gate
    verdicts; the fast readout including `class_count` / `minority_count` (so a single-class slice is
    self-evident); N_eff / MDE; surrogate state; the verdict
    (REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE) + why + next action; the verdict reason
    cites `VerdictReasonCode`.
- **Non-goals:**
  - No verdict-state machine change; no promotion logic (that is P05); no new reason codes.
- **Expected files:**
  - `src/alpha_system/research_lane/verdict_report.py`
  - `tests/unit/research_lane/test_verdict_report.py`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04-verdict-report.md`
- **Forbidden changes:** `forbidden_paths`; secrets; raw data; any alpha/profit/tradability claim in
  rendered text (research-only language only).
- **Validation:** `python -m pytest tests/unit/research_lane/test_verdict_report.py` (golden-file on a
  fixed readout); then `python tools/verify.py --smoke`.
- **Artifact policy:** commit source, curated tests, and the spec only.
- **Done criteria:** `REPORT.md` renders all required sections incl. `class_count`/`minority_count`;
  verdict + reason code + next action present; research-only language; golden-file test passes;
  handoff + review present.
- **Reuse vs build-new:** **Reuse:** `VerdictReasonCode` (8-value enum) + `validate_verdict_reason_code`.
  **Build-new:** the markdown renderer.
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P04/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

### IVL-P05 — Memory wiring + `alpha idea run` end-to-end (YELLOW)

- **Lane:** yellow
- **Dependencies:** IVL-P04
- **Purpose:** close the loop. `alpha idea run` chains validate → testability → fast_probe → report →
  memory, routing each verdict to the correct memory action through the existing trust spine.
- **Scope:**
  - New `memory_router` under `src/alpha_system/research_lane/` mapping verdict → memory action:
    REJECT → `create_rejected_idea_record` (via `alpha_spec_id`, asserted present, fail closed if
    absent); DATA_GAP → `validate_requeued_verdict_record` requeue; WATCH/CANDIDATE →
    `create_promotion_decision` (requires `reviewer_verdict_id`, never auto-promoted).
  - Wire the `run` subcommand into `cli/idea.py`.
  - Enforce the exploratory rail: `reject_exploratory_promotion_artifact` fails closed on any
    `EXPLORATORY`-stamped artifact reaching a trusted promotion input; FactorLibrary stays
    survivor-only; the exploratory readout is never auto-promoted.
- **Non-goals:**
  - No auto-promotion; no FactorLibrary write; no reviewer-verdict synthesis (a real
    `reviewer_verdict_id` is required for any promotion).
- **Expected files:**
  - `src/alpha_system/cli/idea.py`
  - `src/alpha_system/research_lane/memory_router.py`
  - `tests/unit/cli/test_idea_cli.py`
  - `tests/unit/research_lane/test_memory_router.py`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05-memory-wiring.md`
- **Forbidden changes:** any auto-promotion path; FactorLibrary writes; `forbidden_paths`; secrets;
  raw data.
- **Validation:** `python -m pytest tests/unit/research_lane/test_memory_router.py
  tests/unit/cli/test_idea_cli.py`; then `python tools/verify.py --smoke`;
  `python tools/hooks/canary_runner.py` (incl. `forbidden_exploratory_promotion`).
- **Artifact policy:** commit source, curated tests, and the spec only.
- **Done criteria:** `alpha idea run` routes REJECT→graveyard, DATA_GAP→requeue,
  WATCH/CANDIDATE→reviewer-gated promotion; AlphaSpec ID asserted before any graveyard write;
  exploratory artifacts never auto-promoted (`reject_exploratory_promotion_artifact` fails closed);
  FactorLibrary untouched; canaries green; handoff + review present.
- **Reuse vs build-new:** **Reuse:** `create_rejected_idea_record`, `validate_requeued_verdict_record`,
  `create_promotion_decision`, `reject_exploratory_promotion_artifact(s)`. **Build-new:** the
  verdict→memory-action router.
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

### IVL-P06 — Front-Door Slice Passthrough Fix + Dogfood DK Track B through the loop (YELLOW)

- **Lane:** yellow
- **Dependencies:** IVL-P05
- **Purpose:** first close the verified front-door slice-passthrough gap this dogfood surfaced (any
  slice-bearing `idea.yaml` dies at intake because the validator rejects the slice keys the gate/probe
  read), then prove the assembled loop on a real, pre-existing slice **without** adding any new
  mechanism, feature, label, data, geometry sweep, or promotion — and demonstrate that the testability
  gate spends DATA_GAP on a degenerate slice (shot not spent) and PASSES on a barrier-resolving slice.
- **Scope:**
  - **Front-door slice passthrough fix** (`src/alpha_system/governance/idea_draft.py`): the intake
    validator `_reject_unknown_bundle_fields` rejects every top-level field outside
    `IDEA_BUNDLE_INPUT_FIELDS`, but the slice extractors read top-level slice keys
    (`testability_slice`/`testability_slices`/`slice_spec`/`slice_specs`/`fast_probe_slice`/
    `fast_probe_slice_spec`/`slice`/`slices`) and `cli/idea.py` validates **before** extracting → a
    slice-bearing idea dies at intake. Add a **recognized slice-passthrough field set** so the bundle
    validates-and-ignores those keys (consumed downstream by the gate/probe), **never** folds them into
    the frozen content-hashed AlphaSpec/MechanismCard/SetupSpec (ids byte-identical), and still rejects
    every other undeclared key. Add an **end-to-end regression test** driving a *resolving embedded
    slice* through `alpha idea gate` + `alpha idea run` (the coverage gap this dogfood proved missing).
  - Run `alpha idea gate` on the burned single-class ES_2024 120m slice → expect **Check-3 DATA_GAP
    PRE-TEST** → requeue (shot not spent).
  - Run on the barrier-resolving **ES_2020_120m** slice (verified two-class; coverage matrix records
    `ACCEPTED`, `row_count 313156`) → expect **Check-3 PASS** → `alpha idea run` emits a real probe
    readout + verdict + `REPORT.md`, writes memory, `promotion_eligible=false` throughout.
  - Tolerate an honest DATA_GAP if `ALPHA_DATA_ROOT` is unset in the executor (the `first_light`
    DATA_GAP branch); never fabricate values; never materialize/recompute any FUTSUB producer.
- **Non-goals:**
  - No new mechanism/feature/label/data; no geometry sweep; no promotion.
  - No mutation of the frozen content-hashed MechanismCard/SetupSpec/AlphaSpec dataclasses or folding
    slice metadata into them; no weakening of the intake unknown-field rejection for any non-slice key;
    no edit to the value engine / probe engines / a second value loader.
  - No edit to `tools/differentiated_killshot_v1/**` or `research/futures_substrate_scaleout_v1/**`
    (STOPPED campaigns — load-only reads of materialized ES_2020/ES_2024 packs are permitted; no
    recompute, no materialize, no registry write).
- **Expected files:**
  - `src/alpha_system/governance/idea_draft.py` (front-door slice-passthrough fix)
  - `tests/unit/governance/test_idea_draft.py`, `tests/unit/cli/test_idea_cli.py` (passthrough +
    end-to-end resolving-slice regression tests)
  - `tests/integration/test_ivl_dogfood_track_b.py`
  - `research/idea_to_verdict_loop_v0/dogfood/**` (readout/REPORT outputs; local-or-fixture, no
    committed Parquet/sqlite/data)
  - `docs/IDEA_TO_VERDICT_DOGFOOD.md`
  - `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06-dogfood-track-b.md`
- **Forbidden changes:** any FUTSUB/DK tool or materialized producer; materialize/recompute/registry
  writes; committing Parquet/sqlite/raw data; `forbidden_paths`; secrets.
- **Validation:** `python -m pytest tests/integration/test_ivl_dogfood_track_b.py`; then
  `python tools/verify.py --smoke`; `python tools/hooks/canary_runner.py`; `git ls-files runs` empty.
- **Artifact policy:** commit the integration test, the runbook doc, and value-free readout fixtures
  only; no Parquet/sqlite/data.
- **Done criteria:** the intake validator accepts an idea carrying recognized slice-passthrough keys
  (not folded into the frozen schemas, ids byte-identical) while still rejecting any other undeclared
  key, and an end-to-end test drives a resolving embedded slice through `alpha idea gate` + `run`; gate
  returns DATA_GAP on the degenerate slice (shot not spent, requeued); gate PASSES on ES_2020_120m;
  `alpha idea run` emits a real readout + verdict + `REPORT.md`; memory written; `promotion_eligible=false`
  throughout; honest DATA_GAP tolerated when `ALPHA_DATA_ROOT` unset; no FUTSUB producer touched;
  canaries green; handoff + review present.
- **Reuse vs build-new:** **Reuse:** the entire IVL-P01…P05 loop + the existing local ES_2020_120m
  Parquet (load-only). **Build-new:** the front-door slice-passthrough fix (single-file, additive) + its
  end-to-end regression test + the dogfood integration test + the runbook doc.
- **Handoff requirement:** `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06.md`
- **Review requirement:** `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P06/` (fresh Claude review, YELLOW)
- **Auto-merge eligibility:** no auto-merge; YELLOW requires fresh Claude review before merge.

## If this is too much

Collapse to IVL-P00 → IVL-P03 + IVL-P06: P00 is the role-unification ADR (the trunk decision);
P01 is the intake front door; P02 is the pre-test testability gate; P03 is the one generic fast-lane
bridge — together these are the minimum that lets a researcher hand in an idea, get it screened on a
bounded existing slice, and read a fast value-free readout. Defer P04 (richer REPORT renderer; a
minimal text summary suffices), P05 (memory routing; the readout can be filed manually), and fold the
P06 dogfood into a single ES_2020_120m smoke check on P03. The minimum loop is still research-only,
GREEN/YELLOW, with `promotion_eligible=false` and no downstream module chartered.
