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

### FeatureRequest — REGISTERED BBO-dataset `cost_adjusted_fwd_ret` label (all 3 BBO ideas, 2026-06-15)

During the smoke-probe re-pin pass (below), all 3 authored BBO `main_effect` ideas
(`bbo_top_book_imbalance`, `bbo_microprice_dislocation`, `bbo_spread_shock_normalization`)
failed-closed at the gate with `label_pack_deprecated` (INPUTS_BLOCKED) and could NOT be
re-pinned to a REGISTERED BBO-dataset label. The live registry
(`registry/labels.sqlite`) shows that **every** label bound to the ES 2024 BBO
DatasetVersion `dsv_databento_bbo_f9e1d70a04d9dae4` is `lifecycle_state=DEPRECATED` —
all 81 `cost_adjusted_fwd_ret` rows and all 81 `spread_adjusted_fwd_ret` rows, across
every horizon (the same holds for NQ/RTY 2024). There are **zero REGISTERED labels on any
BBO DatasetVersion**.

The registry's named `replacement_label_version_id` for the deprecated BBO
`cost_adjusted_fwd_ret` lvers points to an **OHLCV** DatasetVersion
(`dsv_databento_ohlcv_05404069799decb0`, e.g. `lver_7edc9438…` for ES_2024_15m,
`lver_de9c7c2c…` for ES_2024_30m). The deprecation reason is explicit: *"stale
cost_adjusted-family registration from earlier P19 runs, bound to superseded BBO
DatasetVersion; superseded by current OHLCV-bound full-window registration"* (W1
disposition, FUTSUB-P22 review). Adopting that replacement would re-introduce the
cross-dataset wrong-lver bug — a BBO feature paired with an OHLCV label — which the
no-cross-dataset rule (above) and `data-inventory-canonical` forbid (BBO feature + BBO
label MUST be on the SAME `dsv_databento_bbo_*`).

Therefore the 3 BBO ideas are recorded here as a **registry-lifecycle FeatureRequest**,
not re-pinned: a REGISTERED `cost_adjusted_fwd_ret` (and/or `spread_adjusted_fwd_ret`)
label must be (re)materialized and registered on a current BBO DatasetVersion before any
BBO `main_effect` idea can resolve. This corrects the backlog's earlier "READY
(BBO-dataset lver)" / "co-materialized" readiness note for the BBO seeds, which assumed a
REGISTERED BBO-dataset label that the live registry does not currently hold. The BBO
*features* themselves are fine — `bbo_tradability_microprice` and
`bbo_tradability_top_book_imbalance` are REGISTERED; `bbo_tradability_spread_zscore` is
DEPRECATED but has a REGISTERED same-dataset replacement (`fver_85d552bd…`). The blocker
is strictly the label side.

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

## Smoke-probe re-pin pass (2026-06-15)

A smoke probe of the 9 authored ideas found 8 in `DATA_GAP` from one systematic cause
(see "Deprecated-pack-pin authoring trap" below): the authored pins named feature/label
pack versions the registry has since marked `lifecycle_state=DEPRECATED`. The underlying
materialized parquet is present; only the pinned VERSION is superseded. Re-pin disposition:

| idea | deprecated pin(s) | registered replacement | re-pin? | smoke result |
| --- | --- | --- | --- | --- |
| `volume_effort` (`main_effect_volume_zscore…es2020_60m`) | none (already REGISTERED) | n/a | n/a (already resolved) | RESOLVED — probe ran, `REJECT / WELL_POWERED_NULL` (no IC above floor) |
| `prior_session_low_sweep_reclaim` | `liquidity_structure_sweep_low_flag` fver + `…close_location_value` fver (2 features) | `fver_7393…` + `fver_6eb1…` (same feature_id+dataset+partition) | YES | RESOLVED — testability gate now PASS (all 5 checks); substrate resolves |
| `opening_range_breakout_acceptance` | `liquidity_structure_failed_high_breakout_flag` fver | `fver_08e6…` | YES | RESOLVED — testability gate now PASS |
| `failed_vwap_reclaim_near_session_extreme` | `liquidity_structure_prior_high_distance` fver | `fver_6b36…` | YES | RESOLVED — testability gate now PASS |
| `range_compression_expansion_continuation` | `liquidity_structure_failed_low_breakout_flag` fver | `fver_69fd…` | YES | RESOLVED — testability gate now PASS |
| `rth_gap_fade_or_continuation` | `base_ohlcv_overnight_range` fver | `fver_a9d0…` | YES | RESOLVED — testability gate now PASS |
| `bbo_top_book_imbalance` | `cost_adjusted_fwd_ret` BBO lver | NONE registered on BBO dataset | NO → FeatureRequest | STILL DATA_GAP (registry-lifecycle gap; see BBO FeatureRequest above) |
| `bbo_microprice_dislocation` | `cost_adjusted_fwd_ret` BBO lver | NONE registered on BBO dataset | NO → FeatureRequest | STILL DATA_GAP (registry-lifecycle gap) |
| `bbo_spread_shock_normalization` | `bbo_tradability_spread_zscore` fver (has REGISTERED repl `fver_85d5…`) AND `cost_adjusted_fwd_ret` BBO lver (no BBO repl) | feature replaceable; LABEL not | NO → FeatureRequest | STILL DATA_GAP (label-side registry-lifecycle gap) |

