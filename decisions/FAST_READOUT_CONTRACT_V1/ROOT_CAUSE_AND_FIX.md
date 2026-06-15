# FAST_READOUT_CONTRACT_V1 — Root Cause of Compounding Inconsistencies + Generic Fix

Status: PROPOSED (decision doc + staged build plan)
Date: 2026-06-15
Lane: Yellow (material engineering; consolidation + typed contract + canary)
Scope: research_lane fast-probe readout seam and its consumers. No PnL/value
truth touched. Research-only.

## 0. Why this exists

The user observed: "the more we expand, the more bugs and inconsistencies we
find." This doc names the *specific* structural cause with repo evidence,
inventories every instance, and specifies one generic fix so the whole class
stops recurring. This is a known broad-mining prerequisite (typed FastReadout
contract + per-lane routing canary) — broad mining will fan thousands of ideas
across multiple lanes/outcome types, which would otherwise explode the drift
surface below.

## 1. Root cause (one sentence)

`fast_probe` returns an **untyped `dict` "readout"** that is the *glue seam*
between otherwise-typed islands; every downstream consumer re-discovers its
shape by string keys and recursive searches, so any rename/relocation/new-lane
drifts **silently** (`.get()` returns `None`, never raises) and gets absorbed by
multi-spelling fallbacks and mirror-parsers — so the drift surface grows
super-linearly (producers × consumers × spellings × lanes) as we expand.

The repo already types nearly everything *around* the seam — `ConditionalProbeReadout`
(`research/conditional_probe.py`), `SignalPendingReviewerRecord`
(`governance/signal_pending_reviewer.py`), `SliceSpec` (`research_lane/slice_spec.py`),
`TestabilityGateResult` (`research_lane/testability_gate.py`),
`FactorDiagnosticsRunResult` (`runtime/diagnostics/factor/runtime.py`). The
*readout that wires them together* is the one bare dict, so it is exactly where
drift concentrates.

## 2. Mechanism — why expansion multiplies bugs

1. **No single source of truth for keys.** Each consumer hard-codes string keys.
   A rename in the producer is invisible to consumers until a wrong value
   surfaces in a verdict.
2. **Shape is lane-dependent AND depth-varying.** `power.n_eff` is top-level in
   the setup lane but nested as `ic_power_n_eff` inside
   `readout.readout.factor_diagnostics_report.quality_summary` in the main_effect
   lane. Consumers cope with **recursive `_find_mapping_with_keys(readout, ("n_eff",))`**
   searches that are too broad and can grab the wrong nested `n_eff`.
3. **Silent failure.** `.get()` returns `None` on drift; downstream that becomes
   a *misclassified verdict*, not a crash (this session's #482 / #484 /
   n_eff-from-gate bugs are all this).
4. **Fallbacks are fossils of past drift.** Each `A or B or C` spelling chain is
   a scar from a previous rename, and each masks the *next* one.
5. **Mirror parsers guarantee divergence.** Identical parse logic is copy-pasted
   across `verdict_report.py` and `memory_router.py` with "Mirrors …" comments;
   "keep in sync" by comment never holds.
6. **Lane branching is hand-coded in 4 files** (`fast_probe`, `verdict_report`,
   `memory_router`, `reviewer`); adding a lane/outcome multiplies the edit
   surface and the chance one site is missed.

## 3. Full inconsistency inventory (verified, file:line)

### Class A — multi-spelling fallbacks (each = a fossilized past drift)
- `verdict_report.py:676-677` — verdict read as `verdict` ∨ `final_verdict` ∨ `report_verdict`.
- `verdict_report.py:692` — reason read as `reason_code` ∨ `verdict_reason_code`.
- `verdict_report.py:323-333` — minority count as `minority_class_count` ∨ `minority_count`.
- `verdict_report.py:345-350` — MDE as `minimum_detectable_effect` ∨ `minimum_detectable_abs_ic` ∨ `mde_abs_ic`.
- `slice_spec.py:212-250` — `from_mapping` tolerates `feature_inputs`∨`features`,
  `label_inputs`∨`labels`, `label_version_map`∨`label_versions`∨`path_label_versions`,
  `materialized_label_version`∨`label_version`, `data_version`∨`dataset_version_id`,
  `partition_id`∨`partition`.
