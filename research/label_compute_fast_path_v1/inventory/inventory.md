# LCFP-P01 Label Engine Inventory

This inventory is value-free. It records code paths, symbols, contracts,
configs, counts, and design findings only. It contains no per-row label values,
market prices, canonical rows, Parquet payloads, SQLite rows, provider payloads,
or registry dumps.

## Reference Label Engine

Primary dispatch lives in `src/alpha_system/labels/engine.py`.

- `SupportedLabelDefinition` is the bounded reference-engine union:
  `FixedHorizonLabelDefinition`, `CostAdjustedLabelDefinition`,
  `PathLabelDefinition`, and `EventLabelDefinition`.
- `build_label_materialization_plan(...)` builds deterministic local-only plans
  for accepted DatasetVersion partitions. It validates label-only future-data
  policy, exact DatasetVersion binding, live-feature exclusion, local data root
  placement, and deterministic `label_version_id` / `label_spec_id` ordering.
- `materialize_labels(...)` builds `OHLCVInputView` / `BBOInputView` /
  `CanonicalInputViews`, dispatches through `_compute_definition_records(...)`,
  validates `LabelValueRecord` timestamps, then writes values if and only if a
  non-dry-run materialization plan is executed. LCFP-P01 did not use this write
  path for timing.
- The per-family dispatch is:
  `FixedHorizonLabelDefinition -> compute_fixed_horizon_label(...)`,
  `CostAdjustedLabelDefinition -> compute_cost_adjusted_label(...)`,
  `PathLabelDefinition -> compute_path_label(...)`, and
  `EventLabelDefinition -> compute_event_label(...)`.

## Fixed Horizon Family

Source: `src/alpha_system/labels/families/fixed_horizon/family.py`.

Symbols:

- `FixedHorizonLabelName`: trade-price `fwd_ret_1m`, `fwd_ret_3m`,
  `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_15m`, `fwd_ret_30m`,
  `fwd_ret_60m`, `fwd_ret_120m`, `fwd_ret_240m`, symbolic close-out
  `session_close`, `maintenance_flat`, and midprice `mid_fwd_ret_1m`,
  `mid_fwd_ret_3m`, `mid_fwd_ret_5m`, `mid_fwd_ret_10m`,
  `mid_fwd_ret_30m`.
- `build_fixed_horizon_label_definition(...)` binds each label to a governed
  `LabelSpec` and derives the content-addressed `LabelVersion`.
- `compute_fixed_horizon_label(...)` chooses OHLCV trade-price, BBO midprice,
  or close-out semantics from the definition.

Inputs and semantics:

- Trade-price fixed horizons consume `OHLCVInputView` fields listed by
  `_label_inputs(...)`: `series_id`, `contract_id`, `event_ts`, `bar_end_ts`,
  `available_ts`, `close`, `volume`, and `quality_flags`.
- Midprice fixed horizons consume `BBOInputView` fields including `bid`, `ask`,
  `mid`, and BBO quality flags.
- Fixed-horizon terminals use exact `event_ts + horizon_minutes` lookup through
  `_index_by_series_contract_event_ts(...)` keyed by
  `series_id + contract_id + event_ts`; missing terminals are omitted.
- `session_close` uses `_close_out_terminal_by_scope(...)` and selects the last
  same-contract RTH bar at or before 15:00 America/Chicago for the CME trade
  date. `maintenance_flat` selects the same-contract last bar at or before
  16:00 America/Chicago for the CME trade date. Rows at or after the selected
  close-out terminal are omitted.
- `label_available_ts` is derived in `_label_available_ts(...)` as the max of
  the terminal row availability and the governed availability floor.
- Gap/quality flags include source or terminal trade gaps, BBO gaps, missing or
  quarantined BBO, invariant violations, non-finite returns, and roll-splice
  flags when a retaining roll policy is used. With the default `drop` policy,
  dropped roll or maintenance crossings do not emit records.

Per-row hot loops:

- `_compute_trade_price_forward_returns(...)`: iterates validated OHLCV source
  rows, exact terminal lookup, `_guarded_forward_terminal(...)`, return/flag
  calculation, then `LabelValueRecord`.
- `_compute_trade_price_close_out_returns(...)`: builds close-out terminal
  scopes, iterates source rows, applies the same guard path, then emits records.
