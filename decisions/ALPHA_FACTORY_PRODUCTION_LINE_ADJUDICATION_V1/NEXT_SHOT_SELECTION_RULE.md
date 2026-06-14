# NEXT_SHOT_SELECTION_RULE

Research-only artifact. No alpha / profit / tradability / production claims. This document defines a **ranking rule** for selecting the next narrow research shot; it does not assert that any ranked mechanism has edge. Diagnostics and gates decide outcomes — never priors, never effect-size magnitude. This rule selects *what to test next and in what order*; the verdict is produced downstream by the existing governance gates.

Companion artifacts (authored separately; referenced by name, not duplicated here): `POST_DK_ADJUDICATION.md` (why we are post-DK and what the two clean kill-shots concluded), `FACTORY_LINE_CHARTER.md` (the end-to-end production line this rule feeds), `IDEA_INTAKE_SCHEMA.md` (the unified intake card schema a queued idea must satisfy), `TESTABILITY_GATE.md` (the executable preconditions a card must pass to *enter* this ranking at all).

---

## 1. Scope of the queue (binding)

The selection queue is **ES/NQ/RTY existing-data only**. No new universe, no paid feeds, no downstream factory modules may be chartered by this rule.

- Universe is fixed to the shared-beta equity-index futures set the compass already scopes: `docs/OPERATING_COMPASS.md` §1 (target calibration; "within ES/NQ/RTY — shared equity beta, shared vol regimes").
- External paid data is a hard-stop ask, not a queue option: `docs/OPERATING_COMPASS.md` §4.2 Stage I ("TBBO / MBP-1 SAMPLE MONTHS only; external paid data = hard-stop ask").
- **Survivor gate is currently 0** (live count from the registry / `status_doctor`, not a committed doc) — the survivor-gate rule is `docs/OPERATING_COMPASS.md` §3.5 + §4.2 Stage D. Two kill-shots (FUTSUB, DIFFERENTIATED_KILLSHOT_V1) have fired with zero survivors.
- Therefore **no Stage E–O downstream module** (Mining V2 = §4.2 Stage F, FactorLibrary = Stage G, AlphaBook = Stage J, Strategy Sandbox/Reference = Stage H, PA grammar expansion, universe expansion = Stage N, ML meta-labeling = Stage M, paid data = Stage I) is eligible for charter by this rule. Those are trigger-gated behind the survivor gate per the anti-bloat law (`docs/OPERATING_COMPASS.md` §3.6: "a name appearing on this roadmap is permission to build it ONLY when its trigger fires, never by sequence/inertia."). This rule **only** ranks narrow shots that run on the existing diagnostics + exploratory-probe lanes against already-materialized ES/NQ/RTY substrate.

A candidate that requires new substrate, a new universe, paid data, or a downstream module is **not ranked** — it is rejected at the `TESTABILITY_GATE.md` stage before it reaches this rule.

---

## 2. Queue position 0 (fixed, non-rankable): Track B gap-closure

**The DK Track B gap-closure is FIRST in the queue and is NOT a fresh shot — it is a gap closure of a previously-degenerate run.** It bypasses the ranking below because it has already been adjudicated as the earned next step (see `POST_DK_ADJUDICATION.md`).

Why it is a closure, not a new shot:

- DK Track B already authored a valid executable `setup_spec.json` / `mechanism_card.json` pair on the canonical governance schema (`research/differentiated_substrate_v1/track_b/setup_spec.json` → `setup_c49fe5e7...`, `entry_context.factor_id=liquidity_structure_range_contraction`, `event_trigger.factor_id=liquidity_structure_failed_high_breakout_flag`, `hold_time.horizon=120m`, `stamp=EXPLORATORY`; `research/differentiated_substrate_v1/track_b/mechanism_card.json` → `mech_651debd4...`, `variant_budget:1`, `duplicate_exposure.family_id=dk_p04_track_b_range_contraction_failed_high_breakout`). The context≠trigger separation is already structurally enforced (`src/alpha_system/governance/setup_spec.py:299` `_validate_event_trigger_is_separate`).
- The original probe ran on a **single-class** `target_before_stop` slice (degenerate: barrier did not resolve). The substrate cause is the fixed `+0.02 / -0.02` barrier geometry over a 120m horizon on calm tape, where `_first_barrier` returns no touch and the HORIZON fallback maps to `False` (`configs/labels/scaleout/path.json:108-110`; `src/alpha_system/labels/families/path/family.py:329-339`; `src/alpha_system/labels/fast/path.py:330-343`).
- The probe path computes `target_before_stop_probability` with **no ≥2-class precondition** (`src/alpha_system/research/events.py:84-94` returns a share with no class-count guard; `src/alpha_system/research/conditional_probe.py:298-304` guards only empty aligned/conditioned sets, not single-class), so a constant label produced a numerically "valid" 0.0 probability. The existing class-balance FAIL gate (`src/alpha_system/runtime/diagnostics/label/runtime.py:893-900`) is **not** on this code path.
- A **barrier-resolving alternative slice is already materialized and ACCEPTED**: `research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json:2857-2867` (`partition_id "ES_2020_120m"`, `variant "target_before_stop"`, `acceptance_state "ACCEPTED"`, `row_count 313156`, `n_eff_conservative 2609`, `lver_f9b126...`). Re-running the **same pre-registered** setup/card on this slice is a **DATA_GAP close-and-rerun**, exactly the pattern the requeue ledger exists for: `src/alpha_system/governance/requeue.py:406` `scan_requeue_candidates(...)` over UNDERPOWERED/gap verdicts, `REQUEUE_REASON = "UNDERPOWERED_EVIDENCE_ACCRUAL"` (`requeue.py:39`).

