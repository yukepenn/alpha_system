# TESTABILITY_GATE

Status: research-only governance artifact. No alpha, profitability, tradability, or production claim is made or implied anywhere below. This gate produces only diagnostic PRE-TEST verdicts (PASS / FAIL / DATA_GAP); it never promotes, never asserts an edge, and never substitutes for the reviewer-gated survivor decision.

Companion artifacts (referenced, NOT duplicated here): `POST_DK_ADJUDICATION.md` (why the prior shot was burned), `FACTORY_LINE_CHARTER.md` (the full Idea→verdict line this gate sits inside), `IDEA_INTAKE_SCHEMA.md` (the MechanismCard/SetupSpec intake contract this gate consumes), `NEXT_SHOT_SELECTION_RULE.md` (which slice/shot to run once this gate returns PASS).

---

## 1. Purpose and the lesson it encodes

The DIFFERENTIATED_KILLSHOT_V1 Track B probe was burned on a degenerate, single-class 120m `target_before_stop` slice. The failure is verified, structural, and was caught only by a hand-written caveat AFTER the metric ran, not by any pre-test gate:

- The barrier label falls back to `PathBarrier.HORIZON` when neither barrier is touched, and for `TARGET_BEFORE_STOP` that HORIZON fallback maps to `value=False` (`src/alpha_system/labels/families/path/family.py:329-339`). On a calm tape over 120 bars, a ±2% move (governed `target_return 0.02` / `stop_return -0.02`, `configs/labels/scaleout/path.json:108-110`) almost never touches, so essentially every row resolves False → single-class.
- The probe computed `target_before_stop_probability` directly over conditioned rows (`src/alpha_system/research/conditional_probe.py:362-365` → `src/alpha_system/research/events.py:75-93`) with NO ≥2-class precondition. On a single-class slice this returns a numerically "valid" probability with a power/MDE statement that is statistically meaningless.
- The degeneracy was flagged only post-hoc in a hand-written caveat: `research/differentiated_substrate_v1/track_b/EVIDENCE.json:107-113` (`single_class_path_outcome: true ... NOT alpha`), with the probe still reporting `mde_abs_ic 0.0405` at `n_eff 2348` on a constant label (`EVIDENCE.json:114-129`).

**TESTABILITY_GATE is the executable pre-registration gate a MechanismCard/SetupSpec MUST pass BEFORE any metric is computed.** Its single job: turn a slice that would have produced a meaningless readout into an explicit PRE-TEST `DATA_GAP` (or `FAIL`) verdict, so a kill-shot is never again spent on a degenerate slice. It composes EXISTING governance components; it does not introduce a new ledger, scorer, or class-balance gate. The companion `NEXT_SHOT_SELECTION_RULE.md` consumes this gate's verdict to choose the next slice.

---

## 2. Gate contract

- **Input:** a validated MechanismCard (`src/alpha_system/governance/mechanism_card.py:94`) — and, for context≠trigger shots, its SetupSpec (`src/alpha_system/governance/setup_spec.py:96`) — bound to a concrete data slice `(symbol, year, horizon, path-label variant)` per `IDEA_INTAKE_SCHEMA.md`.
- **Ordering law:** the gate runs strictly BEFORE any real metric (IC, target-before-stop probability, MFE/MAE) is computed. This is the same FDR-before-metric pre-registration discipline already used in the kill-shot readiness checklist; the gate makes the testability subset of that ordering an executable precondition rather than a doc-only check.
- **Output:** a single aggregate verdict over five checks, each emitting one of:
  - **PASS** — substrate is ready and the slice is testable; the shot may proceed to metric computation.
  - **FAIL** — a hard pre-registration violation (substrate not ready, surrogate calibration leakage/blocked, or N_eff structurally insufficient). The shot MUST NOT run. Record under the existing rejected/requeue surfaces; do not author a metric artifact.
  - **DATA_GAP** — the substrate is sound but the *chosen slice* cannot support a meaningful test (single-class path outcome, or barrier-resolvability unknown). This is the DK Track B class of outcome promoted to a PRE-TEST verdict. It is requeue-eligible: route to `src/alpha_system/governance/requeue.py` (`scan_requeue_candidates`, `RequeuedVerdictRecord`) for "closable gap → rerun on a resolving slice," never a fresh rejection record.
