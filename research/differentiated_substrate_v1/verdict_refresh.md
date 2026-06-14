# DK-P03 Verdict Refresh — Track A Differentiated Mechanisms (First Metric, Post-Gate)

Verdict refresh for `DK-P03` in `DIFFERENTIATED_KILLSHOT_V1`. This is the **first phase** in the
campaign chain permitted to read a real-data metric, unlocked only because two gates strictly
precede it: the DK-P00 FDR active-subset restatement (value-free pre-registration) and the DK-P02
surrogate-FDR `ZERO_PASS_MET` calibration for each scored study. This document consumes those
committed predecessor artifacts and the value-bearing per-mechanism diagnostics produced here; it
does not re-run, re-lock, re-scope, or amend them, and it does not promote any study.

Allowed primary states are only `REJECT`, `INCONCLUSIVE`, `WATCH`, and `CANDIDATE_RESEARCH`.
The closed campaign taxonomy is a **document/human/reviewer layer**; no runtime enum is added
(there is no `CANDIDATE_RESEARCH` runtime state). Value-bearing diagnostics are permitted here
(post-gate), but the prose stays research-only: **no** tradability, profitability, or alpha claim,
and no promotion.

## Evidence Inputs

Predecessor gates (committed before any metric was read):

- `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md` (DK-P00 value-free
  restatement; created `2026-06-14T03:45:38Z`).
- `research/differentiated_substrate_v1/surrogate_fdr/day_of_week_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/opex_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/month_end_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/open_close_calibration.md` — `ZERO_PASS_MET`.
- `research/differentiated_substrate_v1/surrogate_fdr/roll_week_calibration.md` —
  `CALIBRATION_BLOCKED` / `DATA_GAP` (no pass; `roll_week_flow` excluded from real-metric inspection).

Real-data diagnostics produced here (value-bearing, committed):

- `research/differentiated_substrate_v1/diagnostics/day_of_week.json`
- `research/differentiated_substrate_v1/diagnostics/opex.json`
- `research/differentiated_substrate_v1/diagnostics/month_end.json`
- `research/differentiated_substrate_v1/diagnostics/open_close.json`
- `research/differentiated_substrate_v1/diagnostics/DK_P03_TRACK_A_DIAGNOSTICS_SUMMARY.md`

Locked StudySpecs scored: `research/differentiated_substrate_v1/study_specs/{day_of_week,opex,month_end,open_close}.json`.

## Boundary Roll-Up

Active pooled surface scored this run = **5 tests** across **4 mechanisms** (day_of_week 1,
opex 1, month_end 1, open_close 2 horizons). `roll_week_flow` is a `DATA_GAP` exclusion (no clean
surrogate gate on this substrate) and is **not** counted as a scored `REJECT`/`INCONCLUSIVE`.

| State | Mechanisms | Scored tests |
| --- | ---: | ---: |
| `REJECT` | 4 | 5 |
| `INCONCLUSIVE` | 0 | 0 |
| `WATCH` | 0 | 0 |
| `CANDIDATE_RESEARCH` | 0 | 0 |
| (`DATA_GAP`, excluded — not scored) | 1 (`roll_week_flow`) | 0 |

**Survivor count: 0.** No mechanism landed `WATCH` or `CANDIDATE_RESEARCH`, so no independent
`reviewer_verdict` artifact was produced and nothing is surfaced for a survivor-gate decision.
This is a **conclusive, no-survivor refresh**: each scored mechanism resolved to
`DIAGNOSTICS_COMPLETE` on a well-powered sample with near-zero aggregate IC and non-monotonic
buckets, so the conservative, evidence-driven verdict is `REJECT` (not `INCONCLUSIVE` — the reads
are not underpowered).

## Refreshed Verdict Table

Each row maps the runtime `StudyRunResultState` to a closed-taxonomy `primary_state`. Pooled
ES/NQ/RTY, one test per (mechanism, horizon). `N_eff` / `MDE(|IC|)` are first-order
horizon-overlap reporting inputs, not significance results; `statistical_validity_claim: false`.

| Mechanism (study_spec_id) | Family | Horizon | Pearson IC | Rank IC | `N_eff` | `MDE(\|IC\|)` | Buckets monotonic | Runtime status | `primary_state` | `reason_code` |
| --- | --- | --- | ---: | ---: | ---: | ---: | :---: | --- | --- | --- |
| `day_of_week_effect` (`sspec_2ec71d30dadc48e237f9d04c`) | flow-seasonality | 30m | -0.00710 | -0.00496 | 243,144 | 0.003975 | no (mixed) | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| `opex_pinning` (`sspec_4936b2ee6614d4b869ec2787`) | event-calendar | 30m | -0.00488 | -0.00513 | 243,144 | 0.003975 | no (mixed) | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| `month_end_flow` (`sspec_c8669b6769a07d69ab897e58`) | event-calendar | 30m | -0.00144 | -0.00496 | 78,593 | 0.006991 | no (mixed) | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| `open_close_auction_flow` (`sspec_0c3386a2dd45451970547acd`) | flow-seasonality | 5m | 0.00082 | -0.00394 | 430,866 | 0.002986 | no (mixed) | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| `open_close_auction_flow` (`sspec_0c3386a2dd45451970547acd`) | flow-seasonality | 30m | -0.00083 | -0.01063 | 70,774 | 0.007368 | no (mixed) | `DIAGNOSTICS_COMPLETE` | `REJECT` | — |
| `roll_week_flow` (`sspec_61b60a8ca735bddea7feb9ff`) | flow-seasonality | 30m | — | — | — | — | — | (not run — `DATA_GAP`) | excluded | `DATA_GAP` (DK-P02 `CALIBRATION_BLOCKED`) |

