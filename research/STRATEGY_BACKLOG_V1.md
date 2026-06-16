# Strategy Backlog V1 — Seed Triage, Lane Routing, and Readiness

Research-only. These are candidate hypotheses (SEEDS), NOT alpha claims. Nothing
here is a survivor, factor-library entry, AlphaBook entry, or a tradability /
profitability statement. Every horizon, threshold, R-geometry, stop, target, and
regime split is a COUNTED, pre-registered variant under family-FDR. Verdicts are
machine records (REJECT → graveyard; DATA_GAP / UNDERPOWERED → requeue;
SIGNAL_PENDING_REVIEWER → reviewer shelf); exploratory readouts decide nothing on
their own.

This backlog is the durable companion to the authored `idea.yaml` files under
`research/idea_to_verdict_loop_v0/`. It records, for all 20 seeds: the dedup verdict
against the existing fleet brain (graveyard / requeue / signal_shelf /
reviewer_adjudications + prior DK/IVL/FUTSUB nulls), the lane the seed must route to,
its substrate readiness, its batch, and whether it was selected for first authoring
or deferred as a FeatureRequest.

## Governing rules used for triage

- **Lane-routing law.** Continuous factor vs continuous label → `main_effect` IC
  lane. Objective context-state ≠ trigger → path outcome → `context_not_equal_trigger`
  setup lane, judged by signed net excursion (MFE + MAE asymmetry / expected-R),
  NEVER single-sided MFE or IC. A categorical / STATE conditioner MUST route to the
  setup lane.
- **Dedup first.** A seed conclusively tested on the SAME recorded slice/thesis is a
  duplicate; only a genuinely new instrument/year/thesis is non-dup. A re-test of a
  feature that was null as a `main_effect` is allowed only as a STATE context in the
  setup lane (distinct unit), with the prior finding noted.
- **No cross-dataset / cross-instrument hacks.** BBO ≠ TBBO. BBO features and BBO
  `cost_adjusted` labels are both on the SAME `dsv_databento_bbo_*` — author BBO ideas
  with the BBO-dataset `lver`, never the OHLCV `lver`. Cross-instrument
  (feature instrument ≠ label instrument) is not supported by the idea grammar
  (`input_resolver` enforces prefix match) → FeatureRequest/requeue, do NOT author.
- **§9 volatility confound.** Compression / range-contraction conditioning shrinks
  excursions symmetrically (vol-magnitude, not direction). Any compression-conditioned
  setup must pre-register the net signed-asymmetry / expected-R gate; symmetric
  MFE/MAE inflation is NOT an edge.

## Substrate facts established during triage (live registry, 2026-06-15)

- OHLCV path labels (`path_mfe` / `path_mae`) are materialized for ES/NQ/RTY ×
  2019–2026 × all horizons on `dsv_databento_ohlcv_bac95e92f1bb1850`.
- OHLCV `cost_adjusted_fwd_ret` is materialized per instrument/year/horizon.
- `volume_activity` features (incl. `base_ohlcv_volume_zscore`, `range_position`) are
  materialized → the volume-effort factor needs ZERO new materialization.
- BBO features (`bbo_tradability_top_book_imbalance`, `bbo_tradability_microprice`,
  `bbo_tradability_spread_zscore`, etc.) AND BBO `cost_adjusted_fwd_ret` are co-materialized
  on `dsv_databento_bbo_*` (e.g. `dsv_databento_bbo_f9e1d70a04d9dae4` for ES 2024).
- **BBO datasets have NO path labels** (only `cost_adjusted_fwd_ret` and
  `spread_adjusted_fwd_ret`). Consequence: a BBO SETUP-lane idea that needs a
  path / net-excursion outcome cannot be authored without a BBO path-label
  FeatureRequest. This directly reshapes `bbo_spread_shock_normalization` (see below).

## Selected for first authoring (9 idea.yaml, all validate clean)

| seed id | lane | authored idea.yaml | slice |
| --- | --- | --- | --- |
| prior_session_low_sweep_reclaim | context_not_equal_trigger | `pa_setup/prior_session_low_sweep_reclaim_es2020_120m_net_excursion.idea.yaml` | ES_2020_120m path |
| opening_range_breakout_acceptance | context_not_equal_trigger | `pa_setup/opening_range_breakout_acceptance_es2020_120m_net_excursion.idea.yaml` | ES_2020_120m path |
| failed_vwap_reclaim_near_session_extreme | context_not_equal_trigger | `pa_setup/failed_vwap_reclaim_near_session_extreme_es2020_120m_net_excursion.idea.yaml` | ES_2020_120m path |
| rth_gap_fade_or_continuation_research_only | context_not_equal_trigger | `pa_setup/rth_gap_fade_or_continuation_es2020_120m_net_excursion.idea.yaml` | ES_2020_120m path |
| range_compression_expansion_continuation | context_not_equal_trigger | `pa_setup/range_compression_expansion_continuation_es2020_120m_net_excursion.idea.yaml` | ES_2020_120m path |
| volume_effort_no_result_exhaustion | main_effect | `seeds/main_effect_volume_zscore_cost_adj_fwd_ret_es2020_60m.idea.yaml` | ES_2020_60m cost_adj |
| bbo_top_book_imbalance | main_effect | `seeds/main_effect_bbo_top_book_imbalance_cost_adj_fwd_ret_es2024_15m.idea.yaml` | ES_2024_15m BBO cost_adj |
| bbo_microprice_dislocation | main_effect | `seeds/main_effect_bbo_microprice_cost_adj_fwd_ret_es2024_15m.idea.yaml` | ES_2024_15m BBO cost_adj |
| bbo_spread_shock_normalization | main_effect (cost-aware) | `seeds/main_effect_bbo_spread_zscore_cost_adj_fwd_ret_es2024_30m.idea.yaml` | ES_2024_30m BBO cost_adj |

