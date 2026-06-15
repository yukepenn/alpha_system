# PA_SETUP_DIAGNOSTICS_V0 — Findings + Pre-Registration

**Date:** 2026-06-15 · **Author:** Command Center Brain (coordinator) ·
**Route:** A (chosen in `RESEARCH_TRUTH_RECONCILIATION.md` §D) ·
**Lane:** context≠trigger / setup path-outcome · **Stamp:** EXPLORATORY,
research-only, non-promoting, no profitability/tradability claim.

> One-line: **the setup/path-outcome lane is functional end-to-end (first time
> confirmed), but every materialized barrier/bool path outcome is degenerate;
> the only non-degenerate path outcomes that exist TODAY are the continuous
> MFE/MAE labels.** The next unit is a governed extension to test setups on a
> continuous path outcome — no new materialization needed for a first diagnostic.

---

## 1. What we proved tonight (repo-verified)

**The context≠trigger fast_probe lane works end-to-end.** Running the
`track_b_es2020_120m` dogfood idea (ES_2020_120m, range_contraction context ×
failed_high_breakout trigger) through `alpha idea run` reached, for the first
time, an **all-PASS testability gate**:

| gate | result |
|---|---|
| `features_materialized` | PASS |
| `labels_path_labels_exist` | PASS |
| `path_label_two_class` | PASS (2 classes: 309206 / 3950) |
| `n_eff_mde_plausible_and_dedup_known` | PASS (n_eff=310547, MDE=0.00352) |
| `available_ts_and_surrogate_fdr_known` | PASS |

But the **fast readout = INCONCLUSIVE → final verdict DATA_GAP (SUBSTRATE_GAP)**:
surrogate-FDR `CALIBRATION_BLOCKED`, readout n_eff=0. The two-class gate passes
(≥2 classes) but the minority class is only **1.26%**, so after conditioning
(context ∩ trigger) the surrogate-FDR engine cannot calibrate. This is an
**honest substrate refusal, not a code bug and not a science null.**

## 2. The substrate gap is real and universal (base-rate diagnostic)

A scan of **all 168 materialized `target_before_stop` path partitions**
(ES/NQ/RTY × 2019–2026 × {5,10,15,30,60,120,240}m) found **0 partitions** with
minority-class share ≥ 10%, only **6** in the 2–10% band (all 240m). Minority
share rises monotonically with horizon but never reaches balance:

```
ES 2020 target_before_stop minority share by horizon:
  5m 0.01% · 10m 0.04% · 15m 0.07% · 30m 0.23% · 60m 0.64% · 120m 1.26% · 240m 2.46%
best across all 168: RTY_2020_240m = 4.97%
```

**Root cause:** the FUTSUB path labels were materialized with one fixed R-geometry
under which the target is rarely reached before the stop within the horizon — the
barrier is mostly **never touched ("neither")**, and `target_before_stop` (a bool)
lumps "neither" into False. Confirmed at the value level for ES_2020_120m:

| materialized version | outcome | distribution | usable? |
|---|---|---|---|
| `lver_f9b126…` | bool `target_before_stop` | true-rate **1.26%** | degenerate |
| `lver_45f469fb…` | int triple-barrier {−1,0,+1} | **97.3% = 0 (neither)** | degenerate |
| `lver_076a51db…` | float **MAE** | median −0.0018, continuous | **non-degenerate** |
| `lver_c0ee9e38…` | float **MFE** | median +0.0019, continuous | **non-degenerate** |

## 3. Decision

- **Barrier/bool path outcomes cannot fairly test a setup on existing data** —
  all are degenerate. Testing one would either hit CALIBRATION_BLOCKED (as
  observed) or be statistically meaningless.
- **MFE / MAE are continuous and non-degenerate and already materialized** for
  ES/NQ/RTY × years × horizons. A setup's path edge can be tested as *"does the
  conditioned (context ∩ trigger) subset have a different MFE / MAE / expected-R
  distribution than the unconditioned base rate?"* — a non-degenerate,
  governable path-outcome test.
- **No ungoverned analysis.** Per the no-second-truth law, MFE/MAE must be tested
  through the governed lane (testability gate + surrogate-FDR + memory routing),
  NOT an ad-hoc pandas comparison. The current `CONTEXT_NOT_EQUAL_TRIGGER` probe
  hard-codes a 2-class bool outcome, so this requires a YELLOW extension to accept
  a continuous path outcome.