- **Aggregate rule (fail-closed):** verdict = PASS only if ALL five checks PASS. Any FAIL ⇒ aggregate FAIL. Otherwise (≥1 DATA_GAP and no FAIL) ⇒ aggregate DATA_GAP. Missing/unavailable inputs fail closed to FAIL, matching the surrounding governance posture (`src/alpha_system/governance/surrogate_run.py` namespace and registry checks all fail closed when inputs are absent).

---

## 3. The five checks

Each check below states (a) what it asserts, (b) the live component that enforces it, (c) PASS/FAIL/DATA_GAP outcomes. No check computes a real research metric; all are pre-test preconditions.

### Check 1 — Feature substrate-ready

**Asserts:** every feature named in the MechanismCard `required_features` (`src/alpha_system/governance/mechanism_card.py:94`, required field) is materialized for the chosen slice, the materialization is ADDITIVE (existing fvers preserved), the feature registry is locked, the resolver smoke is green, and the duplicate-exposure gate outcome is recorded. This check encodes the user-ratified **Never-Again: Feature Phase Substrate-Ready** rule (DK-P01 shipped flag code but never wired materialization, costing hours): a feature-adding shot must PROVE substrate-ready before a metric runs — (1) materialization config wired against the superset `governed_scope`, (2) additive dry-run preview preserving existing fvers, (3) registry lock + resolver smoke, (4) duplicate-exposure gate outcome recorded, (5) StudySpec lock proof.

**Live enforcing components (reuse, do not rebuild):**
- Materialization is declared via per-family scaleout configs with a `governed_scope` allow-list and parsed by the driver: `configs/features/scaleout/*.json` (e.g. `configs/features/scaleout/liquidity_sweep_pa_structure.json:7-14`); driver reads `governed_scope` at `src/alpha_system/features/scaleout/driver.py:572,575`. The `parameter_source` is fixed governed ("no parameter sweep or tuning", `configs/labels/scaleout/path.json:106-107`).
- New inputs gate through `src/alpha_system/governance/feature_request.py` (`FeatureRequest`, required `duplicate_or_equivalent_exposure_notes`) and the duplicate-exposure guard `src/alpha_system/governance/duplicate_exposure.py:127` (`check_duplicate_exposure`), fail-closed when the registry is unavailable. This check records its outcome; it does NOT add a new dedup gate (see `FACTORY_LINE_CHARTER.md` for where intake-layer dedup is wired).
- Registry lock + StudySpec lock proof: `src/alpha_system/governance/study_spec.py` content-addressed `study_spec_id` (`:214,:218 generate_study_spec_id`; `:260-265` id-mismatch fail-closed). Resolver smoke = the StudySpec lock resolving to the materialized Parquet for the slice.

**Outcomes:**
- PASS — all five substrate-ready conditions hold for the slice (materialization wired + additive, registry locked, resolver smoke green, duplicate-exposure outcome recorded, StudySpec lock verifies).
- FAIL — materialization not wired, fvers not preserved (non-additive), registry/resolver fails closed, StudySpec id mismatch, or a BLOCKING duplicate-exposure finding.
- DATA_GAP — feature declared and governed but not yet materialized for this specific slice (a closable gap; requeue when materialized).

### Check 2 — Label substrate-ready (path-label materialized for the slice)

**Asserts:** the path-label variant the shot will measure (`target_before_stop`, `triple_barrier`, `mfe`, or `mae`) is materialized and ACCEPTED for the exact `(symbol, year, horizon)` partition.

