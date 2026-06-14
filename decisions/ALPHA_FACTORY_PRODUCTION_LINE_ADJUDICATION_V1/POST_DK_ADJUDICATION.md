# POST_DK_ADJUDICATION

Research-only. No alpha/profit/tradability/production claims. Diagnostics and gates decide, never priors. All repo claims cite `file:line` verified in this checkout (`main`, 2026-06-14).

This adjudication records *what the second kill-shot (`DIFFERENTIATED_KILLSHOT_V1`, "DK") settled and what it left open*. It is the input to the production-line design captured separately in `FACTORY_LINE_CHARTER.md` (the generic Idea→verdict line), `IDEA_INTAKE_SCHEMA.md` (the unified MechanismCard/SetupSpec intake), `TESTABILITY_GATE.md` (the pre-probe precondition that the DK degeneracy motivates), and `NEXT_SHOT_SELECTION_RULE.md` (the rule for choosing the next shot). This file does not duplicate those; it is the evidentiary basis they reference.

---

## (A) WHAT DK RULED OUT — calendar/flow conditioning as a MAIN-EFFECT context is a WELL-POWERED CLEAN NULL

DK Track A scored calendar/flow conditioning variables as **main-effect context factors** (day-of-week, opex pinning, month-end flow, open/close auction flow) against the sanctioned factor-diagnostics + power path. The result is a **clean null reached on power, not on a prior**.

**1. Four mechanisms scored, all REJECT.** Each Track A diagnostics readout records `"primary_state": "REJECT"` with `"reason_code": null` and empty `"rejection_reason_codes"`:
- `day_of_week_effect` — `research/differentiated_substrate_v1/diagnostics/day_of_week.json:74,76,77`
- `opex_pinning` — `research/differentiated_substrate_v1/diagnostics/opex.json:76,78,79`
- `month_end_flow` — `research/differentiated_substrate_v1/diagnostics/month_end.json:76,78,79`
- `open_close_auction_flow` — `research/differentiated_substrate_v1/diagnostics/open_close.json:76,78,79`

The Track A summary states all four returned `DIAGNOSTICS_COMPLETE` with full coverage and near-zero, non-monotonic IC (`research/differentiated_substrate_v1/diagnostics/DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md:66,75-79,89,93-94`).

**2. The verdict branched on power (n_eff / MDE), NOT on IC magnitude.** The REJECT is produced by `map_runtime_state_to_primary_state` (`src/alpha_system/research/track_a_scorer.py:164-212`): a `DIAGNOSTICS_COMPLETE` read maps to `REJECT` *unless* it is underpowered (`underpowered = n_eff <= 1 or mde_abs_ic is None`, `track_a_scorer.py:199`), in which case it falls to `INCONCLUSIVE + UNDERPOWERED`. The `pearson_ic` / `rank_ic` arguments are passed but **unused** in the branch logic — the docstring and code both state effect size *never promotes* (`track_a_scorer.py:184-189,207-212`). These reads were not underpowered: the recorded effective samples and minimum-detectable-|IC| were `n_eff` 243,144 @ MDE 0.003975 (day_of_week, opex), 78,593 @ 0.006991 (month_end), 430,866 @ 0.002986 and 70,774 @ 0.007368 (open_close) — `DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md:75-79`. A near-zero IC at those MDEs is a **well-powered clean null**, not an absence of evidence.

**3. Each scored study cleared the surrogate-FDR gate before its real metric.** All four carry DK-P02 `ZERO_PASS_MET` recorded as `zero_pass_met_before_real_metric: true` in `study_specs/*.json` (`DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md:19-21`). `ZERO_PASS_MET` is the only non-blocked surrogate verdict (`src/alpha_system/governance/surrogate_run.py:1006-1011`), emitted only when zero label-shuffle surrogates pass the locked detection statistic; the six per-family real calibrations recorded "zero statistic passes; error count 0" (`research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md:31`).

**Ruling (A):** *Calendar/flow conditioning, treated as a stand-alone main-effect context factor, is a TESTED, WELL-POWERED, CLEAN NULL across the four scored mechanisms.* This is not "we didn't find it"; it is "we could have detected an IC down to ~0.003-0.007 and did not." This conclusion is durable and should be recorded against rejected memory (`src/alpha_system/governance/rejected_idea.py`, `ResearchGraveyardLedger`), not re-litigated.

---

## (B) WHAT REMAINS UNANSWERED — context≠trigger as a CONDITIONAL TRIGGER was never tested on a non-degenerate slice

DK Track B was the *exploratory* probe of the genuinely different shape: **context ≠ trigger** (an entry-context bucket conditioning a structurally distinct event-trigger over a path-label outcome). It did NOT produce a null. It produced a **degenerate, uninformative readout** and is therefore a **closable gap**, not a ruling.

**1. Track B ran on a single-class degenerate slice.** The committed Track B readout honestly flags `"single_class_path_outcome": true` and notes the materialized 120m target-before-stop slice (LCFP-P08 ES_2024 benchmark) is single-class — every outcome `False` under `horizon_no_barrier` — so the conditioned target-before-stop probability is degenerate and is "a substrate-coverage observation, not alpha, tradability, or profitability evidence" (`research/differentiated_substrate_v1/track_b/EVIDENCE.json:104-114`). It also carries `"promotion_eligible": false` (`EVIDENCE.json:107,131`), consistent with the EXPLORATORY-stamp refusal rail (`src/alpha_system/governance/promotion.py:386`). The power statement (MDE 0.040458 @ n_eff 2348, `EVIDENCE.json:116-129`) is numerically present but meaningless over a constant label.

