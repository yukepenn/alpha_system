# ACCEPTANCE — ALPHA_IDEA_TO_VERDICT_LOOP_V0

> Shape source: `campaigns/000-template/ACCEPTANCE.md` (the 6-file bundle requirement)
> and the rich conforming example `campaigns/DIFFERENTIATED_KILLSHOT_V1/ACCEPTANCE.md`
> (campaign-level invariants + per-phase gates + campaign-done). Phase IDs / deps / lanes
> here must stay identical to `campaign.yaml`, `PHASE_PLAN.md`, and the 7 spec files under
> `specs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P0n-<slug>.md`. Research-only language throughout.

## Campaign-level invariants (every phase)

- **Assembly + consolidation, never mass deletion.** The work links and reuses the existing
  trust spine; it does not rebuild it. The governance record classes (`alpha_spec.py`,
  `mechanism_card.py`, `setup_spec.py`, `study_spec.py`) are frozen, slotted, closed-schema
  dataclasses and stay **byte-unchanged** — no field is added to any of them (doing so re-hashes
  every locked content-addressed ID and breaks `validate_schema(allowed_fields==required_fields)`).
  Objects are linked at the **intake/orchestration layer** (`cli/idea.py` + a new `IdeaDraft`
  wrapper + lineage sidecar), not by schema mutation.
- **No second value/PnL truth.** `research/` imports zero `core.value_store` /
  `backtest` / `management` / `fast_path`; the boundary test
  `tests/unit/research/test_research_no_value_engine.py` stays green (it rglobs `research/**`
  and fails on any `core.value_store` import or the literal `load_parquet_values` token). The
  fast-lane bridge lives in a NEW package **outside** `research/` (e.g.
  `src/alpha_system/research_lane/`); it imports `load_parquet_values` there and feeds
  already-injected in-memory rows to the unchanged, loader-free probe engines
  (`build_factor_diagnostics_run`, `evaluate_setup_conditional_probe`).
- **FDR / surrogate gate before any real metric, never bypassed.** The
  `_require_zero_pass_surrogate_gate` precondition inside `evaluate_setup_conditional_probe`
  (`conditional_probe.py:348`, raising unless `threshold_verdict == ZERO_PASS_MET`) is preserved;
  the loop never inspects a real-data IC/return/diagnostic value before the testability gate
  passes and the surrogate-FDR requirement is satisfied. `DATA_GAP` is a PRE-TEST verdict (the
  shot is not spent).
- **Exploratory is never auto-promoted.** `promotion_eligible` stays hardcoded `False`
  (`conditional_probe.py:147` / `:398`); `reject_exploratory_promotion_artifact(s)` fails closed
  on any `EXPLORATORY`-stamped artifact reaching a trusted promotion input;
  `FactorLibrary` stays survivor-only and GATED (survivor count = 0 today, unchanged by this
  campaign). Any promotion uses `create_promotion_decision`, which requires a
  `reviewer_verdict_id`.
