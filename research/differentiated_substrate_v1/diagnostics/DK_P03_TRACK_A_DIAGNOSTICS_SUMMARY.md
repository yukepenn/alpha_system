# DK-P03 Track A Real-Data Diagnostics Summary

Research-only diagnostics summary for `DK-P03` in `DIFFERENTIATED_KILLSHOT_V1`. This
document cites the value-bearing per-mechanism diagnostics JSON committed alongside it
(`research/differentiated_substrate_v1/diagnostics/{day_of_week,opex,month_end,open_close}.json`)
and feeds the closed-taxonomy `verdict_refresh.md`. It records diagnostics inputs and the
runtime `StudyRunResultState` each verdict was derived from. It makes **no** tradability,
profitability, or alpha claim; every readout carries `statistical_validity_claim: false`.

## Gate Ordering Consumed (Not Re-Opened)

This phase read a real-data metric only because two predecessor gates were committed first:

- **DK-P00 FDR active-subset restatement** (value-free pre-registration note):
  `research/differentiated_substrate_v1/FDR_ACTIVE_SUBSET_RESTATEMENT.md` (created
  `2026-06-14T03:45:38Z`, before any variant attempt). It pins the active pooled surface and
  carries the existing family budgets unchanged; it is **not** a `BudgetAmendmentRecord`
  (that object is strictly increasing and cannot encode a downward re-scope).
- **DK-P02 surrogate-FDR `ZERO_PASS_MET`** per scored study
  (`research/differentiated_substrate_v1/surrogate_fdr/{day_of_week,opex,month_end,open_close}_calibration.md`,
  recorded in each `study_specs/*.json` as `zero_pass_met_before_real_metric: true`).

`roll_week_flow` is **excluded** from this phase's real-metric inspection: its DK-P02 surrogate
calibration was `CALIBRATION_BLOCKED` / `DATA_GAP` (the sole conditioning flag
`session_calendar_roll_in_roll_window_flag` is all-null/zero-variance across all 24 partitions;
all partitions excluded under the sanctioned `all_null_values` path, and the tool fail-closed
with `no_numeric_declared_factors_for_surrogate`). No clean surrogate gate exists on this
substrate, so no metric was read for it (consistent with the R-036 offline-roll-metadata
constraint and the 2024-26 calendar coverage). It carries a `DATA_GAP` caveat in the verdict
refresh and is **not** a `REJECT` on effect-size evidence.

## How Each Mechanism Was Scored (Reused Engines, Not Re-Implemented)

- The real metric is produced by the existing runtime factor diagnostics engine
  `build_factor_diagnostics_run` (`src/alpha_system/runtime/diagnostics/factor/runtime.py`),
  which computes the directional / point-biserial Pearson and rank IC (via the sanctioned
  `alpha_system.research.ic` module), bucket diagnostics, walk-forward folds, and a coverage /
  availability gate, returning a `StudyRunResultState`
  (`DIAGNOSTICS_COMPLETE` / `INCONCLUSIVE` / `DIAGNOSTICS_FAILED` / `REJECTED`).
- **No-lookahead is enforced by that engine:** a factor/label pair is counted as a usable
  observation only when both `available_ts` and `label_available_ts` are present; any missing
  availability timestamp flips the run to `REJECTED`
  (`factor_available_ts_missing` / `factor_label_available_ts_missing`). The tools-side harness
  carries both timestamps through from the staged rows.
- **No second PnL truth:** the pure research scorer
  (`src/alpha_system/research/track_a_scorer.py`) imports **none** of
  `backtest`/`management`/`fast_path`/`core.value_store`. Materialized values are loaded
  tools-side (`tools/differentiated_killshot_v1/score_track_a.py`, reusing
  `core.value_store.load_parquet_values` via the DK-P02 staging backbone) and **injected** as
  rows. No PnL value is computed in `research/`.
- **Power:** `N_eff` is computed over the usable IC pairs with a first-order horizon-overlap
  discount (`estimate_n_eff`; `discount = max(1, horizon_seconds/60)`), and the deterministic
  `SE(IC) = 1/sqrt(N_eff-1)`, `MDE(|IC|) = 1.96 * SE(IC)` power statement is attached
  (`build_ic_power_statement`, `statistical_validity_claim: false`).
- **Pooling and budget:** ES/NQ/RTY are pooled into one test per (mechanism, horizon); each
  scored variant is ledgered `VariantLedgerStatus.COMPLETED` within the pre-registered
  family/variant budget; no `BudgetAmendmentRecord`, no per-instrument split, no horizon sweep.
- **Verdict mapping (doc-level only, no runtime enum):** the runtime status maps to the closed
  campaign taxonomy. A `DIAGNOSTICS_COMPLETE` read maps to `REJECT` unless the effective sample
  is underpowered (`N_eff <= 1` or no resolvable MDE), in which case it is honest
  `INCONCLUSIVE`+`UNDERPOWERED`. Effect size never **promotes** to a survivor here; a
  `WATCH`/`CANDIDATE_RESEARCH` survivor is reviewer-gated and surfaced separately.

## Per-Mechanism Diagnostics (Real Data, Pooled ES/NQ/RTY)

All four scored mechanisms returned `DIAGNOSTICS_COMPLETE` with full coverage (`coverage_ratio`
= 1.0), well above the underpowered floor (`N_eff` in the tens-to-hundreds of thousands, so a
usable `MDE(|IC|)` resolved), aggregate Pearson IC indistinguishable from zero, and bucket
diagnostics that are **not** monotonic (direction `mixed`). The binary calendar / proximity flag
is valued at every 1-minute bar (the "rare event" is that the flag is mostly 0, not that the
sample is small), so the point-biserial IC is measured over a large pooled sample.