**Pre-execution obligation for position 0** (it does not change the ranking, but is a `TESTABILITY_GATE.md` precondition): the ES_2020_120m **class split must be re-measured from local parquet** (`src/alpha_system/core/value_store.py:116-133` `load_parquet_values`) and confirmed ≥2-class before the probe runs. The committed coverage record stores `row_count`/`n_eff_conservative` but **not** the TARGET/STOP/HORIZON class distribution (verified: `coverage_matrix.json:2857-2867` has no class-split field), so the memory figure (309206 False / 3950 True) is currently un-re-verifiable from this checkout. No new geometry sweep — `configs/labels/scaleout/path.json:106-107` ("no parameter sweep or tuning"); reuse the existing `lver_f9b126...`.

Position 0 carries no promotion implication: `conditional_probe` hardwires `promotion_eligible=False` (`src/alpha_system/research/conditional_probe.py:147,398`) and requires the surrogate ZERO_PASS_MET gate (`conditional_probe.py:343-359`, `:482-505`).

---

## 3. Ranking criteria (positions 1..N, fresh shots after the gap closes)

After position 0, fresh shots are ranked by the four criteria below in lexicographic priority (A first; ties broken by B, then C, then D, then §4 tie-breaks). A criterion is a **filter** (A) or a **score** (B–D).

### Criterion A — TESTABILITY on EXISTING data (HARD FILTER, no rank)
A candidate is in the queue **only if** it passes `TESTABILITY_GATE.md` against already-materialized ES/NQ/RTY substrate with **no new substrate**:
- Required features/labels resolve to existing materialized versions (governed scope: `configs/features/scaleout/*.json` `governed_scope`, `configs/labels/scaleout/path.json:7-12`; driver reads at `src/alpha_system/features/scaleout/driver.py:572,575`).
- Path-label outcomes used by the candidate **resolve ≥2 classes** on the chosen slice (the precondition whose absence caused the Track B degeneracy — `events.py:84-94`, `conditional_probe.py:298-304`). MFE/MAE-conditioned shots are continuous and never single-class (`src/alpha_system/labels/path_metrics.py:31-61`), so they pass A trivially; barrier-outcome shots must name a resolving slice.
- No-lookahead `available_ts` is satisfiable (hard REJECT otherwise: `src/alpha_system/runtime/diagnostics/factor/runtime.py:451-464`).
Candidates failing A are **not ranked**; if previously tested-and-rejected, they go to the graveyard, not the queue (Criterion B).

### Criterion B — UNEXHAUSTED mechanism shape (HARD FILTER against the graveyard)
A candidate must test a **shape not already concluded as a clean null**. Check the rejected memory before queueing:
- `src/alpha_system/governance/rejected_idea.py` `ResearchGraveyardLedger` with `lookup_by_referenced_idea` (`:323`) and a closed reason taxonomy `RejectedIdeaReasonCategory` (`:97`: DUPLICATE/LEAKAGE/WEAK_EVIDENCE/FAILED_DIAGNOSTICS/OUT_OF_SCOPE/...).
- Rejection is non-destructive and **not** a permanent ban (`rejected_idea.py:78` `REJECTION_IS_PERMANENT_BAN = False`; reconsideration via `append_reconsideration` `:336`), but re-running an **identical** shape on the **same** slice that already produced a well-powered clean REJECT is **exhausted** and excluded. Example exhausted shapes: DK Track A calendar/flow **main-effect** factors (day_of_week / opex / month_end / open_close_auction_flow) — the four scored mechanisms, each a well-powered clean null, 4× REJECT (`quarter_end` was a declared flag but was not scored as a separate mechanism). A *new shape* over the same factors (e.g., a context≠trigger conditional, not a main effect) is **not** exhausted.
- A DATA_GAP / UNDERPOWERED verdict is **not** exhausted — it is requeue-eligible (`requeue.py:406`, `:39`). roll_week (honest DATA_GAP, `in_roll_window_flag` all-null) and the Track B substrate gap are requeue candidates, not graveyard entries.

