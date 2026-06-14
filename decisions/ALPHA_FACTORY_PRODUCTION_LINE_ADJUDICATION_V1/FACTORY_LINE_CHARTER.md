# FACTORY_LINE_CHARTER

> **Status:** Research-only governance contract. No alpha, profitability, tradability, or production claims appear or are implied anywhere in this document. Diagnostics and gates decide outcomes; priors do not. This is an INTENT/contract document and lags live run status per AGENTS.md live-status authority — read `runs/<run_id>/state.json` or run `python tools/frontier/status_doctor.py` for the in-flight phase.
>
> **Scope:** The generic, repo-grounded production line for one research idea, end to end. ES/NQ/RTY existing data only; no new universe, no paid feeds.
>
> **Companion artifacts (referenced, NOT duplicated here):** `POST_DK_ADJUDICATION.md` (what the two fired kill-shots adjudicate and the next earned step), `IDEA_INTAKE_SCHEMA.md` (the unified intake-card schema and the Track-A/Track-B reconciliation), `TESTABILITY_GATE.md` (the pre-probe testability/two-class precondition design), `NEXT_SHOT_SELECTION_RULE.md` (how the next shot is chosen). Where this charter names a Stage-1 unification or a testability precondition, the binding detail lives in those documents.

---

## 0. REUSE-MAP LAW (binding on every stage below)

ENHANCE existing governance; never rebuild it. Every stage below cites the LIVE component. Where a stage is a GAP, the charter names the **smallest upgrade to an existing object** — never a new ledger, gate, canary, or card class. The three reason/taxonomy enums (`rejected_idea.py` `RejectedIdeaReasonCategory`, `governance/verdict_reason_code.py` `VerdictReasonCode`, `requeue.py` `REQUEUE_REASON`) must not gain a fourth; any new "why" maps onto an existing one.

---

## 1. The production line (stage by stage)

The canonical one-line pipeline is `docs/OPERATING_COMPASS_V4.md:925-938` §10 [v4.6]. Each stage entry gives: **(1) purpose, (2) LIVE component (file:line) or GAP + smallest upgrade, (3) entry/exit contract, (4) guard/canary covering it.**

---

### Stage 1 — Idea

**(1) Purpose.** Capture a human/strategy idea as the seed of a governed record. No values, no claims — intent only.

**(2) LIVE / GAP.** **GAP (no executable Stage-1 step).** `grep` for `intake`/`idea_intake` across `src/`, `docs/`, `campaigns/`, `research/` returns zero hits — no CLI subcommand, no intake registry, no intake ledger. Ideas exist only as loose JSON under `research/<campaign>/{cards,track_b}/` with no index. **Smallest upgrade:** do NOT build an intake registry; treat "idea" as the un-persisted precursor to a MechanismCard. The first *executable* artifact is the MechanismCard (Stage 2). Persistence of an accepted card's family belongs on the EXISTING `VariantLedger` (`src/alpha_system/governance/variant_ledger.py:284-410`), not a new intake ledger. See `IDEA_INTAKE_SCHEMA.md`.

**(3) Entry/exit contract.** Entry: free-form hypothesis text + ES/NQ/RTY scope. Exit: a draft that can populate the MechanismCard required fields (`src/alpha_system/governance/mechanism_card.py:31` `MECHANISM_CARD_REQUIRED_FIELDS`); fail to populate them ⇒ not yet an idea on this line.

**(4) Guard/canary.** None at this layer by design (no executable step). The first guard fires at Stage 2 validation.

---

### Stage 2 — MechanismCard / SetupSpec

**(1) Purpose.** Encode the idea as a fail-closed, content-addressed governance contract: a **MechanismCard** (any shape) and, for the context≠trigger shape, a **SetupSpec** that structurally enforces the differentiator.