Re-pin discipline used: each deprecated `fver` was matched to the single
`lifecycle_state='REGISTERED'` row with the SAME `feature_id` + `dataset_version_id` +
`partition_id` (the deprecated and registered rows resolve to the same
`materialization_output_path`). Both the `fver` pins (`feature_pack_refs[]`,
`features[].factor_version`, `features[].pack_ref`) AND the paired
`feature_request_id` pins (`feature_request_ids[]`, `features[].feature_request_id`) were
re-pinned, because `runtime/input_resolver.py` (≈L509) rejects a pack whose resolved
`feature_request_id` is not in the idea's `expected_feature_request_ids`
(`feature_pack_not_governed_by_study_input_pack`). The pa_setup labels (`path_mfe` /
`path_mae`) were already REGISTERED and were left unchanged.

"RESOLVED" above means the deprecated-pack `DATA_GAP` is cleared and the substrate now
resolves: `alpha idea testability` returns `overall_status=PASS` on all five gate checks
(including `features_materialized`), so a probe shot would now be spent. The full
`alpha idea run` net_excursion probe (1000 surrogates) executes past the gate and is
compute-heavy; its downstream net-excursion / surrogate-FDR verdict is a separate
exploratory readout and decides nothing on its own (it remains family-FDR /
reviewer-gated). The point of this pass is substrate resolution, not a verdict.

## Deprecated-pack-pin authoring trap (systematic, candidate generic fix)

**Trap.** An `idea.yaml` template pins specific `fver` / `lver` (feature/label pack
versions). The registry can later DEPRECATE those exact versions (e.g. a session-reset
truth repoint or a cost_adjusted-family rebind to a new DatasetVersion), registering a
fresh REGISTERED replacement of the SAME logical `feature_id` / `label_spec_id` on the
SAME materialized data. The authored pin is now stale. At runtime the gate fail-closes:
`runtime/input_resolver.py::_require_registered_pack_lifecycle` compares the resolved
registry record's `lifecycle_state` against `REGISTERED` and, on `DEPRECATED`, raises
`feature_pack_deprecated` / `label_pack_deprecated` at `INPUTS_BLOCKED`, surfacing the
registry's `replacement_feature_version_id` / `replacement_label_version_id` in the
reason. The data is materialized; only the pin is superseded — but the author only learns
this at run time as a `DATA_GAP`, not at authoring/validate time.

**Why it bites.** `alpha idea validate` (`cli/idea.py::run_idea_validate` →
`build_idea_validation_bundle`) is pure schema/governance validation — it never touches
the registry resolver or `lifecycle_state`. The lifecycle check only fires later, in the
testability gate / runtime resolver (`FeatureLabelPackResolver`). So a clean
`validate` plus a clean content-hash gives false confidence; the deprecation only shows
up after a probe run is attempted.

**PROPOSED GENERIC FIX (candidate — NOT implemented in this pass).** Have
`alpha idea validate` (or a dedicated `alpha idea validate --check-registry` mode) detect
a pinned pack whose registry `lifecycle_state=DEPRECATED` and FAIL/WARN LOUD at
validate-time, naming the registry's `replacement_feature_version_id` /
`replacement_label_version_id` (when present) plus the same-`feature_id`/`label_spec_id`
REGISTERED candidate (when the named replacement field is empty, as it is for the
session-reset feature deprecations). This lets authors re-pin DELIBERATELY — preserving
pre-registration and content-hash integrity by making the version bump an explicit,
reviewed authoring decision — instead of discovering a stale pin as a run-time
`DATA_GAP`. Caveat from this pass: a named `replacement_*_version_id` can cross datasets
(the BBO `cost_adjusted_fwd_ret` deprecations name an OHLCV-dataset replacement), so the
validate-time check must SURFACE the replacement, not silently adopt it — adopting a
cross-dataset replacement would re-introduce the wrong-`lver` bug. Cite: registry field
`lifecycle_state` on `feature_registry_records` / `label_registry_records`, the
`replacement_*_version_id` columns on `*_deprecation_records`, and the
`_require_registered_pack_lifecycle` gate.