**2. The degeneracy was caught post-hoc, not by a gate.** The conditional probe's only preconditions are empty-set guards (`src/alpha_system/research/conditional_probe.py:299-304` — raises on no-aligned-rows / no-conditioned-rows). There is **no ≥2-distinct-class precondition** on the path outcomes before `target_before_stop_probability` is computed (`src/alpha_system/research/events.py:77-94`). The single-class condition was recorded only by the hand-written `outcome_caveats` note, not by an automatic FAIL. (The pre-probe precondition that should have fired is the subject of `TESTABILITY_GATE.md`.)

**3. roll_week is an honest DATA_GAP, not a REJECT.** `roll_week_flow` was excluded from real-metric inspection: its sole conditioning flag `session_calendar_roll_in_roll_window_flag` is all-null / zero-variance across all 24 partitions, so its surrogate calibration was `CALIBRATION_BLOCKED` / `DATA_GAP` and the tool fail-closed with `no_numeric_declared_factors_for_surrogate` (`DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md:23-30`; flag declared at `research/differentiated_substrate_v1/study_specs/roll_week.json:18,24`). It carries a `DATA_GAP` caveat and is **not** a REJECT on effect-size evidence.

**4. The SSRL expression lane is built but unexercised on a barrier-resolving slice.** The executable context≠trigger lane exists and fail-closes correctly — `compile_setup_spec_to_conditional_probe` enforces EXPLORATORY stamp and `context.factor_id != trigger.factor_id` (`conditional_probe.py:171-185`), the SetupSpec separation guard structurally rejects a trigger that aliases the context (`src/alpha_system/governance/setup_spec.py:299`), and the DK Track B `setup_spec.json` validates against it. But the only time it ran end-to-end, it ran on a degenerate slice. The lane has **never been exercised on a real, barrier-resolving, two-class path-label slice.**

**Open question (B):** *Does a context≠trigger conditional structure carry information over a NON-DEGENERATE path-label outcome?* This is untested. It is the single largest unresolved shape in the substrate. The selection of how to close it is governed by `NEXT_SHOT_SELECTION_RULE.md`.

---

## (C) WHY — the substrate cause, and why it is CLOSABLE with existing data

**The cause is barrier geometry vs horizon on a calm-tape slice — a substrate degeneracy, not a conditioning-logic flaw.**

`target_before_stop` is a barrier label with governed `target_return = +0.02` / `stop_return = -0.02` over the forward horizon (`configs/labels/scaleout/path.json:108-110`, explicitly "no parameter sweep or tuning", `:106-107`). When neither barrier is touched within the horizon, both engines fall back to `PathBarrier.HORIZON`, which for `TARGET_BEFORE_STOP` maps to `value = False`:
- reference oracle: `src/alpha_system/labels/families/path/family.py:329-339`
- fast producer: `src/alpha_system/labels/fast/path.py:330-343` (with the vectorized `no_touch` screen at `:304-319`).

On a low-volatility 120-minute ES slice, a ±2% excursion within ~120 bars is rare, so essentially every row resolves `False` → **single-class**. `target_before_stop_probability` (`src/alpha_system/research/events.py:77-94`) then returns ~0.0 over a constant label. The conditioning logic is correct; the **label did not resolve** on that data slice. (MFE/MAE are continuous and would not have degenerated — only the barrier label collapsed.)

**Why this is CLOSABLE with existing ES_2020_120m data, not a new alpha bet.** A barrier-resolving alternative slice is already materialized and ACCEPTED: `partition_id "ES_2020_120m"`, `row_count 313156`, `overlap_rows 310547`, `n_eff_conservative 2609`, `variant target_before_stop`, `lver_f9b126…`, parquet (`research/futures_substrate_scaleout_v1/label_packs/path/coverage_matrix.json:2845-2867`). The 2020 tape spans the COVID volatility regime, where ±2% moves over 120m are common, so the barrier resolves into two classes — re-running the *same* pre-registered probe on this slice is a **DATA_GAP close-and-rerun on existing data** (the requeue/evidence-accrual pattern, `src/alpha_system/governance/requeue.py`), using ES/NQ/RTY data only, **no new universe, no paid feed, no new mechanism, no geometry sweep**.

**Caveat to verify before relying on the slice:** the coverage matrix records `row_count` and `n_eff` but NOT the TARGET/STOP/HORIZON class split. The remembered figure (309,206 False / 3,950 True) lives only in local-only parquet under `ALPHA_DATA_ROOT` and is currently un-re-verifiable from this checkout. The two-class split must be re-measured via `core.value_store.load_parquet_values` before the re-run is treated as barrier-resolving — and the re-run must route through the missing ≥2-class precondition (`TESTABILITY_GATE.md`) so a degenerate slice fails automatically rather than via a hand-written caveat.

---

## POST-DK STATE (one line for future agents)

> **Two kill-shots fired, 0 survivors: calendar/flow as a MAIN-EFFECT context is a tested WELL-POWERED CLEAN NULL (4 ZERO_PASS_MET REJECTs decided on n_eff/MDE, not IC priors); but context≠trigger as a CONDITIONAL TRIGGER on a non-degenerate path-label slice was NEVER TESTED — Track B ran on a single-class degenerate 120m slice (barrier did not resolve → `False`-only label → uninformative probe), roll_week is a DATA_GAP, and the SSRL lane is built but unexercised — so this is a CLOSABLE substrate gap re-runnable on existing ES_2020_120m data, NOT a new alpha bet; survivor gate remains 0 and nothing downstream is earned.**