**(2) LIVE / GAP.** **EXISTS.**
- `MechanismCard`: `src/alpha_system/governance/mechanism_card.py:94` (`@dataclass(frozen=True, slots=True)`), required fields enumerated at `mechanism_card.py:31`, `ALLOWED_MECHANISM_STAMPS = frozenset({EXPLORATORY_STAMP})` at `:30`, anti-vagueness `_VAGUE_TEXT`/`_VAGUE_PHRASES` set (`:85-94` confirms `"unbounded"`/`"unlimited"`/`"tbd"`/`"placeholder"` rejected), deterministic content-addressed id (`MECHANISM_CARD_REQUIRED_FIELDS` canonical-serialized at `:505`), `create_mechanism_card()` at `:151`.
- `SetupSpec`: `src/alpha_system/governance/setup_spec.py:96` (15 required fields incl. `entry_context`/`event_trigger`/`path_label`/`mechanism_id`/`stamp`). The context≠trigger guard `_validate_event_trigger_is_separate()` at `setup_spec.py:299` is **verified load-bearing**: it rejects `event_trigger_aliases_entry_context` (same object), `event_trigger_matches_entry_context` (same canonical content), and `event_trigger_derived_from_entry_context` (declared derivation).

**GAP (intake bifurcation — primary line gap).** DK Track A's calendar/flow cards (`research/differentiated_substrate_v1/cards/*.json`, schema in `research/differentiated_substrate_v1/MECHANISM_CARD_TEMPLATE.md`) use a DOC-convention schema that `validate_mechanism_card()` **rejects** (verified `GovernanceValidationError` on `day_of_week_effect.json`). The well-powered-null path and the strategy-shaped path ran on incompatible card schemas. **Smallest upgrade (do NOT build a second card class):** add an optional `study_kind`/shape discriminator (`main_effect` vs `context_not_trigger`) to the EXISTING `MechanismCard` contract so Track-A-style cards validate against the same schema, and reconcile `MECHANISM_CARD_TEMPLATE.md` fields against `MECHANISM_CARD_REQUIRED_FIELDS`. The detailed schema reconciliation is owned by `IDEA_INTAKE_SCHEMA.md`.

**(3) Entry/exit contract.** Entry: idea draft. Exit: a `MechanismCard` (and `SetupSpec` if context≠trigger) that PASSES `validate_mechanism_card()` / `validate_setup_spec()` with a deterministic id; stamp is forced to `EXPLORATORY` (`ALLOWED_*_STAMPS` frozensets). Failure ⇒ `GovernanceValidationError`, idea does not advance.

**(4) Guard/canary.** Schema validators are themselves fail-closed guards. The EXPLORATORY-stamp lock is canaried downstream at the promotion boundary (`exploratory_promotion_refusal_canary`, `tools/hooks/canary_runner.py:163,378`).

---

### Stage 3 — REUSE / duplicate check

**(1) Purpose.** Refuse to re-test an idea/feature whose exposure already exists in the materialized registry; record reuse intent.

**(2) LIVE / GAP.** **PARTIAL.** `src/alpha_system/governance/duplicate_exposure.py:127` `check_duplicate_exposure(feature_request, registry_reader)` is the live, registry-backed, **fail-closed-when-registry-unavailable** guard — but it keys on a `FeatureRequest` (`duplicate_exposure.py:128`, reads SQLite via `connect_registry` at `:13`), NOT on a `MechanismCard`/`SetupSpec`. The card's required `duplicate_exposure` field is free-form metadata, never cross-checked at card validation. **Smallest upgrade (do NOT author a new dedup gate):** extend `check_duplicate_exposure` to accept a `MechanismCard.required_features`/`duplicate_exposure` surface so the REUSE check fires at the card layer, not only when a FeatureRequest is later spawned. Reconciliation owned by `IDEA_INTAKE_SCHEMA.md`.

**(3) Entry/exit contract.** Entry: validated card (and any spawned `FeatureRequest`). Exit: `ExposureFindingKind.DUPLICATE`/`EQUIVALENT` with `severity=BLOCKING` ⇒ idea routed to rejected memory (`DUPLICATE` reason); clean ⇒ advance. Registry unavailable ⇒ fail closed (`duplicate_exposure.py:135`).