| Mechanism (study) | Horizon | Primary conditioning factor | Pearson IC | Rank IC | Usable pairs | `N_eff` | `SE(IC)` | `MDE(\|IC\|)` | Buckets (pop/total) | Monotonic | Runtime status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | --- |
| `day_of_week_effect` (`sspec_2ec71d30dadc48e237f9d04c`) | 30m | `session_calendar_roll_day_of_week` | -0.00710 | -0.00496 | 7,294,349 | 243,144 | 0.002028 | 0.003975 | 5/5 | no (mixed) | `DIAGNOSTICS_COMPLETE` |
| `opex_pinning` (`sspec_4936b2ee6614d4b869ec2787`) | 30m | `session_calendar_roll_is_opex_day_flag` | -0.00488 | -0.00513 | 7,294,349 | 243,144 | 0.002028 | 0.003975 | 5/5 | no (mixed) | `DIAGNOSTICS_COMPLETE` |
| `month_end_flow` (`sspec_c8669b6769a07d69ab897e58`) | 30m | `session_calendar_roll_is_month_end_session_flag` | -0.00144 | -0.00496 | 2,357,813 | 78,593 | 0.003567 | 0.006991 | 5/5 | no (mixed) | `DIAGNOSTICS_COMPLETE` |
| `open_close_auction_flow` (`sspec_0c3386a2dd45451970547acd`) | 5m | `session_calendar_roll_minutes_from_rth_open` | 0.00082 | -0.00394 | 2,154,332 | 430,866 | 0.001523 | 0.002986 | 5/5 | no (mixed) | `DIAGNOSTICS_COMPLETE` |
| `open_close_auction_flow` (`sspec_0c3386a2dd45451970547acd`) | 30m | `session_calendar_roll_minutes_from_rth_open` | -0.00083 | -0.01063 | 2,123,235 | 70,774 | 0.003759 | 0.007368 | 5/5 | no (mixed) | `DIAGNOSTICS_COMPLETE` |

Notes on individual reads:

- **`day_of_week_effect` / `opex_pinning`** were staged over all 24 locked partitions
  (no exclusions); both pooled flags share the full-window grid, so usable pairs and `N_eff`
  are identical. Aggregate IC is near zero and buckets are non-monotonic.
- **`month_end_flow`** used 9 partitions and excluded 15 under the sanctioned `all_null_values`
  path: the month-end / quarter-end flags are effectively populated only over the 2024-26
  calendar window, mirroring the DK-P02 coverage caveat. The surviving sample is still large and
  well-powered; the read is near-zero IC, non-monotonic.
- **`open_close_auction_flow`** was scored at both pre-registered horizons (5m, 30m) over all 24
  partitions. The 30m rank IC is -0.0106, whose magnitude slightly exceeds that horizon's
  `MDE(|IC|)` (0.0074); the Pearson IC is still ~0 and the buckets are non-monotonic, so under
  the asymmetric gate this is **not** a survivor — a `DIAGNOSTICS_COMPLETE`, well-powered,
  non-monotonic read maps to `REJECT`, and the scorer does not mint a survivor from an isolated
  rank-IC magnitude (survivor is reviewer-gated, not effect-size-gated).

## Within-Mechanism Near-Duplicate Secondary Exposures (Caveat)

Each event-calendar / open-close mechanism declared a secondary conditioning feature folded into
the single pooled hypothesis (not an independent confirmation), carried as a caveat on the
diagnostics row:

- `opex_pinning`: `session_calendar_roll_is_quad_witch_day_flag` (quad-witch is a subset of OPEX
  days).
- `month_end_flow`: `session_calendar_roll_is_quarter_end_session_flag` (quarter-end is a subset
  of month-end sessions).
- `open_close_auction_flow`: `session_calendar_roll_minutes_to_rth_close` (the close-proximity
  exposure mirrors the open-proximity exposure within the same session geometry).

These secondaries are near-duplicate exposures of the primary, not separate tests; they do not
add independent survivor evidence and are not scored as extra variants.

## Power / N_eff Caveats

- `N_eff` here is computed over the **capped usable IC pairs** (the actual diagnostics
  observation sample), discounted by a **first-order** horizon-overlap factor
  (`discount = horizon_seconds / 60`; 30 for the 30m horizon, 5 for the 5m horizon). It is a
  deterministic reporting input, **not** a statistical-significance result, and is **not**
  session-clustered or autocorrelation-adjusted. Rows are not independent samples.
- The power statement (`SE(IC) = 1/sqrt(N_eff-1)`, `MDE(|IC|) = 1.96 * SE(IC)`) is a detection-
  power readout only and carries `statistical_validity_claim: false`. A `WATCH` /
  `CANDIDATE_RESEARCH` survivor would require a separate reviewer verdict; none was produced
  because none of these reads is a survivor.

## Boundary / Non-Claims

Materialized values, local registries, Parquet payloads, SQLite databases, and scratch reports
remain **local-only** and are not committed by this phase; only the value-free / research-only
diagnostics JSON, this summary, and the verdict refresh are committed. This document creates no
FactorLibrary entry, no `PromotionDecision`, no AlphaBook/Strategy-Reference write, no paper /
live / broker behavior, and no profitability, tradability, or alpha claim.