**Live enforcing components:**
- Governed path-label family: reference oracle `src/alpha_system/labels/families/path/family.py` (`PathLabelName` enum `:47-53`, `compute_path_label :244-272`) and parity-gated fast producer `src/alpha_system/labels/fast/path.py`; values written/read via `src/alpha_system/core/value_store.py:75-113` (`write_parquet_values`) and `:116-133` (`load_parquet_values`).
- Materialized-label registration: `src/alpha_system/labels/registry.py:419` (`register_materialized_label`), serial parent-only writes recording `producer_engine_id` + `value_schema_version`.
- Coverage record: `research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json` carries the per-partition `acceptance_state`, `row_count`, `n_eff_conservative`, `label_version_id`. Verified ACCEPTED example: `ES_2020_120m` `path_target_before_stop`, `row_count 313156`, `n_eff_conservative 2609`, `lver_f9b126…` (`coverage_matrix.json:2845-2867`).

**Outcomes:**
- PASS — the path-label variant is ACCEPTED for the slice in the coverage matrix and resolves through the label registry to materialized Parquet.
- FAIL — variant absent from the governed `governed_scope` (`configs/labels/scaleout/path.json:7-12`), or registry resolution fails closed.
- DATA_GAP — variant governed but not materialized/ACCEPTED for this partition (e.g. the FUTSUB `roll_week`/`in_roll_window_flag` all-null DATA_GAP class). Requeue-eligible.

### Check 3 — Path-label NON-DEGENERACY / single-class coverage  **(the DK Track B fix)**

**Asserts:** for a barrier path-label (`target_before_stop` / `triple_barrier`), the conditioned slice must contain BOTH classes (TARGET-resolving and STOP/HORIZON-resolving outcomes) each above a minimum absolute count, measured PRE-TEST. For a continuous variant (`mfe`/`mae`) the check asserts outcome variance > 0 (these resolve continuously and do not degenerate; `src/alpha_system/labels/path_metrics.py:31-61`). This is the precise check whose absence burned DK Track B.

- **Positive example (would PASS):** `ES_2020_120m` `target_before_stop` — the barrier-resolving slice. Its 309206 False / 3950 True split is the memory-recorded two-class distribution (minority count 3950 ≫ any sane floor). NOTE: the committed `coverage_matrix.json:2845-2867` records `row_count 313156` and `n_eff_conservative 2609` but does NOT store the True/False class split; that split currently lives only in local-only Parquet under `ALPHA_DATA_ROOT`. This check MUST re-measure the split at gate time via `src/alpha_system/core/value_store.load_parquet_values` — it must not trust an uncommitted figure.
- **Negative example (would DATA_GAP):** the DK Track B 120m slice (LCFP-P08 ES_2024 benchmark) where every outcome resolved False under HORIZON fallback (`family.py:329-339`), producing the degenerate readout flagged at `research/differentiated_substrate_v1/track_b/EVIDENCE.json:107-113`.

**Live enforcing component (reuse — do NOT build a new class-balance gate):** the label-diagnostics class-balance machinery already exists at `src/alpha_system/runtime/diagnostics/label/runtime.py` — `_class_balance_summary` (`:692-702`, emitting `class_count`, `majority_class_count`, `minority_class_count`, `majority_class_share`, `minority_class_share`) and the majority-share FAIL gate (`:893-900`, FAIL when `majority_class_share > config.max_majority_class_share`). The DK Track B probe BYPASSED this gate. The smallest correct upgrade is to route the slice's path-outcome distribution through `_class_balance_summary` (or extract a shared single-class precondition from it) at gate time, and to enhance the probe-side empty-set guards (`src/alpha_system/research/conditional_probe.py:299-304`) with a ≥2-distinct-class precondition on `path_outcomes` before any probability is computed. Reuse `events.target_before_stop_probability` (`src/alpha_system/research/events.py:75-93`) only AFTER this check passes; the recommended companion enhancement is to make it emit `class_count`/`minority_count` so a single-class result is self-evident rather than a silent 0.0.

