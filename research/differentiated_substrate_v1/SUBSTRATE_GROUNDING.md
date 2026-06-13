# DIFFERENTIATED_SUBSTRATE_V1 — Existing-Substrate Grounding (read-only)

Status: VALUE-FREE research-prep design note. No code, no data, no diagnostics,
no IC/return values, no alpha/tradability/profitability claims. Diagnostics and
gates decide promotion, never priors. This note records ONLY what substrate
already exists (read-only inspection) so that event-calendar mechanism cards can
state honestly which inputs are reusable versus which would need a new
`FeatureRequest` / `LabelSpec`.

## Why this direction

The FUTSUB first kill-shot rejected all 6 legacy price-action / BBO mechanisms
(regime, liquidity_pa x2, bbo_tradability, vwap_session x2) at near-zero IC. The
next research direction is DIFFERENTIATED substrate: mechanisms intended to be
orthogonal to crowded main-effect price-action priors. The most orthogonal first
target proposed here is EVENT-CALENDAR-CONDITIONED INTRADAY behavior (conditioning
on scheduled macro/market events). This note does not assert that such an edge
exists; it only scopes what would be required to test it under existing rigor.

## Repo-exact inventory (what exists today)

### Feature families that exist (`src/alpha_system/features/contracts.py`, `FeatureFamily`)

The complete enum has exactly 5 members:

- `BASE_OHLCV = "base_ohlcv"`
- `BBO_TRADABILITY = "bbo_tradability"`  (do NOT touch this namespace — out of scope)
- `SESSION_CALENDAR_ROLL = "session_calendar_roll"`
- `CROSS_MARKET = "cross_market"`
- `LIQUIDITY_STRUCTURE = "liquidity_structure"`

There is NO `event_calendar` / macro-event feature family. Any macro-event
conditioning feature would require either (a) a new `FeatureFamily` member plus a
new family module, or (b) reuse of `SESSION_CALENDAR_ROLL` extended with new
calendar inputs — both gated by a new `FeatureRequest` (`freq_` id) through the
FLF-P05 request gate.

### Session / Calendar / Roll features that EXIST and are reusable

File: `src/alpha_system/features/families/session/family.py`
(`SessionFeatureName` enum — these are the only members):

- `session_id`            (segment id via `session_segment_id`)
- `minutes_from_rth_open`
- `minutes_to_rth_close`
- `rth_segment_flag`
- `eth_segment_flag`
- `day_of_week`           (calendar position, `bar_start_ts.weekday()`)
- `bars_to_roll`          (offline-only future-window countdown; `live=False`)
- `minutes_to_roll`       (offline-only future-window countdown; `live=False`)
- `minutes_to_expiration` (uses optional `SessionCalendarRollMetadata.expiration_ts_by_contract_id`)
- `halt_status_flag`      (uses optional `SessionCalendarRollMetadata.status_by_*`)

Key build/compute symbols: `build_session_feature_definition(...)`,
`build_session_feature_definitions(...)`, `compute_session_feature(...)`,
`compute_session_features(...)`, `supported_session_features()`,
`SessionFeatureDefinition`, `SessionFeatureSpec`, `SessionCalendarRollMetadata`,
`row_key(...)`. Admission is gated ONLY by
`require_feature_request_implementation_allowed(...)`
(`src/alpha_system/features/request_gate.py`) against an approved
`FeatureRequest` (`src/alpha_system/governance/feature_request.py`).

Point-in-time, day-of-week, RTH/ETH segmentation, and expiration-proximity are
reusable building blocks. Optional metadata
(`expiration_ts_by_contract_id`, `status_by_row_key`,
`status_by_available_ts`, and their `*_available_ts_*` provenance maps) is the
existing seam for injecting point-in-time-known calendar metadata, with a strict
guard (`_require_metadata_known_as_of`) that metadata `available_ts` must be
`<= row.available_ts` and absent metadata is flagged, never fabricated.

### What the session family does NOT have (would need a new FeatureRequest)

There is NO concept of a SCHEDULED MACRO/MARKET EVENT (FOMC, CPI, NFP, OPEX,
quad-witching, month-end). Specifically absent:

- a known-ahead event-schedule calendar (event type + scheduled release time);
- features such as `minutes_to_scheduled_event`, `in_event_window_flag`,
  `is_opex_day`, `is_quad_witch_day`, `is_month_end_session`,
  `minutes_since_event_release`;
- any surprise / actual-vs-consensus magnitude input (post-event-knowable only).

These require a new `FeatureRequest` (and likely a new event-schedule metadata
surface analogous to `SessionCalendarRollMetadata`, carrying point-in-time
provenance: scheduled times are known-ahead; release-derived values are NOT).

