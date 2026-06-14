# PHASE_PLAN — DIFFERENTIATED_KILLSHOT_V1

6 phases (`DK-P00` … `DK-P05`) on a `dag_wave` scheduler with a serial merge queue. Phases have
linear dependencies and overlapping `src/`/`research/`/`tools/` footprints, so the DAG
**linearizes to sequential**: `P00 → P01 → P02 → P03 → P04 → P05`. Track A (P01–P03) and Track B
(P04) are LOGICALLY independent and could be parallelized in a future run; this first run keeps them
sequential for merge-safety, matching the proven SSRL pattern. Phase ids/lanes/deps/allowed_paths
are authoritative in `campaign.yaml`; this file mirrors them. Disagreement is a STOP condition.

## Scheduler Wave Map

```text
Wave 0 : DK-P00  Bootstrap + FDR active-subset RESTATEMENT (the FDR-before-metric gate) + REUSE-MAP/scope lock (YELLOW, run-alone)
Wave 1 : DK-P01  Zero-feed calendar substrate — new SESSION_CALENDAR_ROLL flags, parity-gated (YELLOW)
Wave 2 : DK-P02  Track A StudySpecs + declared-conditioning-factor admission + surrogate-FDR zero-pass (YELLOW)
Wave 3 : DK-P03  Track A real-data evidence + verdict refresh (YELLOW, FIRST real metric)
Wave 4 : DK-P04  Track B context≠trigger SetupSpec EXPLORATORY conditional probe, real slice (YELLOW)
Wave 5 : DK-P05  Verdict refresh + survivor gate + closeout (YELLOW)
```

## Phase contracts

### DK-P00 — Bootstrap + FDR Active-Subset Restatement + REUSE-MAP/Scope Lock (YELLOW)
Confirm the bundle + pointer; write `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md`
(value-free; the FDR-before-metric gate). It RESTATES — NOT via a `BudgetAmendmentRecord` (strictly-
increasing, cannot re-scope down) — the active surface: active = day_of_week, opex, month_end
(rebalance folded), roll_week, open_close; DEFERRED = fomc/cpi (`needs_paid_data`); overnight not
exercised. Per-mechanism `variant_budget` = horizon count (1,1,1,1,2); per-family budgets carried
unchanged (event-calendar 6, flow-seasonality 4); active effective pooled surface = **6**;
provenance + a created_at predating any variant. Write `REUSE_MAP`/`SCOPE` pinning reused machinery
+ the OUT-of-scope list. No code, no metric.

### DK-P01 — Zero-Feed Calendar Substrate (YELLOW)
Add five `SessionFeatureName` members (`is_opex_day_flag`, `is_quad_witch_day_flag`,
`is_month_end_session_flag`, `is_quarter_end_session_flag`, `in_roll_window_flag`) to the existing
`SESSION_CALENDAR_ROLL` family — double-implemented (reference `family.py` + polars
`fast/session_calendar_roll.py`) under the auto-derived **parity** gate, `live=True`/CAUSAL/
known-ahead, admitted via an APPROVED `FeatureRequest`. opex/quad-witch = analytic third-Friday
(opex every month; quad-witch Mar/Jun/Sep/Dec); month/quarter-end = last trading session within the
committed calendar's covered window (fail-absent outside, non-exchange-official non-claim);
in_roll_window via `roll_guard.classify_roll_window` (analytic CME quarterly roll, 2-before/1-after;
approximate-roll non-claim; NOT the offline `bars_to_roll`/`minutes_to_roll`). Materialize ES/NQ/RTY
locally. `day_of_week_effect` + `open_close_auction_flow` reuse existing members (no new build).

### DK-P02 — Track A StudySpecs + Surrogate-FDR Zero-Pass (YELLOW)
Author + lock five StudySpecs (calendar flag = declared conditioning factor, pooled ES/NQ/RTY,
forward-return labels at card horizons, `variant_budget` = horizon count, `family_budget` per family).
Make the **minimal** scoped change so an explicitly-declared calendar-conditioning factor is admitted
where `session_calendar_*` is otherwise skipped as support (preserve every gate; mutation-test).
Run `run_real_surrogate_calibration.py` per study (label_shuffle + trade_date_block nulls, K
pre-registered) into a fresh value-free report dir; gate `ZERO_PASS_MET`; any pass = `LEAKAGE_BLOCKED`
→ diagnose first. **No real-data metric inspected.**

### DK-P03 — Track A Real-Data Evidence + Verdict (YELLOW)
Score each locked StudySpec with the runtime factor diagnostics (directional/point-biserial IC +
buckets + walk-forward), loaded via the `tools/runtime` path (research never imports the value
engine). Record N_eff/power/MDE; ledger each variant; write `verdict_refresh.md` (`primary_state +
reason_code` per mechanism; value-bearing diagnostics permitted post-gate, research-only language,
no tradability claim). A WATCH/CANDIDATE survivor requires a `reviewer_verdict` artifact + reason_code
and is surfaced, never auto-promoted.

### DK-P04 — Track B Context≠Trigger EXPLORATORY Probe (YELLOW)
Author a MechanismCard + EXPLORATORY SetupSpec with **genuinely distinct** context vs trigger
signals (C1; e.g. a range-contraction/regime CONTEXT gating a SEPARATE sweep-then-reclaim TRIGGER;
target = path-label target-before-stop; hold ≤ 120m). Wire a `tools/runtime` row-injection harness
(load rows via `core/value_store.load_parquet_values`, run a label-shuffle surrogate for
`ZERO_PASS_MET`, call `evaluate_setup_conditional_probe`). Persist value-free `EVIDENCE.json`
(EXPLORATORY, `promotion_eligible:false`) or honest `DATA_GAP` (no fabricated values — C2). NO
promotion; `conditional_probe.py` byte-unchanged.

### DK-P05 — Verdict + Survivor Gate + Closeout (YELLOW)
Aggregate the five Track A verdicts + the Track B readout into `CAMPAIGN_VERDICT.md`; apply the
survivor gate (0 survivors = conclusive kill-shot; any survivor surfaced with reviewer verdict, no
factory by inertia); write the evidence summary + `RUN_SUMMARY`; carry caveats (zero-feed
approximations, N_eff limits, any DATA_GAP, fomc/cpi deferred). Research-only; no promotion.

## If this is too much
Collapse to P00–P03 (Track A only, drop Track B P04 + fold closeout). P00 is the FDR gate; P01–P03
are the differentiated Track A kill-shot; P04 is the strategy-shaped probe; P05 is the verdict.
Track A alone is a complete, conclusive differentiated kill-shot.