### Criterion C — INFORMATION-PER-COMPUTE (primary SCORE)
Rank surviving candidates by **achievable N_eff relative to the MDE the shape needs to resolve**, using the existing conservative power machinery — never by expected effect size (effect size never promotes: `src/alpha_system/research/track_a_scorer.py:184-189`).
- N_eff is the overlap-aware, purge/embargo-discounted, row-bounded estimate: `src/alpha_system/runtime/diagnostics/splits/n_eff.py:262-303` (`estimate_n_eff`; purge/embargo removed first, then horizon discount, capped at rows; `statistical_validity_claim:False`).
- MDE is `minimum_detectable_abs_ic(N_eff)` / `build_ic_power_statement` (`conditional_probe.py:366-372`; `track_a_scorer.py:283-291`).
- **Score = the margin by which achievable N_eff drives MDE below the smallest effect the shape must distinguish from zero** — i.e., prefer shots that are *well-powered per unit compute*, not shots with large priors. A shot landing at `n_eff <= 1` or undefined MDE is **underpowered** and cannot be auto-promoted (`track_a_scorer.py:199`), so it ranks last regardless of prior.
- Compute cost weight: path/MFE/MAE labels reuse already-materialized parquet (no re-materialization); shots that would require new materialization are penalized (cost-aware) and usually fail A anyway. Reuse the existing `lver`/`fver` rather than recompute (`configs/labels/scaleout/path.json:106-107` no-sweep; coverage matrices record `n_eff_conservative` per partition, e.g. `coverage_matrix.json:2862`).

### Criterion D — CLOSES a known substrate/expression-lane gap (SCORE)
Prefer candidates that retire a *named, closable* gap over candidates that open new uncharted surface:
- The class-balance/single-class probe-precondition gap (the Track B substrate cause) — `events.py:84-94`, `conditional_probe.py:298-304`, with the existing label-diagnostics gate to route through (`runtime/diagnostics/label/runtime.py:893-900`).
- The barrier-outcome class-distribution gap in coverage matrices (slice selection is currently blind to barrier resolvability — `coverage_matrix.json` records `row_count`/`n_eff_conservative` but no TARGET/STOP/HORIZON shares).
- The SSRL **expression-lane** gap: the context≠trigger lane has a worked example (`src/alpha_system/research/first_light.py`, `research/strategy_shaped_lane_v0/first_light/`) and a de-stacked single-factor read (below) but few distinct shapes exercised end-to-end.

---

## 4. Tie-break order (when A passes and B/C/D tie)

1. **Lower compute, same information** — fewer materialized partitions touched / reuses an existing `lver`/`fver` (cost-aware; `configs/labels/scaleout/path.json:106-107`).
2. **Higher slice robustness** — the resolving ≥2-class outcome holds across more than one ES/NQ/RTY year-slice (less single-slice fragility).
3. **Closes the gap with the existing gate, not new code** — a shot retired by *routing through* `runtime/diagnostics/label/runtime.py:893-900` or `requeue.py` outranks one needing net-new machinery (REUSE-MAP discipline).
4. **Exploratory-lane hygiene already satisfied** — surrogate ZERO_PASS_MET reusable per-factor namespace ready (`src/alpha_system/governance/surrogate_run.py:889`, `:1006-1011`, `require_isolated_namespace` `:1195`); per-factor, never cross-factor reuse.
5. **Earliest pre-registration provenance** — a card with FDR/budget amendment authored before the metric (`registered_before_metrics`) outranks an un-pre-registered one (`docs/OPERATING_COMPASS.md` §6, governance / pre-registration).

---

## 5. Worked example ranking (mechanisms the repo already knows)

Slate of three known mechanisms plus the fixed position-0 closure. **No edge is asserted** for any of these; this only orders *test priority*.

