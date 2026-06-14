# IDEA_INTAKE_SCHEMA

Status: VALUE-FREE intake contract. RESEARCH-ONLY. An intake card is a pre-registration of a research hypothesis to be *tested*; it is never a claim that an edge exists. No card may contain IC/return/Sharpe values or any alpha/tradability/profitability/production claim. Diagnostics and gates decide admission and verdict, not the card's priors.

This document defines the **minimal fields an idea must declare to enter the production line**, presented as the checklist a `MechanismCard` (plus its companion `SetupSpec` when the idea is shape-bearing) must pass to be *admitted*. It is grounded in the only card pair on the executable lane today — DK Track B (`research/differentiated_substrate_v1/track_b/mechanism_card.json`, `research/differentiated_substrate_v1/track_b/setup_spec.json`) — both of which were re-verified to validate against the live governance contract during authoring.

Scope boundary (do not duplicate the sibling artifacts):
- **Admission verdict logic** (REJECT/INCONCLUSIVE/WATCH/CANDIDATE_RESEARCH) lives in `TESTABILITY_GATE.md` and the diagnostics stage; this doc only governs *entry*.
- **How an admitted idea flows downstream** (REUSE → discovery → lane → diagnostics → ledger → verdict → memory) lives in `FACTORY_LINE_CHARTER.md`.
- **Which idea to fire next** lives in `NEXT_SHOT_SELECTION_RULE.md`.
- **The post-DK adjudication of why this matters now** (intake bifurcation as the primary gap) lives in `POST_DK_ADJUDICATION.md`.

---

## 1. The two card shapes (and which validator each must pass)

There is exactly one **executable, fail-closed** intake contract, and it has two shapes. The central post-DK gap is that a *parallel doc-convention schema* exists and the two are non-interoperable.

| Shape | Required artifact(s) | Validator (must raise on failure) | Repo grounding |
|---|---|---|---|
| **Main-effect / context-as-factor** (e.g. calendar/flow conditioning, DK Track A) | `MechanismCard` | `validate_mechanism_card()` | `src/alpha_system/governance/mechanism_card.py:198` |
| **context ≠ trigger** (shape-bearing setup, DK Track B / SSRL) | `MechanismCard` **and** `SetupSpec` | `validate_mechanism_card()` + `validate_setup_spec()` | `mechanism_card.py:198`, `src/alpha_system/governance/setup_spec.py:208` |

**Admission rule:** an idea is admitted only when its card artifact(s) PASS the executable validator(s) above. The `MechanismCard` schema is the **single canonical intake schema** (`MECHANISM_CARD_REQUIRED_FIELDS`, `mechanism_card.py:31-45`); 13 required fields, exhaustively allow-listed (`allowed_fields=MECHANISM_CARD_REQUIRED_FIELDS`, `mechanism_card.py:205`), so an *extra* field is also a rejection.

**Verified bifurcation (the gap this schema closes).** DK Track B's pair validates today: `validate_mechanism_card(track_b/mechanism_card.json)` → `mech_651debd4497b065e1e121c3d`; `validate_setup_spec(track_b/setup_spec.json)` → `setup_c49fe5e7f8c17305db51a9bd`. By contrast, the DK Track A calendar cards (`research/differentiated_substrate_v1/cards/*.json`, documented by `research/differentiated_substrate_v1/MECHANISM_CARD_TEMPLATE.md`) use a *different* field set (`hypothesis{statement,economic_rationale}`, `conditioning_variable`, `expected_orthogonality_to_dead_mechanisms`, …). Running `validate_mechanism_card(cards/day_of_week_effect.json)` was confirmed to RAISE `GovernanceValidationError` with `missing_required_field` on `source`, `rationale`, `expected_mechanism`, `expected_direction`, `horizon`, `session`. **The well-powered-null Track A path never touched the executable intake contract.** This schema requires that every future idea — main-effect or shape-bearing — enter through `validate_mechanism_card()`, so the calendar-card content (hypothesis statement, economic rationale, conditioning variable, orthogonality reasoning) must be carried *inside* the canonical fields below, not in a parallel doc schema.

> REUSE-MAP note: do **not** author a second card class. The smallest sanctioned upgrade to unify the two shapes (an optional `study_kind`/shape discriminator on the existing `MechanismCard`) is a code change owned by `FACTORY_LINE_CHARTER.md`, not by this intake doc. Until then, the admission rule is literal: the card must pass `validate_mechanism_card()`.

---

## 2. The MechanismCard admission checklist