- **Scope (verified by code-surface recon, premise CORRECTED):** the earlier
  "small / free REUSE of surrogate-FDR" framing was over-optimistic. The label
  casting / type routing (`label_version_map` → `_cast_label_value`) and the
  continuous diagnostics (`post_event_mfe_mae`, IC power) ARE reusable, BUT the
  label-shuffle surrogate (`run_label_shuffle_surrogate`, fast_probe.py:181-249)
  is **hard-wired to binary `target_before_stop`** (boolean shuffle +
  `target_before_stop_probability` probability-delta), and main_effect does NOT
  use this surrogate — so the surrogate effect-metric must be **generalized** to a
  continuous statistic (HIGH-risk tier). Real change surface ≈ **5 files / ~15
  functions** across `slice_spec.py`, `fast_probe.py`, `conditional_probe.py`,
  label diagnostics + tests, in **3 risk tiers** (low: outcome-selector metadata;
  medium: continuous distribution guard replacing the `class_count>=2` guard;
  high: continuous surrogate effect metric). **MEDIUM-scoped, ~2–3 PRs** — a
  proper YELLOW spec + codex execution + fresh review, not a one-shot hand edit.

## 4. Pre-registration (fixed BEFORE any readout — anti-p-hacking)

To avoid horizon/geometry/outcome shopping, the following are declared now:

- **Outcome:** continuous **MAE** (downside path risk) and **MFE** (upside path
  reward) as already materialized; **expected-R proxy** = conditioned mean MFE
  vs conditioned mean |MAE| (descriptive only, no entry/stop/target re-derivation).
- **Setup:** the existing pre-declared `dk_p04_track_b` setup (range_contraction
  context × failed_high_breakout trigger), geometry **unchanged**, no post-hoc edits.
- **Horizon:** test the SAME single horizon used by the existing slice (120m);
  the horizon is fixed by the slice, NOT chosen by scanning for the best result.
- **Diagnostic:** conditioned (context∩trigger) MFE/MAE distribution vs the
  unconditioned base-rate distribution; report lift, not a signal. Surrogate-FDR
  (label-shuffle) must calibrate and gate before any readout is interpreted.
- **Verdict mapping (setup lane, continuous outcome):** invalid/blocked →
  INCONCLUSIVE/DATA_QUALITY; too few conditioned events → UNDERPOWERED; no lift
  over base beyond surrogate noise → REJECT; surrogate-gated lift → SIGNAL_PENDING_REVIEWER.
  **Machine never promotes** (rail law). Promotion stays reviewer-gated.

## 5. Next unit (the build)

`PA_SETUP_DIAGNOSTICS_V0` YELLOW phase (MEDIUM, ~2–3 PRs; spec → codex → review):
1. **PR1 (low risk):** outcome-selector metadata — add an `outcome_label_type`
   (e.g. `mfe`/`mae`) to `SliceSpec`/`SetupSpec` so a setup can point at the
   continuous path-outcome label_version inside the materialized pack
   (`slice_spec.py`, threaded into `conditional_probe.build_path_label_observation_set`).
2. **PR2 (medium risk):** continuous outcome handling — branch
   `build_path_label_observation_set` to extract the continuous value, and replace
   the `class_count>=2` guard with a continuous **distribution/variance** guard for
   non-discrete outcomes (`conditional_probe.py`, label diagnostics).
3. **PR3 (high risk):** generalize the label-shuffle surrogate
   (`run_label_shuffle_surrogate` + `_conditional_uplift`) so the null is built by
   shuffling the continuous outcome and the effect metric is a continuous statistic
   (conditioned-mean delta / IC) instead of `target_before_stop_probability`.
4. Substrate-ready proof per the Never-Again law: prove MFE/MAE labels resolve for
   the slice, no new materialization, no force-recompute. Then run the
   pre-registered ES_2020_120m setup; route the honest verdict to memory.
5. (Deferred, separate) balanced **R-geometry barrier-label materialization** —
   only if a continuous-outcome diagnostic motivates it; it is a real label-adding
   substrate phase (pack-grained force-recompute hazard, calibration discipline)
   and must be its own spec, not bundled here.

**Optional cheap pre-build probe (no code change, governed):** author a
`main_effect` idea pointing the existing continuous main_effect lane at the **MFE
(or MAE) label_version** for the setup's context/trigger factors — a marginal
(non-conditional) IC test of factor→path-extreme. Clean null there would lower the
EV of the conditional build; non-null would raise it. This is the factor lane, not
the setup lane, so it informs but does not replace PR1–PR4.

## 6. Housekeeping recorded (not mainline)

- **Data-integrity audit (read-only) result:** no genuine duplicates, no
  corruption, no coverage gaps, no registered-but-missing files. ~799 parquet
  files (~2.92 GB) are on disk but absent from the registry ("orphans"), mostly
  superseded `dsv_*` feature/label materializations. **No deletion taken:** (a)
  there is no disk pressure (~21 GB used of ~400 GB real WSL headroom — note the
  `df` 927 G figure is the VHDX virtual ceiling); (b) the probe proved the
  resolver reads packs **by path**, so "not in registry ≠ unused" — mass-deletion
  is unsafe without per-file reference cross-checking. Deferred with this recorded
  plan; revisit only under real disk pressure or as a scoped cleanup phase.
- The dogfood DATA_GAP was run with `--no-persist`; **not** routed into the real
  fleet brain (dogfood is a loop/substrate probe, not a research hypothesis) —
  keeps the fleet memory clean (5 graveyard + 1 requeue + 0 signal unchanged).