### Label families that EXIST (`src/alpha_system/labels/version.py`, `LabelFamily`)

`fixed_horizon`, `midprice_forward`, `cost_adjusted`, `path`, `event`.

IMPORTANT naming caveat: `LabelFamily.EVENT` and
`src/alpha_system/labels/families/event/family.py` are NOT a macro-calendar
family. They are STRATEGY-AGNOSTIC PRICE-PATH OUTCOME labels. The
`EventLabelName` enum members are:

- `breakout_success`
- `return_to_vwap`
- `sweep_outcome`
- `liquidity_quality_future`

Build/compute symbols: `build_event_label_definition(...)`,
`build_event_label_definitions(...)`, `compute_event_label(...)`,
`compute_event_labels(...)`, `supported_event_labels()`, `EventLabelDefinition`,
`EventLabelName`, `EventDirection`, `SweepSide`. Future windows are labels-only
(`WindowCausality.FUTURE`, `offline_only=True`,
`future_data_legal_only_for_labels`).

Reusable outcome labels for event-conditioned studies: the existing
`fixed_horizon` / `midprice_forward` forward-return labels and the strategy-
agnostic `event` outcome labels (`breakout_success`, `return_to_vwap`,
`sweep_outcome`). The conditioning is supplied by FEATURES; the OUTCOME labels
already exist. No new `LabelSpec` is required purely to measure forward behavior
around an event — only to add an event-window-restricted label variant if a
study wants outcomes anchored strictly inside an event window.

### Economic / macro event-calendar data source — DOES NOT EXIST

A repo search for `fomc`, `cpi`, `nfp`, `opex`, `witching`, `event_calendar`,
`economic_calendar`, `econ_calendar`, `macro_event` across
`src/`, `configs/`, and `governance/` returned ZERO hits. There is no economic-
calendar dataset, config, ingestion path, or provider boundary today. Scheduled
macro-event timestamps would have to be sourced. This is the primary
`data_dependency` and is marked DEFERRED-PENDING-USER-APPROVAL on every card
where it applies. Market-structure events that are DERIVABLE from the existing
exchange calendar / contract metadata (OPEX dates, quad-witching dates,
month-end sessions, expiration) are a smaller dependency than externally-sourced
macro releases (FOMC/CPI/NFP) and are noted separately on each card.

## Governance / multiple-testing machinery that EXISTS (for the FDR budget)

- `src/alpha_system/governance/variant_ledger.py`: `VariantLedger`,
  `VariantLedgerRecord`, `evaluate_family_budget(...)`, `FamilyBudgetCheck`,
  `validate_variant_and_family_budget(...)`, `BudgetAmendmentRecord` +
  `create_budget_amendment_record(...)` (pre-declared, provenance-carrying,
  strictly-increasing budget amendments; an amendment must predate the earliest
  recorded variant attempt — `_find_covering_amendment`). Family rollup keys on
  `(study_spec_id, variant_id)` via `_family_exposure_key`.
- `src/alpha_system/governance/study_spec.py`: `StudySpec.variant_budget` (int,
  required) and `StudySpec.family_budget` (int, optional). `evaluate_variant_budget`,
  `check_variant_budget`, `StudyBudgetCheck`, `StudyBudgetStatus`.
- `src/alpha_system/governance/surrogate_run.py`: `SurrogateStudyRun`,
  `run_surrogate_study(...)`, `calibrate_surrogate_fdr(...)`,
  `SurrogateCalibrationReport`, perturbation types (`label_shuffle`,
  `trade_date_block_shuffle`, `trade_date_block_bootstrap`, `random_target`),
  zero-pass threshold semantics (`ZERO_PASS_MET`, `LEAKAGE_BLOCKED`),
  false-pass bound "zero passes in K bounds false-pass rate at about 3/K at 95%"
  (`SURROGATE_FALSE_PASS_BOUND_STATEMENT`). `DEFAULT_SURROGATE_FAMILY_ID =
  "family-rigor-p05-surrogate-fdr"`.
- `src/alpha_system/governance/trial_ledger.py`: `TrialLedgerRecord`,
  `summarize_trial_ledger_variants(...)`, `surrogate_flag` (surrogate trials are
  excluded from production variant/family counts).
- `src/alpha_system/governance/pooled_hypothesis.py` exists for pooled-hypothesis
  accounting (Track-B pooled minimum per the Compass).

Conclusion: the multiple-testing budget machinery to bound this work ALREADY
EXISTS. No new ledger or FDR mechanism should be built (REUSE-MAP rule). The FDR
budget note (`FDR_BUDGET.md`) pre-registers counts against these existing
objects.