A card is admitted only if **every** box below is satisfied. Each row names the field, the user-facing intent (the question the field answers), the live constraint enforced by the validator, and whether the check is **machine-checkable** (the validator raises) or **reviewer-judged** (the validator accepts any non-vague string, so a human must confirm it is a *mechanism, not a pattern*).

The required-field set and types are `MECHANISM_CARD_REQUIRED_FIELDS` / `MECHANISM_CARD_FIELD_TYPES` (`mechanism_card.py:31-63`). Example values cited are from the admitted DK Track B card (`research/differentiated_substrate_v1/track_b/mechanism_card.json`).

### 2.1 Hypothesis — mechanism, not pattern

- [ ] **`expected_mechanism`** — *What is the causal/structural mechanism?* Substantive text (`≥32 chars`, `≥6 words`, `≥4 distinct words`, no vague phrases) — **machine-checkable for substance** (`_validate_substantive_text`, `mechanism_card.py:301-324`, applied to `rationale` and `expected_mechanism` at `:217-218`); **reviewer-judged for "mechanism, not pattern"** (the validator cannot tell a behavioral mechanism from a curve-fit description). DK Track B states the context factor "reads trailing range compression" and a *distinct* trigger family "reads a prior-high sweep then close-back-inside event."
- [ ] **`rationale`** — *Why is this worth a bounded test?* Same substantive-text gate. **Machine-checkable for substance; reviewer-judged for economic plausibility.** This carries the economic rationale that the Track A doc-schema put in `hypothesis.economic_rationale` (`MECHANISM_CARD_TEMPLATE.md`); under the canonical schema it lives here.

### 2.2 Direction, horizon, session (the pre-registered prior)

- [ ] **`expected_direction`** — *What forward direction/path outcome is predicted?* Non-empty, non-vague string — **machine-checkable** (`_validate_non_empty_text`, `mechanism_card.py:281-298`, rejects the `_VAGUE_TEXT` set incl. `tbd`/`unbounded`/`unknown`, `:65-80`). **Reviewer-judged** that it is a genuine pre-registered prior, not a post-hoc fit. DK Track B: `"target-before-stop path outcome after the reclaim event"`.
- [ ] **`horizon`** — *Over what forward horizon?* Non-empty non-vague — **machine-checkable**. DK Track B: `"120m"`. Reviewer must confirm horizon is pre-registered and counted against the FDR budget (budget machinery: `VariantLedger`, owned downstream).
- [ ] **`session`** — *Which session/window?* Non-empty non-vague — **machine-checkable**. DK Track B: `"RTH"`.

### 2.3 Inputs the idea consumes (declares the discovery surface)

- [ ] **`required_features`** — *Exactly which feature names does this read?* Non-empty `list[str]`, each item explicit/non-vague — **machine-checkable** (`_validate_list_of_text`, `mechanism_card.py:327-364`; empty list rejected at `:329-338`). DK Track B: `["liquidity_structure_range_contraction","liquidity_structure_failed_high_breakout_flag"]`. **Reviewer-judged**: that the named features exist in `governed_scope` (or trigger a `FeatureRequest`) — the *value-store/discovery* check is downstream, not at card validation.
- [ ] **`required_labels`** — *Which outcome label(s) does it predict?* Same list-of-text gate. **Machine-checkable for non-empty/explicit.** DK Track B: `["target_before_stop_120m_path_label"]`. The **path-label target** (see §3) is declared here and, for shape-bearing ideas, *also* pinned in the `SetupSpec.path_label` id.

### 2.4 Cost sensitivity

- [ ] **`cost_sensitivity`** — *Is the idea cost-fragile / does it need new data?* Non-empty mapping with explicit, non-null, non-vague keys/values — **machine-checkable** (`_validate_mapping_is_substantive` + `_validate_substantive_value`, `mechanism_card.py:367-459`; nulls rejected at `:400-409`). DK Track B: `{"new_data": false, "scope": "exploratory evidence only"}`. **Reviewer-judged** whether the cost note is honest. **Hard constraint:** ES/NQ/RTY existing data only — `new_data: true` implies a paid-feed/universe expansion that is out of scope unless separately authorized; reviewer must reject such an idea at intake.

### 2.5 Variant budget (anti-overfitting cap)

- [ ] **`variant_budget`** — *How many variants may this idea spend before the budget gate fires?* Exact positive `int` — **fully machine-checkable** (`_validate_variant_budget`, `mechanism_card.py:465-486`: rejects non-`int` and `≤0`). DK Track B: `1`. This declared cap is the surface the first-class `VariantLedger`/family-budget machinery (downstream, `governance/variant_ledger.py`) accounts against; the card only *declares* the cap.