**(4) Guard/canary.** The guard IS `duplicate_exposure.py`, wired into `src/alpha_system/features/request_gate.py` (`check_duplicate_exposure` invoked, blocking finding ⇒ `BLOCKED_DUPLICATE`). Doc: `docs/feature_label_foundation/FEATURE_REQUEST_GATE.md:18-31`.

---

### Stage 4 — Feature / Label / Path-label discovery + materialization

**(1) Purpose.** Declare and materialize the governed features/labels (including path-labels: MFE/MAE/`target_before_stop`/`triple_barrier`) the idea needs, parity-gated and no-lookahead.

**(2) LIVE / GAP.** **EXISTS.**
- Declaration: per-family scaleout configs carry a `governed_scope` allow-list — `configs/labels/scaleout/path.json:7-12` (`mfe`/`mae`/`target_before_stop`/`triple_barrier`); driver reads it at `src/alpha_system/features/scaleout/driver.py:572,575`.
- Materialization driver: `src/alpha_system/features/scaleout/driver.py:546-609`, parquet-only at research scale, serialized via `resource_guard.resource_class=materialization_registry`.
- Path-label reference oracle: `src/alpha_system/labels/families/path/family.py` (`compute_path_label`, `_first_barrier`, HORIZON→False mapping for `target_before_stop` at `:329-344`).
- Fast producer (parity-gated, values-only, no second truth): `src/alpha_system/labels/fast/path.py` (vectorized `no_touch` screen `:304-319`, same HORIZON→False mapping `:330-343`).
- Sink: `src/alpha_system/core/value_store.py:75-113` `write_parquet_values` / `load_parquet_values`.
- New inputs gated: `src/alpha_system/governance/feature_request.py:31-90` + `src/alpha_system/features/request_gate.py:34-120`.

**SUBSTRATE NOTE (the DK Track B root cause, verified).** Path barrier geometry is governed-fixed at `target_return=+0.02`/`stop_return=-0.02` (`configs/labels/scaleout/path.json:108-110`, explicitly "no parameter sweep or tuning" at `:106`). On a calm 120m ES slice a ±2% touch is rare ⇒ `_first_barrier` returns None ⇒ HORIZON fallback ⇒ `target_before_stop=False` for ~every row ⇒ single-class. This is a barrier-geometry-vs-horizon-vs-data-slice mismatch, not a conditioning bug. The fix is **slice/geometry SELECTION + a probe-side precondition (Stage 5), NOT modifying the parity-gated label math.**

**(3) Entry/exit contract.** Entry: validated card naming `required_features`/`required_labels` within an existing `governed_scope`. Exit: materialized parquet registered in `registry/{features,labels}.sqlite` with `producer_engine_id` + `value_schema_version`; dataset BLOCKED/missing-lock ⇒ fail closed.

**(4) Guard/canary.** No-second-PnL rail `tools/hooks/forbidden_pattern_guard.py` (`SECOND_TRUTH_DEF_RE`, sanctioned `backtest/**` carve-out), canaried both directions (`canary_runner.py:311-340`). FeatureRequest dedup at `request_gate.py`. Reference-parity gate on the fast producer (parity tolerance noted in `labels/fast/path.py`).

---

### Stage 5 — Testability gate (pre-probe precondition)

**(1) Purpose.** Refuse to run a probe/diagnostic on a degenerate slice — specifically a single-class path-label outcome where a "valid"-looking probability is statistically meaningless.