**Minimum-count rule:** the gate FAILs/DATA_GAPs when `minority_class_count` is below a pre-registered floor OR `majority_class_share` exceeds `config.max_majority_class_share` (`runtime.py:893-900`). The floor and share threshold are pre-registered in the MechanismCard's testability block (`IDEA_INTAKE_SCHEMA.md`), locked before the metric, consistent with the no-sweep governance (`configs/labels/scaleout/path.json:106-107`).

**Outcomes:**
- PASS — barrier label: both classes present, `minority_class_count ≥ floor` and `majority_class_share ≤ threshold`; continuous label: outcome variance > 0.
- DATA_GAP — single-class (majority_share = 1.0) or minority below floor on this slice (the DK Track B case). The substrate is sound; the *slice* cannot support the test. Requeue and let `NEXT_SHOT_SELECTION_RULE.md` pick a barrier-resolving slice (e.g. ES_2020_120m).
- FAIL — barrier-outcome distribution unmeasurable because the underlying Parquet is unreadable/absent at gate time (fail closed; distinct from a clean single-class DATA_GAP).

**Coverage-record enhancement (reuse, not parallel inventory):** so slice selection is not blind to barrier resolvability, enhance the EXISTING coverage-matrix producer to record a per-partition barrier-outcome class-distribution field (TARGET / STOP / HORIZON / AMBIGUOUS share) alongside `row_count`/`n_eff` (`research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json`). This lets `NEXT_SHOT_SELECTION_RULE.md` query resolvability before a shot is even gated. Do not create a second inventory.

### Check 4 — N_eff sufficiency vs MDE

**Asserts:** the conditioned slice's overlap-discounted effective sample is large enough to resolve a usable minimum-detectable effect — i.e. the shot is not structurally underpowered before it runs. This catches the case where Check 3 passes (two classes) but the minority count / horizon overlap leaves N_eff too small for any meaningful MDE.

**Live enforcing components:**
- `src/alpha_system/runtime/diagnostics/splits/n_eff.py:260-303` (`estimate_n_eff`): purge/embargo removed first, then horizon-overlap discount, bounded by raw rows. `HorizonOverlapMetadata` fails closed if `discount_factor < 1` or understates overlap; `statistical_validity_claim: False` is baked in. The conservative, value-free power input.
- The asymmetric-gate mapper consumes this: `src/alpha_system/research/track_a_scorer.py:164-212` (`map_runtime_state_to_primary_state`) treats `underpowered = n_eff <= 1 or mde_abs_ic is None` (`:199`) and CANNOT promote on effect size — `pearson_ic`/`rank_ic` are accepted but UNUSED in branch logic. This gate reuses the same underpowered definition as its FAIL floor; it must NOT wire IC magnitude into the decision (a regression test pinning "effect size never promotes" is recommended).

**Outcomes:**
- PASS — `n_eff` over the conditioned set (not raw rows) supports an MDE below the pre-registered detectability ceiling for this slice.
- FAIL — `n_eff <= 1` or no usable MDE can be formed (structurally underpowered; the shot would only ever return INCONCLUSIVE+UNDERPOWERED — do not spend it).
- DATA_GAP — N_eff is below the pre-registered floor only because the slice is small/thin (closable by accruing more data); requeue via `requeue.py`.

### Check 5 — Surrogate-FDR calibration present + ZERO_PASS_MET, per-factor (no reuse)

**Asserts:** for every factor the shot will measure, a label-shuffled surrogate-FDR calibration EXISTS, was run in an ISOLATED per-factor namespace (no cross-factor / no FUTSUB reuse), and returned `ZERO_PASS_MET` (zero label-shuffle surrogates passed the detection statistic) BEFORE the real metric is computed.