- `testability_gate.py:119-169` — `from_mapping` tolerates `slice_id`∨`id`,
  surrogate-requirement 3-spelling, `feature_pack_refs`∨`feature_packs`,
  `label_pack_refs`∨`label_packs`, `n_eff`∨`effective_sample_size`, MDE 3-spelling.

### Class B — mirror parsers (duplicated logic, "keep in sync" by comment)
- `_continuous_lift_summary` — duplicated `verdict_report.py:157-166` ↔
  `memory_router.py:360-367` (the latter literally comments "Mirrors verdict_report._continuous_lift_summary").
  Both use a broad recursive `_find_mapping_with_keys` precisely because the lift
  is nested deep at `readout.diagnostics.continuous_outcome_mean_lift`
  (`research/conditional_probe.py:471`, carried under the readout's `diagnostics`,
  conditional_probe.py:488) — neither consumer hard-codes that path, they search
  for it. (The Stage-A typed contract extracts from this verified real location.)
- `_n_eff_mde` (`verdict_report.py:338-356`) ↔ `_setup_conditioned_n_eff`
  (`memory_router.py:344-357`, comment "Mirrors verdict_report._n_eff_mde").
- `_find_mapping_with_keys` recursive search — duplicated `verdict_report.py:796`
  ↔ `memory_router.py:370`.

### Class C — lane/depth drift (the dangerous one)
- Producer writes n_eff in **two** places: `gate["conditioned_n_eff"]`
  (`fast_probe.py:333`) and top-level `power.n_eff` (setup ZERO_PASS_MET path);
  main_effect nests it as `ic_power_n_eff` (`verdict_report.py:513`,
  `memory_router.py:274-281`).
- Consumers resolve n_eff via broad recursive `_find_mapping_with_keys(readout,
  ("n_eff",))` (`verdict_report.py:341`, `memory_router.py:354`) → can grab the
  wrong nested value. This is the exact bug fixed ad-hoc in #482/#484.
- `surrogate_fdr_gate` sub-dict read by 2 consumers with different sub-field
  expectations (`verdict_report.py:363-365` vs `memory_router.py:324-338`).
- `quality_summary` 3-level nesting traversed with different null-safety in each
  file (`verdict_report.py:488-491` loose vs `memory_router.py:408-415` checked).

### Class D — lane branching duplicated across files
- `study_kind` parsed + branched independently in `fast_probe.py:123-140`,
  `verdict_report.py:437-454`, `memory_router.py:259-265`, `reviewer.py:103-112`
  with local constants (`MAIN_EFFECT` vs `STUDY_KIND_MAIN_EFFECT` vs bare strings).

## 4. Generic fix — type the seam (kills the class)

One frozen-dataclass family `FastReadout`, matching existing house style
(`*_schema` / `to_dict`/`from_dict` + a module-level `validate_*`):

1. **Canonical field names = single source of truth.** A field-name registry
   (the dataclass fields themselves + a small constants module). Delete every
   multi-spelling fallback (Class A); `from_dict` accepts the canonical name
   only, and *raises* on unknown/missing required fields per lane.
2. **Lane-discriminated typed subtypes.** `MainEffectReadout` and `SetupReadout`
   (discriminated by `study_kind`), each with explicit typed fields — including
   **one canonical n_eff location per lane** (no depth-varying duplicate). This
   removes Class C.
3. **Loud validation at the boundary.** A shape mismatch fails at `from_dict`,
   not silently at a downstream `.get()`.
4. **One shared parser module; delete mirrors.** Consumers (`verdict_report`,
   `memory_router`, `reviewer`) read typed attributes; the duplicated
   `_continuous_lift_summary` / `_n_eff_mde` / `_find_mapping_with_keys`
   (Class B) collapse to the typed accessors. Lane branching (Class D)
   centralizes on the discriminated type.