**(2) LIVE / GAP.** **GAP on the probe code path (the load-bearing gap of the last shot).** A class-balance / single-class FAIL gate EXISTS in the LABEL diagnostics path: `src/alpha_system/runtime/diagnostics/label/runtime.py:893-900` (and the gate consumed at `:945-949`) FAILs when `majority_class_share > config.max_majority_class_share`, backed by `_class_balance_summary`. But the DK Track B conditional probe **bypasses** it: `src/alpha_system/research/conditional_probe.py:299-304` guards ONLY empty aligned/conditioned sets — verified there is **no `>=2`-distinct-class precondition** before `target_before_stop_probability` (`src/alpha_system/research/events.py:77-94`) computes a bare True-share with no class-count. The degeneracy was caught only by a hand-written `EVIDENCE.json` caveat (`single_class_path_outcome:true`), not by an automatic gate. **Smallest upgrade (do NOT build a new class-balance gate):** (a) route the probe through the EXISTING label-diagnostics class-balance gate or extract a small shared single-class precondition; (b) add a `>=2`-distinct-class check to `conditional_probe.py:299-304`'s existing empty-set guard; (c) have `events.target_before_stop_probability` emit `class_count`/`minority_share` alongside the probability so single-class is self-evident. Detailed design owned by `TESTABILITY_GATE.md`.

**(3) Entry/exit contract.** Entry: aligned/conditioned observation set with materialized path outcomes. Exit: PASS only if conditioned path-outcomes contain ≥2 distinct classes AND `majority_class_share ≤ max_majority_class_share`; single-class ⇒ FAIL (not a null, a closable DATA_GAP — route to `requeue.py`, not rejected memory). `promotion_eligible:false` preserved throughout.

**(4) Guard/canary.** Today: post-hoc human caveat only (the gap). Target: the existing label-runtime FAIL gate becomes preflight on the probe path. A regression covering "single-class slice FAILs before diagnostics run" should live where the label-runtime tests already do.

---

### Stage 6 — EXPLORATORY vs TRUSTED lane split

**(1) Purpose.** Route the study into one of two lanes with structurally different promotion semantics (see §2 Lane Policy).

**(2) LIVE / GAP.** **EXISTS.**
- EXPLORATORY lane reference flow: `src/alpha_system/research/first_light.py` wires `create_mechanism_card()` → `create_setup_spec()` → `compile_setup_spec_to_conditional_probe()` → `evaluate_setup_conditional_probe()`, emitting `promotion_eligible:false` readouts (`:222,:284`). `src/alpha_system/research/conditional_probe.py` requires the EXPLORATORY stamp or raises (`:177-179`) and hardwires `promotion_eligible=False` (`:147,:398`).
- TRUSTED lane: `src/alpha_system/research/track_a_scorer.py` (value-bearing factor-diagnostics scorer; deliberately imports none of backtest/management/fast_path/core.value_store — the no-second-PnL rail), NOT EXPLORATORY-stamped.
- Bridge: `src/alpha_system/governance/trusted_handoff.py` (`create_trusted_handoff_gap_report`) enumerates the AlphaSpec/StudySpec/FeatureRequest/LabelSpec gaps an EXPLORATORY probe must fill before a trusted rerun; sets `promotion_evidence=False`, `trusted_rerun_required=True` (`:98,:162`).

**(3) Entry/exit contract.** Entry: validated card/spec that passed the testability gate. Exit (EXPLORATORY): a `promotion_eligible:false` readout. Exit (TRUSTED): a value-bearing diagnostics run feeding the verdict path. EXPLORATORY→TRUSTED is a *manual, gap-report-mediated* rerun (no auto-generation of trusted specs — by design).

**(4) Guard/canary.** `exploratory_promotion_refusal_canary` (`canary_runner.py:163,378`) backed by `reject_exploratory_promotion_artifact` (`promotion.py:386`, verified fail-closed: raises `EXPLORATORY_PROMOTION_REFUSAL_CODE` on any nested EXPLORATORY stamp).

---

### Stage 7 — Diagnostics / probe

**(1) Purpose.** Measure sanctioned IC / path-outcome diagnostics under no-lookahead and overlap-aware power, with an asymmetric gate that can never self-promote.