| Rank | Candidate | A: testable on existing data? | B: unexhausted shape? | C: info/compute (N_eff vs MDE) | D: closes a gap? |
|------|-----------|-------------------------------|------------------------|-------------------------------|------------------|
| **0 (fixed)** | **DK Track B re-run** — same `setup_c49fe5e7...` / `mech_651debd4...` on **ES_2020_120m** (`coverage_matrix.json:2857-2867`) | YES — slice ACCEPTED, materialized; must re-measure ≥2-class from parquet (`value_store.py:116-133`) | N/A — **gap closure, not fresh** (prior run = degenerate single-class, requeue-eligible `requeue.py:39,406`) | n_eff_conservative 2609 on 313156 rows (`coverage_matrix.json:2862,2865`); MDE via `conditional_probe.py:366-372` | YES — closes Track B substrate gap + the probe single-class precondition gap |
| **1** | **Path-outcome conditioning, new context≠trigger shape over the resolving slice** (reuses `compile_setup_spec_to_conditional_probe`, `conditional_probe.py:171-200`; MFE/MAE-conditioned to avoid single-class, `path_metrics.py:31-61`) | YES — reuses materialized path labels + existing factor families | YES — distinct shape from DK Track A main-effects and from the Track B baseline variant | Continuous MFE/MAE never single-class → N_eff bounded by materialized rows; MDE well-defined | YES — exercises the expression lane + retires the single-class hazard by construction |
| **2** | **SSRL expression-lane shot** — first_light card→setup→conditional probe (`research/strategy_shaped_lane_v0/first_light/{setup_spec,mechanism_card}.json`; `first_light.py`) | YES — library flow over existing substrate | YES if the authored shape ≠ any graveyard entry (`rejected_idea.py:323` lookup) | depends on conditioned N_eff; rank by `estimate_n_eff` (`n_eff.py:262`) of the authored slice | PARTIAL — exercises the expression lane; does not retire a substrate gap |
| **3** | **De-stacked vwap `factor_session_minute` isolated read** (`research/strategy_shaped_lane_v0/de_stack/EVIDENCE.json`: `ic 0.068`, `observation_count 6862`, `n_eff 6862`, `mde_abs_ic 0.0237`, `stamp EXPLORATORY`, `promotion_eligible:false`, `gate_status PASSED zero-pass-met`) | YES — already materialized FUTCORE factor | **WEAK** — already RECORDED as an EXPLORATORY restatement, **not fresh corroboration** (`research/differentiated_substrate_v1/CAMPAIGN_VERDICT.md:185-186`: "carried SHIP_REFIT restatement, not fresh corroboration") | N_eff 6862, MDE 0.0237 — usable power, but the *isolated read is already on record* | NO new gap closed; re-reading the same isolated IC is near-exhausted |

**Resulting order: 0 → 1 → 2 → 3.**
- Position 0 is fixed (gap closure).
- Position 1 wins criterion D over 2 (retires the single-class hazard structurally) and ties-breaks above 3 on B (de-stack is a near-exhausted restatement per `CAMPAIGN_VERDICT.md:185-186`).
- Position 3 ranks last: it passes A and has usable power (C), but its shape is the **weakest on B** — it would re-record an already-RECORDED isolated read with no new gap closed (D = NO), so it is the lowest-information-per-compute fresh shot. It is *not* graveyarded (it was never a clean REJECT; it is an EXPLORATORY restatement), so it remains queue-eligible but low.

---

## 6. Invariants this rule must never violate

- **No promotion from ranking.** Selecting a shot grants it no evidentiary status. All ranked shots run on the EXPLORATORY probe lane (`conditional_probe.py:147,398` `promotion_eligible=False`) or the TRUSTED diagnostics scorer (`track_a_scorer.py`), and a complete read is **never** auto-promoted to WATCH/CANDIDATE (`track_a_scorer.py:184-189,207-212`); survivor is reviewer-gated.
- **Effect size never breaks ties.** Criterion C scores *power per compute* (achievable N_eff vs MDE), never expected IC magnitude. `pearson_ic`/`rank_ic` are inputs the scorer deliberately leaves unused in its branch logic (`track_a_scorer.py:199-212`).
- **REUSE, never rebuild.** Ranking, gap-closure, and requeue use existing objects only — `requeue.py` (not a new revival ledger), `rejected_idea.py` graveyard (not a new rejection enum), `surrogate_run.py` per-factor isolated namespace (not a shared calibration cache), the label-diagnostics class-balance gate (`runtime/diagnostics/label/runtime.py:893-900`, not a new gate).
- **Stays inside the survivor gate.** While the gate = 0 (`docs/OPERATING_COMPASS.md` §3.5 / §4.2 Stage D; live count from `status_doctor`), this rule may only enqueue narrow ES/NQ/RTY shots on existing substrate. It may **never** charter a Stage E–O downstream module; that is `FACTORY_LINE_CHARTER.md` territory and is trigger-gated (`docs/OPERATING_COMPASS.md` §3.6).