- `_compute_midprice_forward_returns(...)`: iterates validated BBO rows, exact
  terminal lookup, guard path, BBO return/flag calculation, then records.

Overlap metadata:

- `OVERLAP_METADATA_VERSION = "horizon_overlap_metadata_v1"`.
- `HorizonOverlapMetadata` records raw row count, horizon minutes, sampling
  interval, effective sample count, overlap fraction, and
  `rows_are_independent=False`.
- `compute_horizon_overlap_metadata(...)` uses
  `floor(raw_row_count / horizon_bars)` with a floor of 1 for non-empty input,
  capped at raw rows.
- Extended fixed horizons include `horizon_overlap_metadata` in contract
  metadata. Close-out labels record a distinct effective-sample rule based on
  distinct close-out terminal events.

## Cost-Adjusted Family

Source: `src/alpha_system/labels/families/cost_adjusted/family.py`.

Symbols:

- `CostAdjustedLabelName`: `cost_adjusted_fwd_ret`,
  `spread_adjusted_fwd_ret`.
- `build_cost_adjusted_label_definition(...)` adapts governed `LabelSpec`
  `cost_model` fields into `CostAdjustedForwardReturnSpec` or
  `SpreadAdjustedForwardReturnSpec`.
- `compute_cost_adjusted_label(...)` and `compute_cost_adjusted_labels(...)`
  are the reference entrypoints.

Inputs and semantics:

- Inputs are `canonical_bbo` plus optional dense-grid/trade rows for no-trade
  anchor detection. `_INPUT_FIELDS` includes BBO prices/sizes, availability,
  event time, `series_id`, `quality_flags`, and dense-grid trade metadata.
- The terminal is an exact BBO row at `event_ts + LabelSpec.horizon`, keyed by
  `series_id + event_ts`.
- `_CostModel.from_cost_adjustment(...)` supports `spread_plus_bps` for
  `cost_adjusted_fwd_ret` and `spread_adjusted` / `spread_plus_bps` for
  `spread_adjusted_fwd_ret`.
- `label_available_ts` is the max of `horizon_end_ts`, the governed
  availability floor, and the terminal BBO availability when present.
- Missing terminal BBO, invalid entry/terminal quote, zero/negative mid, and
  synthetic no-trade anchors emit `None` with explicit quality flags.

Per-row hot loop:

- `compute_cost_adjusted_label(...)` validates/sorts BBO rows, builds BBO and
  trade indexes, then iterates every BBO row through `_label_point(...)` and
  `_label_value_record(...)`.

Inventory finding for P02:

- The cost-adjusted family records guard requirements in contracts/config, but
  this module does not call `labels.roll_guard.evaluate_roll_guard(...)` or the
  fixed-horizon maintenance guard directly. P02 needs a shared guard contract so
  the later producer path does not inherit a family-specific guard gap.

## Path Family

Source: `src/alpha_system/labels/families/path/family.py`.

Symbols:

- `PathLabelName`: `mfe`, `mae`, `target_before_stop`, `triple_barrier`.
- `PathDirection`: `long`, `short`.
- `SameBarBarrierPolicy`: `ambiguous`, `target_first`, `stop_first`.
- `PathBarrier`: `target`, `stop`, `horizon`, `ambiguous`.
- Entry points: `build_path_label_definition(...)`,
  `build_path_label_definitions(...)`, `compute_path_label(...)`,
  `compute_path_labels(...)`.

Inputs and semantics:

- Inputs are `canonical_ohlcv`; `_label_input_fields(...)` includes
  `event_ts`, `available_ts`, selected price field, `high`, `low`, and
  `quality_flags`.
- `_real_trade_rows(...)` filters rows through `is_real_trade_bar(...)` before
  any path or barrier calculation.
- `mfe` and `mae` require a complete forward path of `horizon_steps`; incomplete
  trailing paths are omitted.
- `target_before_stop` and `triple_barrier` use `_first_barrier(...)`.
  Same-bar target/stop crossings resolve according to `SameBarBarrierPolicy`;
  the default ambiguous policy emits `None` for target-before-stop and
  triple-barrier when both barriers are crossed in the same bar.
- `label_available_ts` is the max of the resolution row `event_ts`, resolution
  row `available_ts`, and the governed availability floor.

Per-row hot loop:

- `compute_path_label(...)` loops over each real trade entry row, slices future
  rows, resolves MFE/MAE or first barrier through `_resolve_path_outcome(...)`,
  then builds `LabelValueRecord`.