5. **Per-lane routing canary** under `evals/canaries/` — exercises
   producer → verdict → router → record → reviewer for **both** lanes end-to-end
   and asserts the typed contract round-trips. Any future consumer drift fails
   CI. This is the "add a guard" half of fix-the-class-plus-guard.

### REUSE-MAP compliance
This does NOT rebuild `ConditionalProbeReadout`, `SignalPendingReviewerRecord`,
etc. It types the **one untyped seam between them** and consolidates the
duplicated parsers. It enhances existing governance/validation rather than
adding a parallel one.

## 7. Implementation notes (as built)

- **Stage A (#485):** typed `FastReadout` family + routing canary, additive,
  consumers untouched.
- **Stage A.2 (this PR):** Stage B's first attempt correctly STOPPED — the
  Stage-A contract under-specified the producer surface. There are **three**
  readout producers, not two: `fast_probe` (4 shapes) **plus**
  `cli/idea.py:_pre_probe_exploratory_readout` (the gate-FAIL / DATA_GAP path of
  `alpha idea run`), which emits a *partial* `surrogate_fdr_gate`
  (`gate_status`+`threshold_verdict` only) and an empty nested `readout`. A.2
  amended the contract to parse it faithfully: gate count fields optional
  (default 0, a not-run gate has 0 runs) with presence-tracking for exact
  round-trip; main_effect requires the IC summary only when RECORDED; setup
  RECORDED no longer hard-requires top-level `power`; the canonical `n_eff`
  accessor resolves IC→power→gate.conditioned_n_eff→0 (reproducing the old
  fallback). A.2 ALSO found a Class-A drift *inside* the `power` dict — the MDE
  key (`mde_abs_ic` from the sanctioned `build_ic_power_statement` vs
  `minimum_detectable_abs_ic` hand-written in `conditional_probe.py:483` and
  `cli/idea.py:582`) — and **canonicalized it at the source** to `mde_abs_ic`
  (value unchanged), so the contract reads one spelling.
- **Stage B (this PR):** consumers migrated onto typed attributes; Class A
  readout fallbacks, Class B mirror parsers
  (`_continuous_lift_summary`/`_n_eff_mde`/`_setup_conditioned_n_eff`/
  `_main_effect_quality_summary`) and the recursive `_find_mapping_with_keys`
  deleted from the readout path. `reviewer.py` (reads the shelf record, not the
  readout) and the `slice_spec`/`testability_gate` `from_mapping` alias-tolerance
  (a different contract) are out of scope — left as future work.
- **Behavior preserved:** whole suite green (incl. the IVL dogfood e2e that
  exercises the real signal-shelf path). The single behavior-test change is the
  authorized reversal of the over-strict "setup RECORDED requires power" rule.

## 5. Staged rollout (additive-first; working pipeline never breaks)

- **Stage A (additive, zero-break):** Add the `FastReadout` typed family +
  canonical-name constants + `from_dict`/`to_dict` + the routing canary. The
  canary asserts the *current* producer output parses into the typed contract
  for both lanes. Nothing deleted; producer output unchanged. CI green, pipeline
  identical. (This also pins the current shape as a regression baseline.)
- **Stage B (migrate consumers):** `verdict_report` / `memory_router` /
  `reviewer` read typed attributes; delete Class A fallbacks + Class B mirrors;
  centralize Class C/D. Stage A canary guards the migration.

Build parallel / merge serial; B depends on A. Worktree-isolated builds
(PYTHONPATH=<worktree>/src under the venv editable-install caveat). Main is
branch-protected (CI: canaries + validate×2).

## 6. Acceptance

- `FastReadout.from_dict` raises on missing required per-lane field (not None).
- Zero multi-spelling fallbacks remain in `verdict_report.py` /
  `memory_router.py` for readout fields (Class A cleared).
- `_continuous_lift_summary` / `_n_eff_mde` / `_find_mapping_with_keys` exist
  once (Class B cleared).
- Routing canary covers both lanes producer→reviewer and fails on a deliberately
  drifted field.
- `python tools/verify.py --all` + `python tools/hooks/canary_runner.py` green.
- No new PnL/value truth; research-only language preserved.