**(2) LIVE / GAP.** **EXISTS.**
- TRUSTED diagnostics: `src/alpha_system/runtime/diagnostics/factor/runtime.py:240-265` (`build_factor_diagnostics_run`), no-lookahead `available_ts` hard-gated as a REJECT (`_evaluate` REJECTs `factor_available_ts_missing`/`factor_label_available_ts_missing` at `:451-464`). IC delegated to value-free `research.ic`.
- Power: `src/alpha_system/runtime/diagnostics/splits/n_eff.py:262-303` `estimate_n_eff` (purge/embargo removed first, then horizon-overlap discount, bounded by rows; `statistical_validity_claim:False` baked in).
- Asymmetric keystone (verified adversarially): `src/alpha_system/research/track_a_scorer.py:164-212` `map_runtime_state_to_primary_state` branches ONLY on `n_eff <= 1 or mde_abs_ic is None` (`:199`); `pearson_ic`/`rank_ic`/`bucket_is_monotonic` are accepted but UNUSED in the branch — a DIAGNOSTICS_COMPLETE read is **never** auto-promoted to WATCH/CANDIDATE (docstring + code at `:184-189,:207-212`). Pooled wiring `score_mechanism` at `:215-322`.
- EXPLORATORY probe path-outcome diagnostics: `src/alpha_system/research/events.py:77-112`.

**GAP-watch (regression debt, not a build).** Because the IC params are accepted-but-unused, a future editor could wire effect size into the branch and silently break the asymmetric gate. **Smallest upgrade:** add a regression test pinning "effect size never promotes." Do not edit branch logic.

**(3) Entry/exit contract.** Entry: lane-routed study with materialized features/labels. Exit: a `StudyRunResultState` → `(primary_state, reason_code)` where `primary_state ∈ {REJECT, INCONCLUSIVE}` only at this stage; WATCH/CANDIDATE_RESEARCH are reviewer-gated, never minted here.

**(4) Guard/canary.** `random_target`/`future_shift`/`permuted_labels`/`optimistic_fill` negative controls (`canary_runner.py:373-376` → `governance/canaries/harness.py`); `planted_fake_alpha` (gun does NOT fire on garbage, `canary_runner.py:92,379`) PAIRED with `true_alpha_detection` strong/weak (gun DOES fire on real alpha, `canary_runner.py:380-381`) — a verified detect/no-detect mutation twin.

---

### Stage 8 — VariantLedger / TrialLedger / surrogate-FDR / power

**(1) Purpose.** Bound multiple-comparisons exposure (per-study and platform-cumulative family budgets), calibrate a per-factor surrogate-FDR floor (label-shuffle), and require FDR-before-metric.

**(2) LIVE / GAP.** **EXISTS** (one PARTIAL).
- `TrialLedger`: `src/alpha_system/governance/trial_ledger.py` (`TrialLedgerRecord:111`, `summarize_trial_ledger_variants:480` — the bridge VariantLedger consumes; one-way derivation, no duplicate accounting).
- `VariantLedger` (first-class, RIGOR-P02): `src/alpha_system/governance/variant_ledger.py` — JSONL append-only fail-closed (`:284-410`), `BudgetAmendmentRecord` with `new_budget > prior` enforced (`:560`) and `amendment.created_at < earliest attempt` (`_find_covering_amendment:1259`), `evaluate_family_budget:645`, `validate_variant_and_family_budget:684` wired into `promotion_gate.py:58` (verified import) at the EVIDENCE_READY transition.
- Surrogate-FDR: `src/alpha_system/governance/surrogate_run.py:889` `calibrate_surrogate_fdr` (workers>1 byte-identical via deterministic per-spec seed); `surrogate_calibration_report_from_rows:989` verified → `LEAKAGE_BLOCKED` if `statistic_pass_count>0`, `CALIBRATION_BLOCKED` if `error_count>0`, else `ZERO_PASS_MET` (`:1006-1011`). Per-factor isolation enforced by `require_isolated_namespace` + per-spec seeding — no cross-factor reuse (six separate real per-family calibrations recorded under `research/discovery_rigor_floor_v1/surrogate_fdr/`).
- **PARTIAL — FDR-before-metric.** Not a runtime interlock; a pre-registration contract: `detection_statistic.evaluate_detection_statistic` takes `threshold_abs_pearson_ic` as a *supplied* required input (locked `TRUE_ALPHA_DETECTION_THRESHOLD_ABS_PEARSON_IC=0.95`, a surrogate-leakage detector, NOT a discovery bar), plus `registered_before_metrics`/`budget_amendment_authored` flags + `KILL_SHOT_READINESS.md` rows. **Smallest upgrade (optional, only if a hard interlock is chartered):** a thin guard that fails closed when a metric artifact predates its locked FDR/threshold artifact (content-hash/timestamp ordering), reusing existing `study_spec` content-hash + `variant_ledger` `registered_before_metrics` — NOT a new ledger.

