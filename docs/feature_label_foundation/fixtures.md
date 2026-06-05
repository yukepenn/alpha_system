# Feature/Label Synthetic Fixtures

FLF-P25 adds tiny deterministic fixtures under
`tests/fixtures/feature_label/` and fail-closed tests under
`tests/no_lookahead/feature_label/`.

The fixtures are fabricated examples only. They are not real market data, not
provider captures, not materialized feature or label values, and not evidence of
alpha, profitability, tradability, or production readiness.

## Fixture Inventory

- `canonical_rows.json` contains two canonical OHLCV rows, three canonical BBO
  rows, and two dense-grid OHLCV rows.
- `partition_metadata.json` contains minimal development and locked-test
  metadata for partition-governance checks.
- `synthetic.py` loads the JSON fixtures and builds accepted DatasetVersion,
  governed FeatureRequest, and governed LabelSpec helper objects for tests.
- `README.md` documents the local fixture policy.

The BBO fixture includes one valid row, one `missing_bbo` zero quote, and one
`bbo_quarantined` row. The dense-grid fixture includes one provider-truth trade
row and one synthetic previous-close `no_trade` row with `has_trade=false`,
`synthetic=true`, `volume=0`, `fill_method=previous_close`, and no provider bar
reference.

## Example Configs

- `configs/features/examples/synthetic_fail_closed_feature_set.json`
- `configs/labels/examples/synthetic_fail_closed_label_set.json`

These configs are illustrative references for tests and docs. They are not
materialization requests and do not authorize generated value outputs.

## Fail-Closed Coverage Map

| Guard / Shortcut | Test Coverage |
| --- | --- |
| No approved governance `FeatureRequest` (`freq_`) blocks feature implementation | `test_missing_or_unapproved_feature_request_blocks_feature_implementation` |
| No validated `FeatureSpec` blocks feature values | `test_missing_validated_feature_spec_or_available_ts_rule_blocks_values` |
| No governance `LabelSpec` (`lspec_`) blocks label values | `test_missing_governed_label_spec_blocks_label_values` |
| Feature input missing `available_ts` is rejected | `test_canonical_feature_inputs_missing_available_ts_fail_before_values` |
| Feature derivation from `ingested_at` / non-`available_ts` rule is rejected | `test_missing_validated_feature_spec_or_available_ts_rule_blocks_values` |
| Label value missing `label_available_ts` is blocked | `test_label_available_ts_missing_or_too_early_blocks_audit` |
| Label `label_available_ts` earlier than availability is blocked | `test_label_available_ts_missing_or_too_early_blocks_audit` |
| Label series exposed as a live feature is blocked | `test_label_as_feature_reference_blocks_label_materialization_plan` |
| Future or centered live feature windows are blocked | `test_centered_or_future_windows_cannot_enter_live_feature_specs` |
| Raw-provider reader tokens are absent from feature/label code | `test_raw_provider_readers_are_not_reachable_from_feature_label_code` |
| Missing or abnormal BBO is flagged, not silently filled | `test_missing_or_abnormal_bbo_is_flagged_not_forward_filled` |
| Synthetic dense-grid no-trade rows are not real trade bars | `test_synthetic_dense_grid_no_trade_rows_are_never_real_trade_bars` |
| Locked-test partition use without governance contamination metadata is blocked | `test_locked_test_partition_requires_governance_contamination_metadata` |
| Locked-test fit policy without contamination metadata is blocked | `test_locked_test_fit_policy_requires_contamination_metadata` |

## Artifact Policy

The fixtures stay under `tests/fixtures/feature_label/` and are intentionally
small JSON/Python helper files. They do not read `.dbn`, `.zst`, parquet, arrow,
or feather files. They do not call Databento, IBKR, brokers, paper/live systems,
or order-routing surfaces. They do not commit feature values, label values,
registries, DBs, caches, logs, or report bundles.
