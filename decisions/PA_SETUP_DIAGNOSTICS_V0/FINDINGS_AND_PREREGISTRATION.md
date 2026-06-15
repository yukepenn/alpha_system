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

## 7. End-to-end result + the overlap-validity finding (2026-06-15)

The continuous path-outcome capability landed in three increments: probe runtime
(PR #477), the testability gate (PR #478), and the slice-level continuous
metadata (n_eff/MDE + `continuous_label_summary`). With all three, the
**setup/path-outcome lane ran end-to-end for the first time**: the pre-registered
ES_2020_120m setup (range_contraction context × failed_high_breakout trigger) vs
the continuous **path_mfe** outcome reached an all-PASS gate and a `RECORDED`
fast readout — engine `evaluate_setup_conditional_probe`, conditioned n_eff=30342,
MDE≈0.01125, surrogate `ZERO_PASS_MET`. (Run `--no-persist`.)

**But the apparent signal is statistically untrustworthy — overlap-naive
surrogate.** `run_label_shuffle_surrogate` shuffles outcome values at the **row
level** and the conditional power uses the **raw conditioned count** (30342),
while `path_mfe` is a **120m forward-overlapping** label. Row-level shuffling
breaks the overlap autocorrelation, so the null variance is understated and
significance is inflated — the **same defect class** as the raw-n_eff IC inflation
that PR #474 fixed for the `main_effect` lane. PR #474 did **not** touch the setup
lane's surrogate or power. Therefore a setup-lane `ZERO_PASS_MET` on an overlapping
outcome **cannot be trusted as a signal** without overlap-aware treatment.

**The rail held.** The verdict classifier has no setup-lane mapping, so the readout
defaulted to **INCONCLUSIVE / DATA_QUALITY ("no governed final verdict")** — i.e.
the machine did **not** auto-promote the suspect signal. This conservative default
is, by luck of omission, the correct outcome. The readout was **not** persisted to
the fleet brain as a signal.

## 8. Next unit (corrected): extend the overlap law to the setup lane

Before any setup readout may be classified as a signal:
1. **Overlap-aware power for the setup lane** — discount the conditioned n_eff by
   the label horizon overlap (reuse `runtime/diagnostics/splits/n_eff.estimate_n_eff`,
   the same estimator behind PR #474), instead of raw `len(conditioned)`.
2. **Overlap-respecting surrogate** — replace/augment the row-level label shuffle
   with a block / horizon-aware shuffle (or an n_eff-discounted significance
   threshold) so the null variance reflects the 120m overlap. This is the
   load-bearing statistical fix and is a coordinator (my) design decision, not a
   delegated mechanical edit.
3. **Then** a setup-lane verdict mapping in `verdict_report.py` (parallel to
   `_derive_main_effect_verdict`): overlap-valid surrogate gate + conditioned-mean
   lift vs an overlap-aware threshold → REJECT (well-powered null) /
   SIGNAL_PENDING_REVIEWER (surrogate-gated) / REVIEW_NEEDED. Machine never promotes.

This is the honest continuation: the lane is built and runs; the **statistical
validity of overlapping path outcomes is the next gate**, exactly mirroring the
overlap law's spine. Until then, setup readouts stay non-promoting INCONCLUSIVE.

## 9. Overlap-aware result + the MAE control: a volatility confound, not an edge (2026-06-15)

The overlap law was extended to the setup lane (PR #479): `block_size`-blocked
label-shuffle surrogate (block = `required_future_bars`) + overlap-discounted
conditioned n_eff via the sanctioned `estimate_n_eff`. Fixture proof: an
autocorrelated outcome that row-shuffle falsely passes (0 exceedances →
ZERO_PASS_MET) is correctly blocked by block-shuffle (~98/300 exceedances →
CALIBRATION_BLOCKED).

**Re-running the real ES_2020_120m setup under block-shuffle (honest, predicted
wrong by me):**

| outcome | n_eff (overlap-aware) | MDE | surrogate | verdict |
|---|---|---|---|---|
| `path_mfe` (favorable) | 252 (was 30342) | 0.124 (was 0.011) | **ZERO_PASS_MET** | INCONCLUSIVE (non-promoting) |
| `path_mae` (adverse, control) | 252 | 0.124 | **ZERO_PASS_MET** | INCONCLUSIVE (non-promoting) |

I predicted the MFE `ZERO_PASS_MET` would flip to `CALIBRATION_BLOCKED` under
overlap-correct shuffling — it did **not**. But the pre-registered **MAE control**
resolves the interpretation: the conditioned subset (range_contraction ∩
failed_high_breakout) has **both** significantly elevated favorable excursion (MFE)
**and** significantly elevated adverse excursion (MAE). Both excursions rising
together is a **volatility-selection confound** — the setup picks higher-volatility
windows — **not a signed/directional tradable edge.** A real edge would show
**asymmetry** (favorable rising more than adverse, after cost), not symmetric
excursion inflation.

**Conclusion:** under honest overlap-aware statistics, this setup is **REJECT as a
directional edge** (volatility confound; no signed asymmetry). The machine did NOT
manufacture a signal: raw MFE significance alone would have looked like one, but the
adversarial MAE control + the non-promoting verdict default held the rail. This is
the methodology working as designed.

## 10. Next unit (refined by the confound): signed expected-R, not raw excursion

The real edge diagnostic for a setup is the **signed MFE-vs-MAE asymmetry /
expected-R**, cost-adjusted — never a single excursion's surrogate significance
(which is volatility-confounded). Next:
1. A governed **expected-R / excursion-asymmetry** diagnostic in the setup lane:
   conditioned (MFE − |MAE|) or target-vs-stop asymmetry vs base, under the same
   overlap-aware block surrogate; only a surrogate-gated **asymmetry** counts.
2. The setup-lane **verdict mapping** in `verdict_report.py` keyed off that signed
   asymmetry (REJECT volatility-confound / SIGNAL_PENDING_REVIEWER only on
   surrogate-gated signed edge / REVIEW_NEEDED). Machine never promotes.
3. Only then is a setup readout eligible to be recorded as a signal; raw single-
   excursion `ZERO_PASS_MET` must NOT route to the signal shelf.