Authoring discipline: each authored file COPIES the structure of a known-good,
validating template in the same lane (setup lane from the regime conditional-setup
family; main_effect lane from the IVL powered-probe seed) and changes ONLY the
mechanism / threshold / factor-and-label-ref fields. All factor/label pack refs
(`fver` / `lver` / `relative_path` / `feature_request_id` / `label_spec_id`) are real,
registry-verified rows, using the SAME `dataset_version` + `fver`/`lver` pattern the
template uses. BBO ideas use the BBO-dataset `cost_adjusted` `lver`, never the OHLCV
`lver` (this corrects the prior wrong-lver DATA_GAP authoring bug).

> First slices are pre-registered exploratory units, not survivors. ES_2020_120m /
> ES_2020_60m / ES_2024 are the powered first slices; cross-year (2022–2024) and
> cross-instrument (NQ/RTY) extensions are SEPARATE counted variants under family-FDR,
> never a sweep-then-pick.

## Full 20-seed triage table

Status legend: KEEP = no recorded verdict, novel-enough to author/queue;
DEDUP = conclusively recorded on the same slice/thesis, do NOT re-run;
REQUEUE_DUP = already an existing requeue row (evidence-accrual, not a fresh author);
GRAMMAR_BLOCKED = unsupported by the idea grammar → FeatureRequest.

| # | seed id | batch | lane | dedup status | readiness | selected first? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | opening_selloff_vwap_reclaim | A | setup | DEDUP (graveyard REJECT, ES_2020_120m net_excursion) | READY (non-2020 only) | no |
| 2 | vwap_rejection_trend_continuation | A | setup | KEEP (vwap-slope trend pullback-reject not recorded) | READY | no (Batch-A queue) |
| 3 | opening_drive_failure | A | setup | REQUEUE_DUP (requeue INCONCLUSIVE/DATA_QUALITY, ES_2020_120m) | READY (non-2020) | no |
| 4 | opening_range_breakout_acceptance | A | setup | KEEP (acceptance/continuation thesis untested) | READY | **YES** |
| 5 | prior_session_high_sweep_failure | A | setup | DEDUP (signal_shelf → reviewer REWORK, ES_2020_120m) | READY (OOS+FDR rework only) | no |
| 6 | prior_session_low_sweep_reclaim | A | setup | KEEP (LONG-side mirror untested) | READY | **YES** |
| 7 | session_high_low_sweep_with_vwap_context | A | setup | DEDUP (graveyard REJECT, ES_2020_120m net_excursion) | READY (non-2020 only) | no |
| 8 | range_compression_failed_breakout | A | setup | KEEP w/ high dup-risk (§9 vol-confound; range_contraction main_effect REJECT) | READY (net-asymmetry gate) | no |
| 9 | failed_vwap_reclaim_near_session_extreme | A | setup | KEEP (failed-reclaim continuation untested) | READY | **YES** |
| 10 | range_compression_expansion_continuation | B | setup | KEEP w/ §9 caveat (separate vol-magnitude from direction) | READY (net-asymmetry gate) | **YES** |
| 11 | vwap_slope_price_location_pullback | B | main_effect | REQUEUE_DUP (distance_to_vwap IC requeue, ES_2020_60m, 2020 artifact) | NEEDS_FEATUREREQUEST (vwap_slope not a column) | no |
| 12 | volume_effort_no_result_exhaustion | B | main_effect | KEEP (effort_vs_result untested) | READY | **YES** |
| 13 | bbo_top_book_imbalance | C | main_effect | KEEP (no recorded verdict; prior DATA_GAP was wrong-lver bug, not a null) | READY (BBO-dataset lver) | **YES** |
| 14 | bbo_microprice_dislocation | C | main_effect | KEEP (named-but-never-probed) | READY (BBO-dataset lver) | **YES** |
| 15 | bbo_spread_shock_normalization | C | main_effect (cost-aware) | KEEP (named-but-never-probed) | READY as main_effect; SETUP framing → FeatureRequest | **YES** (main_effect form) |
| 16 | bbo_liquidity_filter_interaction | C | interaction | KEEP w/ discipline (counted variant on a base setup; watch n_eff collapse) | READY but downstream of a base setup result | no (interaction, after base) |
| 17 | es_nq_leader_lagger_catchup | D | cross_instrument | KEEP (no verdict) | GRAMMAR_BLOCKED → FeatureRequest | no — FeatureRequest |
| 18 | es_nq_confirmation_filter_vwap_reclaim | D | cross_instrument | KEEP (no verdict; base ES vwap-reclaim is graveyard REJECT) | GRAMMAR_BLOCKED → FeatureRequest | no — FeatureRequest |
| 19 | rty_relative_weakness_filter | D | cross_instrument | KEEP (no verdict) | GRAMMAR_BLOCKED → FeatureRequest | no — FeatureRequest |
| 20 | rth_gap_fade_or_continuation_research_only | B | setup | KEEP (gap fade/continuation untested) | READY | **YES** |