**(3) Entry/exit contract.** Entry: a study with a writable family-scoped VariantLedger path (`resolve_variant_ledger_path` rejects None/vague — provisioning is an integration responsibility, fail-closed by design). Exit: family budget within bounds (or pre-dated amendment), surrogate `ZERO_PASS_MET`, power statement with overlap-aware `n_eff`. Any surrogate pass ⇒ `LEAKAGE_BLOCKED`; any error ⇒ `CALIBRATION_BLOCKED`.

**(4) Guard/canary.** `validate_variant_and_family_budget` (fail-closed, wired into `promotion_gate.py`) + RIGOR-P02 bypass canaries (`tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py`). Surrogate gate is itself fail-closed.

---

### Stage 9 — Verdict

**(1) Purpose.** Emit a closed-taxonomy verdict (REJECT / INCONCLUSIVE / WATCH / CANDIDATE_RESEARCH) with a typed reason code; WATCH/CANDIDATE are reviewer-gated.

**(2) LIVE / GAP.** **EXISTS.** `src/alpha_system/governance/promotion.py`: `PromotionDecisionOutcome = REJECTED|WATCH|INCONCLUSIVE` (`:129-134`), `reason_code: VerdictReasonCode` required for INCONCLUSIVE, fail-closed (`:331,:262-265`). Closed enum `governance/verdict_reason_code.py:11-21` (`UNDERPOWERED|SUBSTRATE_GAP|COST_FRAGILE|DATA_QUALITY|LEAKAGE_BLOCKED|DUPLICATE_EXPOSURE|REGIME_UNSTABLE|BBO_PROXY_LIMITATION`; free text rejected). `implies_live_approval`/`implies_capital_allocation`/`implies_production_readiness` all defined (and False). The kill-shot **readiness gate** is a composition, not one object: `promotion_gate.py` EVIDENCE_READY state machine (`DIAGNOSTICS_ALLOWED→DIAGNOSTICS_RUN→EVIDENCE_READY→REVIEWED→{CANDIDATE/REJECTED}`, verified `:74-77`) + the 13-row fail-closed checklist `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` + integration audit `tests/unit/discovery_rigor_floor/test_rigor_p07_integration_audit.py`.

**(3) Entry/exit contract.** Entry: completed diagnostics + Stage-8 gates passed. Exit: a verdict with `primary_state` + `VerdictReasonCode`; CANDIDATE_RESEARCH/WATCH only via a validated `PromotionDecision` at the REVIEWED transition (`promotion_gate.py:541-586`). INCONCLUSIVE without a reason code ⇒ fail closed.

**(4) Guard/canary.** `promotion_gate` transition validation; `reject_exploratory_promotion_artifacts` runs BEFORE any lifecycle hop (`promotion_gate.py:175`). Reason-code closedness is enforced by the enum.

---

### Stage 10 — Rejected memory OR survivor memory

**(1) Purpose.** Persist the outcome: rejected ideas into the non-destructive research graveyard; survivors (only on a reviewer-approved CANDIDATE) into survivor memory — which does not exist yet because the survivor gate = 0.