- **No new dependency, no new data, no RED.** No paid data, broker, live, paper, order, or new
  universe; the `fomc` / `cpi` Track-A cards are migrated as **record-only** (data_dependency
  class `needs_paid_data`, deferred) and never tested in V0. No `feature`/`label materialize`,
  no registry write, no scaleout-driver call. FUTSUB-stamped and DK-stamped artifacts/tools are a
  STOPPED campaign and are **not touched** (read-only `load_parquet_values` of already-materialized
  Parquet is the only contact, and only in IVL-P06's dogfood).
- **Allowed verdicts only.** `REJECT / DATA_GAP / INCONCLUSIVE (+reason_code) / WATCH /
  CANDIDATE`. Verdict reasons cite `VerdictReasonCode` (the 8-value closed enum via
  `validate_verdict_reason_code`). No alpha / profitability / tradability / production claim.
- **Artifact discipline.** `git ls-files runs` empty; explicit staging only; no edits under
  `forbidden_paths`; no data / Parquet / SQLite / secret committed. Commit-eligible handoffs under
  `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>.md`, reviews under
  `reviews/ALPHA_IDEA_TO_VERDICT_LOOP_V0/<PHASE_ID>/**`.
- **Per-lane checks pass or are documented.** `python tools/verify.py --smoke` and
  `python tools/hooks/canary_runner.py` all-PASS for every phase; the narrowest relevant tests run
  first, broadening when shared behavior changes. Local-only `verify.py --all` failures that are
  pre-existing env/fixture issues (CI-green) are documented, not silently skipped.

## Per-phase acceptance

### IVL-P00 (YELLOW) — Role-unification ADR + canonical schema map
- `decisions/ADR-IVL-0001-role-unification.md` and `docs/IDEA_TO_VERDICT_SCHEMA_MAP.md` committed;
  **no behavior change** (`git diff --stat` touches only `decisions/` + `docs/`).
- ADR records, grounded against current code: AlphaSpec is the front-door / kill-trunk (everything
  already keys off `alpha_spec_id`); MechanismCard (`EXPLORATORY`-stamped) and optional SetupSpec
  are emitted **sub-objects / lineage sidecars**, not replacements; the optional `study_kind`
  discriminator (`main_effect` | `context_not_equal_trigger`) lives only on the new `IdeaDraft`
  wrapper (greenfield — `grep study_kind src/alpha_system/governance/` is empty), never on a frozen
  dataclass; **no second card class** is authored.
- ADR resolves all three flagged conflicts: (1) `study_kind` placement on the wrapper; (2)
  shape-bearing ideas still ride an AlphaSpec trunk (StudySpec only accepts `alpha_spec_id`); (3)
  graveyard writes require an AlphaSpec ID (`RejectedIdea.alpha_spec_id_or_hypothesis_id`).
- ADR records the full Track-A → canonical field map, the four fail-closed gaps (`source`,
  `cost_sensitivity`, `variant_budget`, `duplicate_exposure`), the mechanism-id lineage rule (kebab
  slug → `MechanismCard.source`; canonical `mech_<24-hex>` minted fresh), and the
  `data_dependency.class` migration partition. The 8 `research/differentiated_substrate_v1/cards/*.json`
  are marked **legacy / migrate-then-retire**.
- REUSE-MAP confirms each cited reuse symbol exists in current code (verify-before-build).
- `verify.py --smoke` + canaries PASS.

### IVL-P01 (YELLOW) — Intake validator + `alpha idea validate`
- `alpha idea validate <idea.yaml>` is registered in `cli/main.py:build_parser()` (mirroring the
  `cli/study.py` `register_subparser` pattern) and emits a canonical AlphaSpec + MechanismCard
  (+ SetupSpec only when `study_kind == context_not_equal_trigger`); the new `IdeaDraft` wrapper
  carries `study_kind` + validates it.
- Emission **reuses** `create/validate_mechanism_card`, `create/validate_setup_spec`,
  `validate_alpha_spec`, `generate_mechanism_id`; the three frozen governance dataclasses are
  byte-unchanged.
- All 8 Track-A cards migrate into canonical fields per the IVL-P00 map: `day_of_week_effect`
  (data_dependency `existing_substrate`) is the live `main_effect` exemplar; each migrated
  MechanismCard mints a fresh `mech_<24-hex>` id and carries the kebab slug as
  `source = "track_a:<slug>"` (lineage preserved so the STOPPED DK
  `study_spec.dataset_scope['mechanism_id']` linkage is not broken); multi-horizon cards apply the
  declared collapse rule (one MechanismCard per horizon, or pre-registered primary).
- Migration outputs land under a new canonical directory; `research/differentiated_substrate_v1/cards/**`
  is read-only reference and is **not edited or deleted** in this phase (retire is a later
  migrate-then-retire step gated on the parity test below).
- **Fails closed** when any of `source` / `cost_sensitivity` / `variant_budget` /
  `duplicate_exposure` cannot be populated (no fabricated value); the MechanismCard substantive-text
  gate (rationale + expected_mechanism) is satisfied or validation fails closed.
- A canonical-vs-card field-parity test asserts the migration map; `fomc` / `cpi`
  (`needs_paid_data`) migrate as **record-only** and are not tested.
- New tests under `tests/unit/cli/` + `tests/unit/governance/` pass; `verify.py --smoke` + canaries
  PASS.

### IVL-P02 (YELLOW) — Executable Testability Gate + `alpha idea testability`
- `alpha idea testability <idea.yaml>` returns **PASS / FAIL / DATA_GAP** as a PRE-TEST verdict
  (shot not spent) across the five fail-closed checks: (1) features materialized; (2) labels /
  path-labels exist; (3) path-label **≥2-distinct-class non-degeneracy**; (4) N_eff / MDE plausible
  and dedup known; (5) no-lookahead / `available_ts` satisfiable and the surrogate-FDR requirement
  known — all resolved **before** any real metric is computed.
- The gate orchestrator lives in the new package **outside** `research/`
  (`src/alpha_system/research_lane/`).
- The ≥2-distinct-class precondition is added to `conditional_probe.py` (which today has only
  empty-set guards at `:299-304`), reusing the label-runtime class-count logic
  (`_class_balance_summary` / `_distribution_summary`, emitting `class_count` /
  `majority_class_count` / `minority_class_count`); a single-class slice yields Check-3 `DATA_GAP`,
  not a probe.
- New tests under `tests/unit/research_lane/` + `tests/unit/research/` pass; `verify.py --smoke` +
  canaries PASS.

### IVL-P03 (YELLOW) — Fast exploratory lane bridge (`fast_probe`)
- One generic `fast_probe(card, setup, slice_spec)` in `src/alpha_system/research_lane/` loads a
  bounded **existing** slice via `load_parquet_values` + `FeatureLabelPackResolver`, maps the
  value-store schema to governance rows, and feeds `build_factor_diagnostics_run` |
  `evaluate_setup_conditional_probe` **in-memory**; `slice_spec` parameterizes root / pack-refs /
  instrument / session / label-version (de-hardcoding the ES_2024 paths from
  `dk_p04_track_b_probe.py` and the frozen `FIRST_LIGHT_*` constants from `first_light.py`).
- `promotion_eligible == False` throughout; **no** materialization, **no** scaleout-driver call,
  **no** registry write, **no** second value loader.
- Fails closed with an honest `DATA_GAP` (no fabricated values) when polars is absent or rows are
  unloadable (the `first_light.py` DATA_GAP branch pattern).
- The boundary test `tests/unit/research/test_research_no_value_engine.py` stays GREEN (bridge is in
  `research_lane/`, not `research/`); the loader-free probe engines are byte-unchanged.
- New tests under `tests/unit/research_lane/` pass; `verify.py --smoke` + canaries PASS.

### IVL-P04 (YELLOW) — Human-readable verdict `REPORT.md` renderer
- `REPORT.md` renders, for one idea: idea summary, `study_kind`, slice, data / features / labels
  used, dedup outcome, the 5 gate verdicts, the fast readout (including `class_count` /
  `minority_count` so a single-class slice is self-evident), N_eff / MDE, surrogate state, and the
  final verdict (`REJECT / DATA_GAP / INCONCLUSIVE / WATCH / CANDIDATE`) with a "why" and a "next
  action".
- The verdict reason cites `VerdictReasonCode` (validated via `validate_verdict_reason_code`).
- A golden-file test fixes the rendered output on a known readout; research-only language, no
  promotion / profitability / tradability claim.
- `verify.py --smoke` + canaries PASS.

### IVL-P05 (YELLOW) — Memory wiring + `alpha idea run` end-to-end
- `alpha idea run` wires verdict → memory: `REJECT` → `create_rejected_idea_record` (via the
  `alpha_spec_id`, asserted present, fail closed otherwise); `DATA_GAP` → requeue via
  `validate_requeued_verdict_record`; `WATCH` / `CANDIDATE` → `create_promotion_decision` (requires
  a `reviewer_verdict_id`, never auto-promoted).
- `FactorLibrary` stays survivor-only; `reject_exploratory_promotion_artifact` fails closed on any
  `EXPLORATORY`-stamped artifact reaching a trusted input; `promotion_eligible` stays `False`.
- New tests under `tests/unit/cli/` + `tests/unit/research_lane/` pass; `verify.py --smoke` +
  canaries PASS.

### IVL-P06 (YELLOW) — Dogfood DK Track B through the loop
- No new mechanism / feature / label / data; no geometry sweep; no promotion; no
  materialize / recompute of any FUTSUB or DK producer.
- `alpha idea gate` on the burned **single-class ES_2024 120m** slice → **Check-3 DATA_GAP**
  PRE-TEST (shot not spent) → requeue.
- `alpha idea gate` on the barrier-resolving **ES_2020_120m** slice (verified two-class; coverage
  matrix `acceptance_state: ACCEPTED`, `row_count` 313156, `overlap_rows` 310547 in
  `research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json`) → **Check-3 PASS**
  → `alpha idea run` emits a real probe readout + verdict + `REPORT.md`, and memory is written.
- `promotion_eligible == false` throughout; verdict in the allowed set; research-only language.
- **Must tolerate an honest `DATA_GAP`** if `ALPHA_DATA_ROOT` is unset in the executor (the
  ES_2020_120m Parquet is local-only, not in git) — the dogfood degrades to the `first_light`
  DATA_GAP branch with no fabricated values, and that path is an accepted outcome of the test.
- `tools/differentiated_killshot_v1/**` and `research/futures_substrate_scaleout_v1/**` are **not
  touched**; `git ls-files runs` empty; `verify.py --smoke` + canaries PASS.

## Campaign done

- IVL-P00–IVL-P06 merged with the per-phase gates above met.
- The loop runs end-to-end via the `alpha idea` front door: `validate` emits the canonical objects
  (+ `study_kind`), `testability` returns a PRE-TEST PASS/FAIL/DATA_GAP, `fast_probe` feeds the
  unchanged probe engines in-memory, `REPORT.md` renders a human-readable governed verdict, and
  `run` routes the verdict to memory (graveyard / requeue / reviewer-gated promotion).
- The DK Track B dogfood demonstrates the gate behavior: **DATA_GAP** on the degenerate single-class
  ES_2024 120m slice and **PASS** on the barrier-resolving ES_2020_120m slice, with `REPORT.md`
  emitted, memory written, and `promotion_eligible = false` throughout.
- The trust spine is untouched (frozen governance schemas byte-unchanged; `research/` imports no
  value engine; surrogate-FDR + no-lookahead + exploratory-never-promoted rails intact; FactorLibrary
  survivor-only; FUTSUB/DK STOPPED artifacts unmodified).
- All language is research-only — no alpha / profitability / tradability / production claim and no
  auto-promotion.
- `RUN_SUMMARY.md` (or equivalent campaign summary) is written; durable lessons are added to
  `project-skill` when applicable.
