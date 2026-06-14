# DIFFERENTIATED_KILLSHOT_V1 — Campaign Verdict (Aggregation + Survivor Gate)

Phase `DK-P05`, campaign `DIFFERENTIATED_KILLSHOT_V1`. This is an **aggregation + adjudication**
document only. It runs **no new study, no new metric, no new calibration, no re-score**. It consumes
the locked, committed evidence of `DK-P03` (Track A real-data verdicts) and `DK-P04` (Track B
`EXPLORATORY` probe) **verbatim** and maps it to the closed campaign verdict taxonomy.

Allowed primary states are **only** `REJECT`, `INCONCLUSIVE` (with a `reason_code`), `WATCH`, and
`CANDIDATE_RESEARCH`. The closed campaign taxonomy is a **document / human / reviewer layer**; no
runtime enum is added (there is no `CANDIDATE_RESEARCH` runtime state). The prose is research-only:
**no** tradability, profitability, or alpha claim, and **no** promotion.

## Evidence Inputs (consumed, not re-derived)

Predecessor gates (committed strictly before any real-data metric — the FDR-before-metric chain):

- `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md` (DK-P00 value-free
  pre-registration restatement, created `2026-06-14T03:45:38Z`, before any variant attempt). Active
  pooled surface = day_of_week + opex + month_end + roll_week + open_close; `fomc`/`cpi` DEFERRED =
  `needs_paid_data`. Not a `BudgetAmendmentRecord` (that object is strictly increasing and cannot
  encode a downward re-scope).
- `research/differentiated_substrate_v1/surrogate_fdr/day_of_week_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/opex_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/month_end_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/open_close_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/roll_week_calibration.md` —
  `CALIBRATION_BLOCKED` / `DATA_GAP` (`no_numeric_declared_factors_for_surrogate`; no pass).

Track A real-data evidence (DK-P03):

- `research/differentiated_substrate_v1/verdict_refresh.md` (closed-taxonomy verdict refresh).
- `research/differentiated_substrate_v1/diagnostics/DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md`.
- `research/differentiated_substrate_v1/diagnostics/{day_of_week,opex,month_end,open_close}.json`
  (value-bearing per-mechanism diagnostics, post-gate).

Track B `EXPLORATORY` evidence (DK-P04):

- `research/differentiated_substrate_v1/track_b/EVIDENCE.json` (value-free `EXPLORATORY`
  `ConditionalProbeReadout`; `stamp: EXPLORATORY`, `promotion_eligible: false`).
- `research/differentiated_substrate_v1/track_b/{setup_spec,mechanism_card}.json`.

Survivor-gate framing precedent (the shape mirrored, not edited):

- `research/futures_substrate_scaleout_v1/rerun/verdict_refresh.md` (FUTSUB-P29 no-survivor refresh).

## Per-Item Verdict Table — All 5 Track A Mechanisms + 1 Track B Item

Each row reproduces the upstream `primary_state` + `reason_code` (or the Track B `status` +
`issue_code`) verbatim. No state is re-derived, "upgraded", or changed. Pooled ES/NQ/RTY, one test
per (mechanism, horizon). `N_eff` / `MDE(|IC|)` are first-order horizon-overlap **reporting inputs**,
not significance results; every read carries `statistical_validity_claim: false`.