**(2) LIVE / GAP.** **EXISTS (rejected) / correctly ABSENT (survivor).**
- Rejected memory: `src/alpha_system/governance/rejected_idea.py` — `RejectedIdeaReasonCategory` closed 7-value enum (`:97`), `RejectedIdeaRecord:142`, `ResearchGraveyardLedger` append-only with `lookup_by_id`/`lookup_by_referenced_idea`/`append_reconsideration` (`:238-398`); reconsideration is a linked record, never a deletion (`REJECTION_IS_PERMANENT_BAN`).
- Evidence-accrual requeue (closable-gap revival): `src/alpha_system/governance/requeue.py` — `scan_requeue_candidates` over UNDERPOWERED verdicts (`:406`), `RequeuedVerdictRecord:91`. Use this for the DK Track B substrate gap and roll_week DATA_GAP — NOT a new revival ledger.
- Survivor memory / FactorLibrary: **correctly ABSENT.** No `src/` module; only docs + the librarian guard `src/alpha_system/agent_factory/roles/librarian.py:107` (forbids direct survivor-memory writes). Survivor gate = 0 (two clean kill-shots, 0 survivors) ⇒ nothing earns it. See §3.

**(3) Entry/exit contract.** Entry: a verdict. Exit (REJECT) → `ResearchGraveyardLedger` record with a `RejectedIdeaReasonCategory`. Exit (INCONCLUSIVE+UNDERPOWERED / DATA_GAP) → requeue candidate via `requeue.py`. Exit (CANDIDATE_RESEARCH/WATCH) → **blocked at survivor memory because the gate is 0** (this is the live state, not a defect).

**(4) Guard/canary.** Librarian guard (`librarian.py:102/:106/:107` forbids promotion/self-approval/direct survivor-memory write); EXPLORATORY promotion refusal (`promotion.py:386`). The three reason enums must not gain a fourth.

---

## 2. Lane policy

Two lanes with structurally different promotion semantics. **Neither lane changes the research-only constraint.**

**EXPLORATORY lane** (the context≠trigger / SSRL expression lane):
- Every artifact is `EXPLORATORY`-stamped (`mechanism_card.py:29` `EXPLORATORY_STAMP`; `ALLOWED_*_STAMPS` frozensets lock it).
- `promotion_eligible:false` is hardwired at every readout (`conditional_probe.py:147,:398`; `first_light.py:222,:284`).
- It is **structurally refused as promotion evidence**: `reject_exploratory_promotion_artifact` (`promotion.py:386`, verified — recurses the artifact tree, raises `EXPLORATORY_PROMOTION_REFUSAL_CODE='exploratory_artifact_refused'`), wired into `validate_governance_transition` BEFORE any lifecycle hop (`promotion_gate.py:175`), and covered by `exploratory_promotion_refusal_canary` (`canary_runner.py:163,378`) and `tests/unit/governance/test_exploratory_refusal.py`.
- Output set: an exploratory readout that can only feed a TRUSTED rerun via the `trusted_handoff.py` gap report — never directly into verdict/memory.

**TRUSTED lane** (the value-bearing diagnostics + verdict path):
- Reached via `track_a_scorer.py` (NOT EXPLORATORY-stamped) and the value-free `trusted_handoff.py` gap report; requires authoring AlphaSpec/StudySpec/FeatureRequest/LabelSpec (no auto-generation by design).
- Subject to the full Stage-7/8/9 chain: sanctioned IC + no-lookahead (`runtime.py:451-464`), overlap-aware power (`n_eff.py`), per-factor surrogate-FDR `ZERO_PASS_MET` (`surrogate_run.py:889`), and the asymmetric verdict that **never self-promotes** (`track_a_scorer.py:184-189`).
- Only the TRUSTED lane can reach REVIEWED→CANDIDATE_RESEARCH, and only via a reviewer-validated `PromotionDecision`.

**Lane-crossing rule.** EXPLORATORY → TRUSTED is gap-report-mediated and manual. There is no path by which an EXPLORATORY artifact becomes promotion evidence; the refusal is fail-closed and canaried.

---

## 3. Downstream modules are survivor-gated (FORBIDDEN to build now)