Inventory finding for P02:

- The path family does not call `labels.roll_guard.evaluate_roll_guard(...)` or
  a maintenance-crossing guard directly. FUTSUB-P20 requires those guards, so
  P02 should define the shared terminal/guard contract before the producer
  implementation.

## Event Family

Source: `src/alpha_system/labels/families/event/family.py`.

Symbols:

- `EventLabelName`: `breakout_success`, `return_to_vwap`, `sweep_outcome`,
  `liquidity_quality_future`.
- `EventDirection`: `up`, `down`; `SweepSide`: `buy_side`, `sell_side`.
- Entry points: `build_event_label_definition(...)`,
  `build_event_label_definitions(...)`, `compute_event_label(...)`,
  `compute_event_labels(...)`.

Inputs and semantics:

- Trade event labels consume OHLCV/dense-grid event rows and future real-trade
  rows only. `liquidity_quality_future` also consumes exact future BBO rows.
- `breakout_success`, `return_to_vwap`, and `sweep_outcome` resolve over future
  trade rows; incomplete future paths are omitted.
- `liquidity_quality_future` scans exact BBO rows across the future horizon and
  flags missing/quarantined/invariant-violating BBO instead of filling.
- `label_available_ts` is the max of horizon/resolution time, relevant
  availability candidates, and the governed availability floor.

FUTSUB P16-P20 does not require event labels except that the P18 config names
`event` as an underlying family for session/maintenance context. The actual
committed close-out labels are implemented through the fixed-horizon family.

## Existing `labels/fast` Surface

Sources:

- `src/alpha_system/labels/fast/materializer.py`
- `src/alpha_system/labels/fast/fixed_horizon.py`
- `src/alpha_system/labels/fast/__init__.py`

Surface:

- `FastLabelMaterializer`
- `FastLabelPack`
- `FastLabelDeclaration`
- `FastFixedHorizonLabelMetadata`
- `FastLabelComputationMetadata`
- `FastLabelComputation`
- `LabelPanelFrameRequest`
- `build_fixed_horizon_label_pack(...)`
- `fixed_horizon_pack_coverage(...)`
- `supports_fixed_horizon_label_pack(...)`
- `FAST_LABEL_PRODUCER_ENGINE_ID`
- `FAST_LABEL_VALUE_SCHEMA_VERSION`

Coverage and known defect:

- `FastLabelPack` currently accepts only `FixedHorizonLabelDefinition`.
  There is no cost-adjusted, path, or event pack.
- `FastLabelMaterializer` loads OHLCV/BBO canonical panels through sanctioned
  local readers, computes records, writes value stores, and registers through
  `LabelRegistry` using `_REGISTRY_WRITE_LOCK` for serial writes.
- The existing compute kernel `_compute_fixed_horizon_records(...)` assumes
  minute horizons through `definition.horizon_minutes` and a `series_id` +
  terminal-event join in the prepared Polars panel.
- The disclosed stale-enum defect is present: `FIXED_HORIZON_LABEL_IDS` now
  reflects the extended governed `FixedHorizonLabelName` enum, but
  `fixed_horizon_pack_coverage()` calls `_horizon_minutes(...)` for non-minute
  tokens, and `labels/fast/fixed_horizon.py:96-101` still says the governed
  enum covers only trade-price 1/3/5/10/15/30m and midprice 1/3/5/10/30m.
- This phase did not repair the defect. It is LCFP-P03 input.

Design implications for later phases:

- P02 should define a shared panel/terminal/guard contract before P03 changes
  this module.
- P03 must repair `_horizon_minutes(...)`, the stale `governance_gap_note`, and
  coverage behavior before extending fixed/extended/session/maintenance support.
- Producer code must emit values only and preserve `LabelVersion` identity from
  the governed `LabelContractSpec`.

## FUTSUB P16-P20 Label Needs

Committed configs:

| FUTSUB phase | Config | Family / pack | Labels or metrics | Symbols | Years | Input schemas |
| --- | --- | --- | --- | --- | --- | --- |
| P16 | `configs/labels/scaleout/fixed_horizon.json` | `fixed_horizon` | `fwd_ret_1m`, `fwd_ret_3m`, `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_15m`, `fwd_ret_30m` | `ES`, `NQ`, `RTY` | `2018`-`2026` in config; accepted summaries exclude blocked `2018` | `ohlcv_1m` |
| P17 | `configs/labels/scaleout/extended_horizon.json` | `fixed_horizon` / `extended_horizon` | `fwd_ret_60m`, `fwd_ret_120m`, `fwd_ret_240m` | `ES`, `NQ`, `RTY` | `2018`-`2026` in config; accepted summaries exclude blocked `2018` | `ohlcv_1m` |
| P18 | `configs/labels/scaleout/session_close_maintenance_flat.json` | `session_close_maintenance_flat` | `session_close`, `maintenance_flat` | `ES`, `NQ`, `RTY` | `2018`-`2026` in config; accepted summaries exclude blocked `2018` | `ohlcv_1m`, `ohlcv_dense_research_grid` |
| P19 | `configs/labels/scaleout/cost_adjusted.json` | `cost_adjusted` | cost/spread-adjusted forward-return scope across `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | `ES`, `NQ`, `RTY` | `2018`-`2026` in config; predecessor paused during P19 | `ohlcv_1m`, `bbo_1m` |
| P20 | `configs/labels/scaleout/path.json` | `path` | `mfe`, `mae`, `target_before_stop`, `triple_barrier` across `5m`, `10m`, `15m`, `30m`, `60m`, `120m`, `240m` | `ES`, `NQ`, `RTY` | `2018`-`2026` in config; not run before pause | `ohlcv_1m` |

Value-free existing coverage:

- `research/futures_substrate_scaleout_v1/label_packs/fixed_horizon/coverage_summary.md`
  records P16 reference-engine fixed-horizon materialization summary.
- `research/futures_substrate_scaleout_v1/label_packs/extended_horizon/coverage_summary.md`
  records P17 extended-horizon rows, guard drops, and effective samples.
- `research/futures_substrate_scaleout_v1/label_packs/session_close_maintenance_flat/coverage_summary.md`
  records P18 close-out coverage and terminal semantics.
- P19/P20 commit-eligible handoffs/coverage are absent in this worktree because
  FUTSUB is deliberately paused at P19. `handoffs/LABEL_COMPUTE_FAST_PATH_V1/FUTSUB_PAUSE_STATE.md`
  records the paused state and preservation rules.

## Roll Guard Semantics

Sources:

- `src/alpha_system/labels/roll_guard.py`
- `docs/futures_substrate_scaleout/ROLL_GUARD.md`
- `research/futures_substrate_scaleout_v1/roll_guard/roll_guard_contract.md`
- `campaigns/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/RISK_REGISTER.md`

Symbols and policies:

- `RollCrossPolicy`: `drop`, `truncate`, `flag`, `invalid`.
- `RollGuardAction`: `pass`, `drop`, `truncate`, `flag`, `invalid`.
- `DEFAULT_CROSS_ROLL_POLICY = RollCrossPolicy.DROP`.
- `SAFE_MISSING_CALENDAR_POLICY = RollCrossPolicy.DROP`.
- `ROLL_POLICY_ID = "roll_cme_index_futures_quarterly"` and
  `ROLL_GUARD_VERSION = "roll_guard_v1"`.
- Default roll-window split is two days before the approximate roll date and
  one day after.

Calendar semantics:

- The roll calendar is analytic/ex-ante for CME equity-index quarterly roots
  `ES`, `NQ`, and `RTY`: March/June/September/December cycle, third Friday
  expiration, roll date eight calendar days before expiration.
- The calendar is approximate and not provider-exact splice truth.
- Missing or ambiguous calendar coverage fails closed to `drop`.

Risk context:

- R-036 records that prior roll-countdown features were derived from future
  contract-id changes and were excluded from the trusted causal substrate.
- R-037 records that roll-crossing label guard wiring was a realized risk:
  forward labels over continuous unadjusted front-month series can measure a
  cross-contract gap unless the label path uses contract-scoped terminal lookup
  and roll guard semantics.

## Label Availability Policy

Source: `src/alpha_system/labels/version.py`.

Symbols:

- `LabelAvailabilityPolicy`
- `LabelAvailabilityConsumer.LABELS_ONLY`
- `LabelContractSpec.from_label_spec(...)`
- `LabelValueRecord`

Contract:

- `LabelAvailabilityPolicy.from_label_spec(...)` derives
  `label_available_ts_derivation_rule` as:
  `label.label_available_ts = max(horizon_end_ts, path_rules terminal availability, LabelSpec.availability_time)`.
- `future_data_legal_only_for_labels` is true only when forward data is allowed
  and `legal_consumer` is `labels_only`.
- `LabelContractSpec` validates that availability fields, leakage checks, path
  rules, barriers, and cost adjustment match the governed `LabelSpec`.
- `LabelValueRecord.__post_init__(...)` enforces:
  `horizon_end_ts >= event_ts`, `label_available_ts >= event_ts`,
  `label_available_ts >= horizon_end_ts`, and
  `label_available_ts >= LabelSpec.availability_time`.

Per-family derivation points:

- Fixed horizon: max terminal row `available_ts` and governed availability floor.
- Cost-adjusted: max `horizon_end_ts`, governed availability floor, and terminal
  BBO availability when present.
- Path: max resolution row event time, resolution row availability, and governed
  availability floor.
- Event: max horizon/resolution time, relevant future availability candidates,
  and governed availability floor.

Exact `label_available_ts` parity is a first-class dimension for every later
producer pack.

## Label Registry Schema

Sources:

- `src/alpha_system/labels/store.py`
- `src/alpha_system/labels/registry.py`
- `src/alpha_system/labels/fast/materializer.py`

Registry path and tables:

- `LabelRegistry.from_alpha_data_root(...)` resolves
  `$ALPHA_DATA_ROOT/registry/labels.sqlite`.
- `_ensure_schema(...)` creates `label_registry_records`,
  `label_lineage_records`, and `label_deprecation_records`.
- `LabelRegistryRecord` is metadata only; it does not store label values.

Key fields:

- `label_version_id`, `label_id`, `label_spec_id`, `lifecycle_state`.
- `materialization_plan_id`, `dataset_version_id`, `partition_id`,
  `materialization_output_path`.
- `value_store_format`, `parquet_path`, `value_content_hash`,
  `value_schema_version`, `value_record_count`.
- `first_event_ts`, `last_event_ts`, `first_label_available_ts`,
  `last_label_available_ts`, `exposure_status`, `registered_at`,
  and canonical `metadata_json`.
- `LabelLineageRecord` stores contract provenance and must bind the same
  `LabelVersion`, `LabelContractSpec`, and `label_spec_id`.

Write and resolve path:

- `LabelRegistry.register_materialized_label(...)` validates a
  `LabelMaterializationResult`, summarizes materialized metadata, builds
  duplicate/equivalent exposure reports, and persists idempotently through
  `_persist_label(...)`.
- `LabelRegistry.resolve_label(...)`, `resolve_label_by_version(...)`, and
  `resolve_lineage(...)` are read paths by exact `label_version_id`.
- `FastLabelMaterializer.register_pack(...)` writes through `LabelRegistry` and
  holds `_REGISTRY_WRITE_LOCK` so pack registration remains serial.
- Fast producer lineage records `producer_engine_id =
  "alpha_system.labels.fast.pack_materializer.v1"` and
  `value_schema_version = "alpha_system.labels.fast.values.v1"` in contract
  provenance. The reference engine remains the oracle; producer provenance is
  metadata, not identity.

Legacy local helper:

- `LocalLabelStore` writes JSONL under a local-only root outside the repo.
- `register_label_version(...)` writes an older `label_versions` table through
  a temp/local registry path and is not the current pack registry path used by
  LCFP.

## Parity Harness Inventory

Source: `tests/unit/feature_compute_fast_path/parity_harness.py`.

Label symbols:

- `LabelParityTolerance(abs=0.0, rel=0.0, reason="exact label parity expected")`.
- `assert_label_records_match(...)`.

Current assertions:

- Both reference and producer records are non-empty.
- Both sides use the expected `label_version_id`.
- Record keys match by `(label_version_id, entity_id, event_ts)`.
- For each key, exact parity is required for `horizon_end_ts`,
  `label_available_ts`, `quality_flags`, and `label_spec_id`.
- Values are exact by default, or approximate when a non-zero tolerance is
  explicitly supplied. Nested mappings are compared recursively.

P07 extension points:

- Add explicit roll/maintenance guard assertions for dropped/flagged/null cases.
- Add per-family tolerance defaults only where justified by implementation
  details.
- Add summary counters for compared records, gap/null counts, and max/median
  numeric differences without committing per-row values.