## Deferred work (not authored as idea.yaml)

### FeatureRequest / requeue — grammar-blocked cross-instrument (Batch D)

Seeds 17, 18, 19 require a cross-instrument feature (feature instrument ≠ label
instrument). The idea grammar's `input_resolver` enforces an instrument+year prefix
match, and existing `cross_market_alignment` features are SAME-BAR contemporaneous,
not predictive lead-lag (rolling beta/corr are within-window, not
ES_t → NQ_{t+h}). These are recorded here as FeatureRequests — a predictive lead-lag /
dispersion feature plus resolver work must land BEFORE any idea.yaml can be authored.
Do NOT hack a cross-dataset slice.

### FeatureRequest — BBO path label (for the spread-shock SETUP framing)

`bbo_spread_shock_normalization` is preferentially a STATE conditioner (spread high
then normalizes within M bars), which the lane-routing law routes to the SETUP lane
with a path / net-excursion outcome. BBO datasets have NO path labels materialized
(only `cost_adjusted_fwd_ret` / `spread_adjusted_fwd_ret`). Rather than hack the seed
onto a cross-dataset OHLCV path label, the SETUP framing is recorded as a
BBO-path-label FeatureRequest. The seed is authored in this backlog in its SUPPORTED,
cost-aware `main_effect` form (spread z-score vs BBO `cost_adjusted_fwd_ret`), where
wide-spread untradability is absorbed by the cost-adjusted outcome.

### FeatureRequest — vwap_slope column (Batch B)

`vwap_slope_price_location_pullback` needs a `vwap_slope` feature; `vwap_session_auction`
materializes `base_ohlcv_vwap` / `anchored_vwap` / `distance_to_vwap` but no slope column.
Its core `distance_to_vwap` main_effect IC is already a requeue row (ES_2020_60m, the
2020-COVID artifact) — do NOT re-run that slice. File a `vwap_slope` FeatureRequest;
requeue-link and avoid 2020. (`vwap_rejection_trend_continuation`, seed 2, can read
vwap-slope as a STATE context once the column exists, and is otherwise a Batch-A setup
queue item.)

### Batch-A / B queued setups (not first-authored, dedup-constrained)

- Seed 1 / 3 / 5 / 7 are DEDUP or REQUEUE_DUP on ES_2020_120m: re-authoring is only
  legitimate on a genuinely new (non-2020) instrument/year slice, judged by net
  asymmetry, and (for seed 5) under the reviewer's required OOS + ≥1000-surrogate +
  family-FDR rework. They queue as counted-variant OOS extensions, not fresh authors.
- Seed 8 (`range_compression_failed_breakout`) carries the §9 vol-confound directly;
  authorable only as a signed-expected-R / net-asymmetry diagnostic, pre-registered,
  family-FDR — queued behind seed 10 to avoid duplicating the compression family in one batch.
- Seed 16 (`bbo_liquidity_filter_interaction`) is an INTERACTION variant on top of an
  existing base setup; it is downstream of an authored base setup result and is a
  COUNTED variant (n_eff drops; never promote on one improved slice).

## Family-FDR grouping (pre-registered)

- `pa_setup_prior_extreme_sweep*` — prior-high sweep-failure (shelved/REWORK), prior-low
  sweep-reclaim (authored). Dedup-linked; share the rework conditions.
- `pa_setup_opening_range_acceptance_net` / opening-drive-failure requeue — acceptance vs
  failure counted pair.
- `pa_setup_failed_vwap_reclaim_extreme_net` / `pa_setup_rth_gap_*` — VWAP / gap setups.
- `pa_setup_range_compression_*` — compression-conditioned setups (10 authored, 8 queued)
  under the shared §9 net-asymmetry gate.
- `tier1_main_effect_continuous_ic` — volume-effort and other OHLCV main_effect probes.
- `tier1_main_effect_bbo_microstructure_ic` — top-book imbalance, microprice, spread
  z-score; each horizon and each instrument is a counted variant; overlap-aware n_eff
  (horizon_bars / cadence discount) applies.