**Current survivor gate = 0.** Two kill-shots have fired with 0 survivors (FUTSUB; DIFFERENTIATED_KILLSHOT_V1). The Stage-D survivor ladder is `docs/OPERATING_COMPASS_V4.md:417-466`; the layer-naming + anti-bloat LAW is §10 `:915-979` ("a name on this roadmap is permission to build it ONLY when its trigger fires, never by sequence/inertia," `:974-977`).

**Important adversarial caveat (verified):** the survivor-count ladder and the kill-shot readiness gate are **doc + human-judgement + REUSE-MAP discipline**, NOT executable counters. No module counts survivors and refuses to charter a downstream campaign; `experiments/survivors.py` + `experiments/candidate_policy.py:38` only gate a single *reviewed* candidate's management-grid eligibility. Enforcement of the table below therefore rests on review + compass-consistency + the absence of any built downstream module — not on a guard. Do not interpret "the gate is doc-only" as license to build; interpret it as a charter obligation.

| Module — FORBIDDEN now | Compass stage / pointer | Exact trigger that earns it |
|---|---|---|
| **Mining V2** (broad search) | Stage F, `docs/OPERATING_COMPASS_V4.md:493` | ≥1 reviewed survivor through the gate (Stage D ladder satisfied). |
| **FactorLibrary** (survivor memory ingestion) | Stage G, `:508-522`; explicitly "a MechanismCard/SetupSpec is NOT a FactorLibrary entry" `:964-967`; forbidden by `librarian.py:107` | ≥1 reviewed WATCH/CANDIDATE_RESEARCH survivor (the narrowed Stage-G trigger). |
| **AlphaBook** | Stage J, `:557` | Stage E-J unlock: ≥3 low-correlation survivors OR ≥1 validated pooled ensemble (`:464-465`). |
| **Strategy Sandbox / Strategy Reference** | Stage H, `:527` | ≥1 survivor → minimal CandidateRecord, Strategy Reference next (`:457-459`). |
| **PA grammar substrate** (expression catalog) | §10 `:962-968` (PA_GRAMMAR_SUBSTRATE ≠ FactorLibrary; grammar is expression, not evidence) | A survivor whose mechanism demands sequenced/conditional encoding; never built by inertia. |
| **Universe expansion** | Stage N, `:634` | Survivor-validated edge that motivates new symbols; ES/NQ/RTY only until then. |
| **Paid data feeds** (e.g. FOMC/CPI event calendars) | Stage N/inputs; deferred `needs_paid_data` | A survivor-validated edge whose mechanism requires the feed; behind FRED onboarding SOP + secret. **Hard-stop: requires explicit user authorization.** |

**No-build affirmation.** This charter authorizes building NONE of the above. Each remains a docs/handoff contract until its trigger fires. The existing `PromotionGate` (`promotion.py:386`) + librarian guard + `ResearchGraveyardLedger` cover every memory surface needed pre-survivor. The honest standing gap is that the survivor-count ladder / readiness gate / layer-naming law have **no executable guard** — if executability is ever chartered, the smallest upgrade is to extend `experiments/candidate_policy.py` and register the negative control as a scenario in `tools/hooks/canary_runner.py`, never a new gate object or a second canary runner.

---

## 4. What this charter does NOT decide (see companions)

- **The Stage-2/3 intake unification** (single card schema + shape discriminator + card-layer dedup): `IDEA_INTAKE_SCHEMA.md`.
- **The Stage-5 testability / two-class precondition design**: `TESTABILITY_GATE.md`.
- **The adjudication of the two fired kill-shots and the next earned step** (incl. the barrier-resolving ES_2020_120m re-run as a DATA_GAP close-and-rerun via `requeue.py`): `POST_DK_ADJUDICATION.md`.
- **Which shot fires next and on what rule**: `NEXT_SHOT_SELECTION_RULE.md`.

This charter is the generic line; those four are the specific decisions that flow through it. All five maintain research-only language and the REUSE-MAP law.