All five scored tests returned full coverage (`coverage_ratio` = 1.0) and were well above the
underpowered floor (a usable `MDE(|IC|)` resolved), so none mapped to
`INCONCLUSIVE`+`UNDERPOWERED`. Each binary calendar / proximity flag is valued at every 1-minute
bar across the pooled ES/NQ/RTY window; the point-biserial IC is measured over the full sample,
the aggregate Pearson IC is indistinguishable from zero, and the 5-bucket forward-return
diagnostic is non-monotonic (direction `mixed`) for every read.

## Why No WATCH Or CANDIDATE_RESEARCH

No diagnostics evidence supports a `WATCH` or `CANDIDATE_RESEARCH` state:

- every scored read is `DIAGNOSTICS_COMPLETE`, resolver-clean, and well-powered, but the
  aggregate Pearson IC is near zero and bucket monotonicity is false for every mechanism;
- the asymmetric survivor gate is honored: a `DIAGNOSTICS_COMPLETE`, non-underpowered read maps
  to `REJECT`; effect size never **promotes** to a survivor in the scorer. The lone case where a
  rank-IC magnitude (open_close 30m, |rank_ic| = 0.0106) slightly exceeds its `MDE(|IC|)` (0.0074)
  is **not** minted as a survivor — the Pearson IC is ~0 and the buckets are non-monotonic, and a
  survivor is a reviewer/coordinator decision, not an isolated rank-IC magnitude;
- the declared secondary conditioning features (quad-witch, quarter-end, the close-proximity
  exposure) are within-mechanism near-duplicate exposures folded into the single pooled
  hypothesis, not independent confirmations;
- no independent reviewer verdict for `WATCH` / `CANDIDATE_RESEARCH` was produced, and the
  assigned `REJECT` states do not require one.

## Carried Caveats

- **`roll_week` `DATA_GAP`.** `roll_week_flow` was excluded from real-metric inspection: its
  DK-P02 surrogate calibration was `CALIBRATION_BLOCKED` (`no_numeric_declared_factors_for_surrogate`)
  because `session_calendar_roll_in_roll_window_flag` is all-null / zero-variance across all 24
  partitions, consistent with the R-036 offline-roll-metadata constraint and the 2024-26 calendar
  coverage. This is a substrate gap, not effect-size evidence; no `REJECT` is claimed for it.
- **Month-end / quarter-end 2024-26 coverage.** `month_end_flow` used 9 partitions and excluded
  15 under the sanctioned `all_null_values` path; the month-end / quarter-end flags are populated
  only over the 2024-26 window. The surviving sample is still large and well-powered.
- **Within-mechanism near-duplicate exposures.** The secondary conditioning features (quad-witch
  ⊂ OPEX, quarter-end ⊂ month-end, close-proximity mirroring open-proximity) are folded into the
  single pooled hypothesis and are not independent tests.
- **First-order N_eff.** `N_eff` is a deterministic first-order horizon-overlap reporting input
  over the capped usable IC pairs; it is not session-clustered or autocorrelation-adjusted and is
  not a significance result. Rows are not independent samples.

## Ledger / Budget Discipline

Every scored variant is recorded `VariantLedgerStatus.COMPLETED` within the pre-registered
family/variant budgets, with the fail-closed family-budget hook intact and not weakened:

| Mechanism | Family | `variant_budget` | observed | family_budget | family budget status |
| --- | --- | ---: | ---: | ---: | --- |
| `day_of_week_effect` | flow-seasonality | 1 | 1 | 4 | RESPECTED |
| `opex_pinning` | event-calendar | 1 | 1 | 6 | RESPECTED |
| `month_end_flow` | event-calendar | 1 | 1 | 6 | RESPECTED |
| `open_close_auction_flow` | flow-seasonality | 2 | 2 | 4 | RESPECTED |

No `BudgetAmendmentRecord` was authored; no per-instrument split; no horizon sweep beyond the
pre-registered count. The carried per-family budget caps are unchanged (event-calendar 6 still
includes the **deferred** fomc/cpi horizons; flow-seasonality 4); the active event-calendar
surface scored this run is only 2 (opex + month_end).

## Boundary And Non-Claims

This refresh is an evidence summary and allowed-state verdict record only. It does not create a
FactorLibrary ingestion record, Strategy Reference validation, AlphaBook entry, paper or live
trading behavior, broker/order behavior, deployment behavior, capital-allocation decision,
profitability claim, or tradability claim. `research/` imports none of
`backtest`/`management`/`fast_path`/`core.value_store`; values were injected from the
tools/runtime harness (no second PnL truth). Materialized values, local registries,
raw/canonical provider data, Parquet payloads, SQLite databases, and scratch reports remain
local-only and are not committed by this phase.