| # | Mechanism (study_spec_id) | Family | Horizon | Pearson IC | Rank IC | `N_eff` | `MDE(\|IC\|)` | Runtime status | `primary_state` | `reason_code` |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | `day_of_week_effect` (`sspec_2ec71d30dadc48e237f9d04c`) | flow-seasonality | 30m | -0.00710 | -0.00496 | 243,144 | 0.003975 | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| 2 | `opex_pinning` (`sspec_4936b2ee6614d4b869ec2787`) | event-calendar | 30m | -0.00488 | -0.00513 | 243,144 | 0.003975 | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| 3 | `month_end_flow` (`sspec_c8669b6769a07d69ab897e58`) | event-calendar | 30m | -0.00144 | -0.00496 | 78,593 | 0.006991 | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| 4a | `open_close_auction_flow` (`sspec_0c3386a2dd45451970547acd`) | flow-seasonality | 5m | 0.00082 | -0.00394 | 430,866 | 0.002986 | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| 4b | `open_close_auction_flow` (`sspec_0c3386a2dd45451970547acd`) | flow-seasonality | 30m | -0.00083 | -0.01063 | 70,774 | 0.007368 | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| 5 | `roll_week_flow` (`sspec_61b60a8ca735bddea7feb9ff`) | flow-seasonality | 30m | — | — | — | — | not run (excluded) | `INCONCLUSIVE` | `DATA_GAP` (DK-P02 `CALIBRATION_BLOCKED`) |
| TB | Track B `context≠trigger` probe (`setup_c49fe5e7f8c17305db51a9bd`, `tbrun_6161efcc7e6643f0715c5a17`) | differentiated context-not-equal-trigger | 120m | n/a (path outcome) | n/a | 2,348 | 0.040458 | `RECORDED` / `EXPLORATORY` | `INCONCLUSIVE` | `DATA_GAP` (single-class 120m path slice) |

Notes on the two non-scored rows:

- **`roll_week_flow` (#5)** is the only Track A mechanism never scored on real data. Its DK-P02
  surrogate calibration was `CALIBRATION_BLOCKED` / `DATA_GAP`: the sole conditioning flag
  `session_calendar_roll_in_roll_window_flag` is all-null / zero-variance across all 24 partitions
  (`all_null_values` exclusion fired on every partition → `no_numeric_declared_factors_for_surrogate`,
  consistent with the R-036 offline-roll-metadata constraint). It is mapped to `INCONCLUSIVE` +
  `DATA_GAP` (a **substrate gap, never a `REJECT` on effect-size evidence**) — the FDR-before-metric
  gate correctly refused to read a metric for it.
- **Track B (TB)** is a permanently `EXPLORATORY`, `promotion_eligible: false` readout (DK-P04). It ran
  on **real, locally-materialized** ES_2024 rows (aligned `25,219`; conditioned `2,348`), and its
  surrogate-FDR gate reached `ZERO_PASS_MET` (`run_count 64`, `gate_pass_count 0`) FDR-before-metric.
  But the only materialized 120m `target_before_stop` slice
  (`ES_2024_120m_lcfp_p08_es_202406`) is **single-class** — every one of the 26,184 outcomes is
  `False` under `horizon_no_barrier` (the 120m barrier was never hit in that LCFP-P08 June-2024
  benchmark slice), so the conditioned target-before-stop probability is degenerate (`0.0`) and the
  context≠trigger conditioning **could not be exercised**. This is an honest **substrate-coverage
  `DATA_GAP`, not a clean null and not a failure** (`outcome_caveats.single_class_path_outcome: true`,
  `fabricated_values: false`). The probe **plumbing is validated**; the differentiated bet itself is
  **UNANSWERED**.

## Boundary Roll-Up

The roll-up counts the **full pre-registered surface** (all 5 Track A mechanisms + the 1 Track B
item). Every cell is traceable to the per-item rows above.

| State | Track A mechanisms | Track A scored tests | Track B items | Total items |
| --- | ---: | ---: | ---: | ---: |
| `REJECT` | 4 | 5 | 0 | 4 |
| `INCONCLUSIVE` (+`reason_code`) | 1 (`roll_week_flow` — `DATA_GAP`) | 0 | 1 (Track B — `DATA_GAP`) | 2 |
| `WATCH` | 0 | 0 | 0 | 0 |
| `CANDIDATE_RESEARCH` | 0 | 0 | 0 | 0 |
| **Total** | **5** | **5** | **1** | **6** |

Item accounting (must reconcile): 4 `REJECT` (`day_of_week_effect`, `opex_pinning`, `month_end_flow`,
`open_close_auction_flow` — the latter scored at 5m + 30m = 5 scored tests) + 2 `INCONCLUSIVE` +
`DATA_GAP` (`roll_week_flow` substrate gap; Track B single-class-slice substrate gap) = **6 items
total**, with the active scored pooled surface = **5 tests across 4 mechanisms**. **`WATCH` = 0,
`CANDIDATE_RESEARCH` = 0.**

## Survivor Gate — Applied

**Survivor count = 0.** No Track A mechanism landed `WATCH` or `CANDIDATE_RESEARCH`; the Track B
readout is permanently `EXPLORATORY` / `promotion_eligible: false` and can **never** be a survivor.
Because zero `WATCH` / `CANDIDATE_RESEARCH` survivors exist, the asymmetric survivor gate takes the
**no-survivor branch**: **no `reviewer_verdict` survivor artifact is required** (mirrors FUTSUB-P29),
nothing is surfaced for a survivor-gate decision, and **nothing is promoted**.

### This is a conclusive, trustworthy negative — the argument (earned, not asserted)

A no-survivor result is conclusive **only because** the truth chain held every phase. The closeout
states the argument rather than asserting "0 survivors":

1. **FDR before metric.** The DK-P00 FDR active-subset restatement (value-free) was committed
   `2026-06-14T03:45:38Z`, **before any variant attempt**, pinning the active pooled surface; and the
   DK-P02 surrogate-FDR calibration reached `ZERO_PASS_MET` for every scored study **before** any
   real-data metric was read. No metric was inspected ahead of its gate.
2. **The surrogate zero-pass gate held honestly, including the fail-closed case.** Four mechanisms
   reached `ZERO_PASS_MET`; `roll_week_flow` was **refused** (`CALIBRATION_BLOCKED` / `DATA_GAP`) rather
   than force-passed — the machine declined to read a metric it had no clean gate for. The Track B
   probe's label-shuffle surrogate reached `zero-pass-met` (`run_count 64`, `gate_pass_count 0`).
3. **The safety canaries stayed green.** `planted_fake_alpha`, the true-alpha pair,
   `forbidden_second_pnl_truth`, `forbidden_exploratory_promotion`, `governance_random_target`, and
   `forbidden_scope_drift` all PASS — so a planted fake edge would have been caught, a true edge would
   have been detected, no second PnL truth leaked, and the `EXPLORATORY` Track B artifact is refused by
   the promotion path.
4. **The 4 scored Track A reads were well-powered, not underpowered.** Each is `DIAGNOSTICS_COMPLETE`
   with full coverage (`coverage_ratio = 1.0`) and `N_eff` in the tens-to-hundreds of thousands, so a
   usable `MDE(|IC|)` resolved and none maps to `INCONCLUSIVE` + `UNDERPOWERED`. The aggregate Pearson
   IC is indistinguishable from zero and every bucket diagnostic is non-monotonic. **The four
   zero-feed calendar / flow-seasonality mechanisms are a tested, well-powered CLEAN NULL** — not an
   underpowered "don't know".

So on the four gated mechanisms this is a **successful, conclusive kill-shot** (the second to land
clean; FUTSUB was the first): differentiated zero-feed calendar / flow-seasonality conditioning did
**not** carry detectable intraday directional signal on this substrate, under the same rigor that
produced a trustworthy negative before. **`roll_week` and Track B are NOT clean nulls — they are
substrate `DATA_GAP`s** with no remaining effect-size evidence either way, carried as honest
`INCONCLUSIVE` + `DATA_GAP`, never as `REJECT`.

### Well-powered clean null vs substrate `DATA_GAP` (explicit distinction — load-bearing)

| Class | Items | What it means | What it does NOT mean |
| --- | --- | --- | --- |
| **Well-powered CLEAN NULL** | `day_of_week_effect`, `opex_pinning`, `month_end_flow`, `open_close_auction_flow` (5 scored tests) | Scored on real, well-powered, full-coverage pooled data; near-zero IC, non-monotonic buckets → conservative `REJECT`. The machine could have detected an effect down to the reported `MDE(\|IC\|)` and did not. | Not underpowered; not a missing-substrate excuse. A genuine, conclusive negative. |
| **Substrate `DATA_GAP`** | `roll_week_flow`; Track B `context≠trigger` probe | The mechanism could not be exercised on the available substrate (`roll_week`: all-null conditioning flag; Track B: single-class 120m path slice). No clean metric was read. | **Not a `REJECT`** and **not a clean null.** The bet is **UNANSWERED**, not answered negatively. Closable by a non-degenerate substrate slice (see POST-DK adjudication). |

## Carried Caveats (forward, verbatim from DK-P03 / DK-P04)

- **`roll_week` `DATA_GAP`.** `session_calendar_roll_in_roll_window_flag` is all-null / zero-variance
  across all 24 partitions (R-036 offline-roll-metadata constraint; roll-related conditioning is
  effectively populated only over the 2024-26 calendar coverage and carries no usable variation there).
  Substrate gap, not effect-size evidence.
- **Track B single-class 120m path slice `DATA_GAP`.** The only materialized 120m
  `target_before_stop` slice (`ES_2024_120m_lcfp_p08_es_202406`) is single-class (all `False`,
  `horizon_no_barrier`). The conditioning could not be exercised; the readout is `EXPLORATORY` /
  non-promotion with `fabricated_values: false`. The probe plumbing is validated; the bet is
  unanswered.
- **Month-end / quarter-end 2024-26 coverage.** `month_end_flow` used 9 partitions and excluded 15
  under the sanctioned `all_null_values` path; the month-end / quarter-end flags are populated only
  over the 2024-26 window. The surviving sample is still large and well-powered.
- **Zero-feed calendar approximations (non-claim).** opex / quad-witch = analytic third-Friday;
  month-end / quarter-end = last trading session within the committed calendar's covered window
  (non-exchange-official); `in_roll_window` = approximate analytic CME quarterly roll via
  `roll_guard.classify_roll_window`. These are deterministic zero-feed approximations, not
  exchange-official calendars.
- **Within-mechanism near-duplicate secondary exposures.** Quad-witch ⊂ OPEX, quarter-end ⊂
  month-end, and close-proximity mirroring open-proximity are folded into the single pooled hypothesis
  per mechanism — **not** independent confirmations or extra survivor evidence.
- **First-order `N_eff` / power / MDE limits.** `N_eff` is a deterministic first-order
  horizon-overlap reporting input over capped usable IC pairs; it is **not** session-clustered or
  autocorrelation-adjusted and is **not** a significance result. Rows are not independent samples;
  `statistical_validity_claim: false` on every read. `N_eff` / `MDE` are metadata, not significance.
- **`fomc` / `cpi` DEFERRED = `needs_paid_data`.** The macro-surprise cards remain deferred until a
  feed is onboarded; a zero-feed scheduled-time stub would be a different, weaker mechanism and is out
  of scope. The carried event-calendar family budget cap of 6 still includes these deferred horizons;
  the active event-calendar surface scored this run was only 2 (opex + month_end).
- **Governed overnight family DEFERRED (no cards this round).** The
  `OVERNIGHT_FAMILY_DESIGN_NOTE.md` is a value-free design note only; no overnight cards, `LabelSpec`,
  or `FeatureRequest` were authored, and any paper/live overnight use is RED-lane (gap-risk approval
  gate).
- **Carried-evidence integrity (C2 / C3).** The SSRL first-light `EVIDENCE.json` is an honest
  `DATA_GAP`, **not** real ES_2024 evidence, and is **not** cited as a result (C2). The de-stack
  `ic = 0.068 / n = 6862` is a carried SHIP_REFIT restatement, **not** fresh corroboration, and is
  **not** referenced as such (C3).

## Boundary And Non-Claims

This document is an evidence summary and allowed-state verdict record only. It creates no
`FactorLibrary` ingestion record, no `AlphaBook` / Strategy-Reference entry, no `PromotionDecision`,
no paper / live / broker behavior, no deployment, and no capital-allocation decision. It makes **no**
profitability, tradability, or alpha claim. The Track B `EXPLORATORY` readout is **context** here,
never promotion evidence, and the trusted resolver still refuses it
(`forbidden_exploratory_promotion`). `research/` imports **none** of
`backtest` / `management` / `fast_path` / `core.value_store`; no value was computed in this phase —
outcomes were injected upstream from `tools/` / `runtime/`. Materialized values, local registries,
raw / canonical provider data, Parquet payloads, SQLite databases, and scratch reports remain
local-only and are not committed.