### 2.6 REUSE / duplicate-exposure declaration

- [ ] **`duplicate_exposure`** — *Does this duplicate an already-tested mechanism?* REQUIRED non-empty mapping with explicit keys/values — **machine-checkable that the declaration is present and substantive** (same `_validate_mapping_is_substantive` gate, `:221-222`). DK Track B: `{"family_id": "dk_p04_track_b_range_contraction_failed_high_breakout", "status": "bounded", "variant_id": "…"}`.
  - **Reviewer-judged at the card layer:** whether the idea genuinely re-tests a dead mechanism (regime, vwap_session, bbo_tradability, liquidity_pa) or a prior REJECT. The card field is *self-declared intent* — the validator does **not** cross-check it against the registry.
  - **Machine-checkable downstream only:** the executable REUSE check is `check_duplicate_exposure(feature_request, registry_reader)` (`src/alpha_system/governance/duplicate_exposure.py:127`), which keys on a `FeatureRequest` against the SQLite factor registry and **fails closed when the registry is unavailable** (`:135`). It does **not** today accept a `MechanismCard`. So: cite `duplicate_exposure.py:127` as the dedup authority, declare the family/variant in this field, and treat the registry-level dedup as enforced *if/when* the idea spawns a `FeatureRequest`. (Wiring the existing `check_duplicate_exposure` to also accept the card's `required_features`/`duplicate_exposure` surface is the sanctioned enhancement, owned by `FACTORY_LINE_CHARTER.md` — never a new dedup gate.)

### 2.7 Provenance and stamp

- [ ] **`source`** — *Where did the idea come from?* Non-empty non-vague — **machine-checkable**. DK Track B: `"DK-P04 Track B differentiated context-not-equal-trigger probe"`.
- [ ] **`stamp`** — *EXPLORATORY-vs-TRUSTED self-declaration.* MUST be `"EXPLORATORY"` — **fully machine-checkable** (`_validate_stamp`, `mechanism_card.py:489-499`; `ALLOWED_MECHANISM_STAMPS = frozenset({EXPLORATORY_STAMP})`, `:30`; `EXPLORATORY_STAMP="EXPLORATORY"`, `:29`). See §5 — **there is no TRUSTED intake stamp**; the trusted lane is *not* an intake declaration.
- [ ] **`mechanism_id`** — *Deterministic content address.* Must equal the hash of all other fields (`generate_mechanism_id`, `mechanism_card.py:186`; mismatch raises at `:228-240`) and carry the `mech_` kind (`GovernanceIdKind.MECHANISM_CARD`, validated `:262-278`). **Fully machine-checkable** — generated, not hand-set; any post-hoc field edit changes the id, so the card is tamper-evident.

---

## 3. Path-label target the idea predicts

The intake card declares the predicted **path-label target** in `required_labels` (§2.3). For shape-bearing ideas it is *also* pinned by the `SetupSpec.path_label` id and `SetupSpec.target` (§4). The governed path-label family is the existing substrate — reuse it; do **not** define a new label at intake:

- Governed path-label names: `mfe`, `mae`, `target_before_stop`, `triple_barrier` (`configs/labels/scaleout/path.json:7-12`; enum `PathLabelName`, `src/alpha_system/labels/families/path/family.py:47-53`).
- DK Track B predicts `target_before_stop` over a fixed `120m` horizon (`track_b/setup_spec.json` `target.path_outcome = "target_before_stop"`, `horizon = "120m"`).

**Intake-time hazard the card must surface (reviewer-judged), grounded in the DK Track B degenerate slice.** `target_before_stop` is a barrier label with governed `target_return=+0.02`/`stop_return=-0.02` (`configs/labels/scaleout/path.json:108-110`, explicitly "no parameter sweep or tuning" at `:106-107`). On calm tape a ±2% move within 120 bars rarely touches, so the barrier resolves to `HORIZON → False` (`labels/families/path/family.py:329-339`; vectorized twin `src/alpha_system/labels/fast/path.py:330-343`) and the slice collapses to a **single class**. DK Track B's probe then computed `target_before_stop_probability = 0.0` on a constant label — caught only by a hand-written caveat, not a gate. Therefore:

- [ ] **Path-label resolvability declaration** — *On the intended data slice, will the predicted path-label resolve to ≥2 classes?* This is **reviewer-judged at intake** (no card field enforces it today; the executable single-class/class-balance FAIL gate exists at `src/alpha_system/runtime/diagnostics/label/runtime.py:893-900,945-949` keyed on `max_majority_class_share`, but the conditional probe path does not route through it). The intake reviewer must confirm the chosen (target, stop, horizon) × slice is plausibly two-class **before admission**. Making this an automatic preflight (routing the probe through the existing class-balance gate, or adding a ≥2-distinct-class precondition) is the substrate fix owned by `TESTABILITY_GATE.md` — not a new gate, an enhancement of the existing one.

---

## 4. SetupSpec companion checklist (context ≠ trigger ideas only)

If the idea is shape-bearing (the entry *context* must be structurally distinct from the entry *trigger*), the `MechanismCard` is **not sufficient** — a `SetupSpec` must also be admitted. Required fields: `SETUP_SPEC_REQUIRED_FIELDS` (`setup_spec.py:31-47`); types `setup_spec.py:51-67`. Example values from the admitted `track_b/setup_spec.json`.

- [ ] **`entry_context`** — the conditioning regime/bucket. Non-empty substantive mapping — **machine-checkable** (`_validate_mapping_is_substantive`, applied `setup_spec.py:221-231`). DK Track B: `factor_id = "liquidity_structure_range_contraction"`, `bucket = "range_contraction_high"`.
- [ ] **`event_trigger`** — the EXACT trigger expression, a **distinct** factor/event. Non-empty substantive mapping. DK Track B: `factor_id = "liquidity_structure_failed_high_breakout_flag"`, `event = "prior_high_sweep_close_back_inside"`.
- [ ] **context ≠ trigger SEPARATION** — *the load-bearing differentiator.* **Fully machine-checkable** via `_validate_event_trigger_is_separate` (`setup_spec.py:299-335`): the validator RAISES if `event_trigger` is the same object as `entry_context` (`event_trigger_aliases_entry_context`, `:302-311`), has identical canonical content (`event_trigger_matches_entry_context`, `:312-322`), or declares itself derived from entry_context via `alias`/`alias_of`/`derived_from`/`same_as`/`source_field` (`event_trigger_derived_from_entry_context`, `:325-334`; derivation keys at `:69-77`). This is the structural test that a "context≠trigger" idea is not a disguised main-effect factor. **Do not re-implement this separation logic anywhere else** — reuse this guard as the shape-testability primitive.
- [ ] **`regime_filter` / `confirmation` / `invalidation` / `stop` / `target` / `hold_time`** — all non-empty substantive mappings (`:221-231`). **Machine-checkable for substance; reviewer-judged for coherence.** DK Track B fixes ES/RTH, a fixed path stop, `target.path_outcome = "target_before_stop"`, and `hold_time.max_minutes = 120`. **Hard constraint:** `regime_filter.instrument_root` must be ES/NQ/RTY only (existing universe).
- [ ] **`path_label`** — `lspec_`-kinded id, validated as `GovernanceIdKind.LABEL_SPEC` (`_validate_ids`, `setup_spec.py:276-296`). **Machine-checkable.** DK Track B: `lspec_9f0c3e7b99d146e4046e1b4b`.
- [ ] **`allowed_variants` / `forbidden_post_hoc_changes`** — non-empty `list[str]`, explicit items — **machine-checkable**. The `forbidden_post_hoc_changes` list is the pre-registration lock (DK Track B forbids context-bucket, trigger-threshold, and target/stop changes after readout); reviewer confirms it is honest.
- [ ] **`mechanism_id`** — must reference the companion card's `mech_` id (validated `GovernanceIdKind.MECHANISM_CARD`, `:276-296`). **Machine-checkable.** DK Track B links `mech_651debd4497b065e1e121c3d`.
- [ ] **`stamp`** — MUST be `"EXPLORATORY"` (`ALLOWED_SETUP_STAMPS = frozenset({EXPLORATORY_STAMP})`, `setup_spec.py:30`; `_validate_stamp`). **Machine-checkable.**
- [ ] **`setup_spec_id`** — deterministic `setup_`-kinded content hash; mismatch raises (`setup_spec.py:239-252`). **Machine-checkable.**

---

## 5. EXPLORATORY-vs-TRUSTED self-declaration (the lane gate)

Every admitted card is **EXPLORATORY** at intake — this is enforced, not optional. Both `ALLOWED_MECHANISM_STAMPS` and `ALLOWED_SETUP_STAMPS` are `frozenset({EXPLORATORY_STAMP})` (`mechanism_card.py:30`, `setup_spec.py:30`), so a card stamped anything else is rejected by `_validate_stamp`. **There is no TRUSTED intake contract** — by design.

What the EXPLORATORY stamp means downstream (do not re-implement; reference):
- The stamp is the data that the promotion boundary keys on. `reject_exploratory_promotion_artifact` (`src/alpha_system/governance/promotion.py:386`, code `exploratory_artifact_refused`, `:92`) recurses the whole artifact tree and **fails closed on any nested EXPLORATORY stamp**, wired into `validate_governance_transition` *before* any lifecycle hop (`src/alpha_system/governance/promotion_gate.py:175`). An EXPLORATORY card therefore **cannot become promotion evidence**.
- The TRUSTED diagnostics lane is reached **only** via the value-free gap-report bridge (`src/alpha_system/governance/trusted_handoff.py`, `_require_exploratory_provenance` inverts the same guard at `:178`), which enumerates the AlphaSpec/StudySpec/FeatureRequest/LabelSpec gaps a separate trusted rerun must author. The trusted-lane main-effect scorer is `track_a_scorer.py` (value-bearing, no-second-PnL), reached after that handoff.

**Intake self-declaration checkbox:**
- [ ] **Lane declaration is `stamp = "EXPLORATORY"`** — **machine-checkable** (`_validate_stamp`). The card author must additionally **reviewer-judge** which downstream lane the idea is destined for and record it in `source`/`rationale` (main-effect → trusted diagnostics via `track_a_scorer`; context≠trigger shape → exploratory conditional probe). The card never *grants* trusted status; trusted entry is a separate authored rerun, governed by `FACTORY_LINE_CHARTER.md`.

---

## 6. Admission summary — machine vs reviewer split

| Check | Field(s) | Machine-checkable | Reviewer-judged | Authority (file:line) |
|---|---|---|---|---|
| Passes the executable validator at all | all required fields, exhaustive allow-list | ✅ | — | `mechanism_card.py:198,205`; `setup_spec.py:208,215` |
| Hypothesis is substantive text | `expected_mechanism`, `rationale` | ✅ (length/word/vagueness) | ✅ (mechanism *not* pattern; economic plausibility) | `mechanism_card.py:301-324,217-218` |
| Direction/horizon/session declared, non-vague | `expected_direction`,`horizon`,`session` | ✅ | ✅ (genuine pre-registered prior) | `mechanism_card.py:281-298,65-80` |
| Feature/label inputs explicit & non-empty | `required_features`,`required_labels` | ✅ | ✅ (inputs exist in governed_scope / need FeatureRequest) | `mechanism_card.py:327-364` |
| Path-label target declared | `required_labels`, (`SetupSpec.path_label`,`target`) | ✅ (id-kind, non-empty) | ✅ (resolvable ≥2-class on intended slice) | `family.py:47-53`; `path.json:7-12,108-110` |
| Cost sensitivity, ES/NQ/RTY only, no new data | `cost_sensitivity` | ✅ (substantive mapping) | ✅ (honest cost note; new_data=false) | `mechanism_card.py:367-459` |
| Variant budget is a positive int cap | `variant_budget` | ✅ | — | `mechanism_card.py:465-486` |
| REUSE / duplicate-exposure declared | `duplicate_exposure` | ✅ (present & substantive) | ✅ (not a re-test of a dead mechanism) | `mechanism_card.py:221-222`; dedup authority `duplicate_exposure.py:127` |
| context ≠ trigger separation (shape ideas) | `entry_context` vs `event_trigger` | ✅ (alias/match/derivation) | ✅ (genuine structural distinction) | `setup_spec.py:299-335,69-77` |
| Pre-registration lock | `forbidden_post_hoc_changes`,`allowed_variants` | ✅ (non-empty list of text) | ✅ (lock is honest) | `setup_spec.py:234-235` |
| EXPLORATORY stamp / lane self-declaration | `stamp` | ✅ (frozenset gate) | ✅ (intended downstream lane) | `mechanism_card.py:30,489-499`; `setup_spec.py:30` |
| Deterministic content-address id | `mechanism_id`,`setup_spec_id` | ✅ (hash match, kind) | — | `mechanism_card.py:186,228-240`; `setup_spec.py:239-252,276-296` |

**Net admission rule:** an idea enters the production line iff (a) it is expressed as a `MechanismCard` (plus a `SetupSpec` when shape-bearing) that PASSES the live `validate_*` functions above, and (b) a reviewer signs off on the four judgement-only items the validator cannot enforce — *mechanism-not-pattern*, *honest REUSE/dedup against dead mechanisms*, *path-label resolvability on the intended slice*, and *intended-lane coherence*. The DK Track B pair is the reference exemplar (verified to validate); the DK Track A doc-convention cards are **not** admitted by this contract until carried through the canonical `MechanismCard` schema.