**Live enforcing components:**
- `src/alpha_system/governance/surrogate_run.py`: `calibrate_surrogate_fdr` (`:889`), report builder `surrogate_calibration_report_from_rows` (`:989-1020`) → `LEAKAGE_BLOCKED` if any statistic passes, `CALIBRATION_BLOCKED` if any error, else `ZERO_PASS_MET` (`:1006-1011`; `ZERO_PASS_MET = "zero-pass-met"` at `:101`).
- Per-factor isolation (no reuse) is structurally enforced by `require_isolated_namespace` (`:1195-1236`) requiring an existing, writable, non-data-file directory per calibration, plus per-spec seeding (`base_seed + spec_index*run_budget + run_index`). Operationally proven: six separate per-family v2 real calibrations were required and recorded under `research/discovery_rigor_floor_v1/surrogate_fdr/` (`bbo_tradability_533f66_real_calibration_v2.md`, `liquidity_pa_840e83…`, `liquidity_pa_c237c6…`, `regime_dec89a…`, `vwap_session_1604b0…`, `vwap_session_f6cbd8…`). This matches the "calibration is per-factor (no FUTSUB reuse)" rule.

**Outcomes:**
- PASS — a per-factor isolated calibration exists for every measured factor and each returns `ZERO_PASS_MET`.
- FAIL — `LEAKAGE_BLOCKED` (a surrogate passed → leakage) or `CALIBRATION_BLOCKED` (calibration errored), or a reused/non-isolated namespace. The shot MUST NOT run.
- DATA_GAP — calibration not yet run for a factor on this slice (closable: run the per-factor calibration, then re-gate).

---

## 4. Why this is one gate, not five new modules (REUSE-MAP)

Every check above binds to a component that ALREADY EXISTS and is tested. TESTABILITY_GATE is a thin composition layer over them, mirroring how `promotion_gate.py` is itself a composition (`src/alpha_system/governance/promotion_gate.py:328-339` variant/family budget; `:346-397` sealed-holdout + locked-test contamination), NOT a monolith.

- Check 1 reuses `feature_request.py` + `duplicate_exposure.py:127` + `study_spec.py` content-hash lock + the scaleout driver — and encodes the Never-Again substrate-ready rule. No new dedup gate.
- Check 2 reuses `labels/families/path/family.py`, `labels/registry.py:419`, `core/value_store.py`, and the path coverage matrix. No new materialization path.
- Check 3 reuses `runtime/diagnostics/label/runtime.py` `_class_balance_summary` (`:692-702`) + majority-share FAIL gate (`:893-900`); the only code change is routing the probe path through it and enhancing the coverage matrix. **No new class-balance gate.**
- Check 4 reuses `splits/n_eff.py` `estimate_n_eff` and the `track_a_scorer.py` underpowered definition. No new power estimator.
- Check 5 reuses `surrogate_run.py` `calibrate_surrogate_fdr` / `ZERO_PASS_MET` / `require_isolated_namespace`. No shared calibration cache.

DATA_GAP outcomes route to the EXISTING `src/alpha_system/governance/requeue.py` evidence-accrual path; FAIL/REJECT memory routes to the EXISTING `src/alpha_system/governance/rejected_idea.py` `ResearchGraveyardLedger` (closed reason taxonomy — do not add a fourth enum). This gate introduces NO new ledger, NO new canary runner (any negative control belongs in `tools/hooks/canary_runner.py`), and NO promotion path — it is upstream of the asymmetric scorer and the reviewer-gated survivor decision, both of which remain unchanged.

---

## 5. The net effect: DATA_GAP becomes a PRE-TEST verdict

Before this gate, a degenerate slice produced a "valid"-looking metric that a hand-written caveat had to retroactively disown (`research/differentiated_substrate_v1/track_b/EVIDENCE.json:107-113`). After this gate, the identical slice returns **DATA_GAP from Check 3 before any metric is computed** — no kill-shot is spent, the gap is requeued, and `NEXT_SHOT_SELECTION_RULE.md` selects a barrier-resolving slice (the verified `ES_2020_120m` two-class partition, re-measured at gate time from local Parquet per Check 3). That is the entire point: testability is adjudicated up front, the failure mode that burned DK Track B is converted into an explicit, requeue-eligible PRE-TEST verdict, and the shot only runs when the substrate and the slice can actually support an honest read.
