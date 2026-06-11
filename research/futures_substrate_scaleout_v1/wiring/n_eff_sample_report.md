# N_eff Sample Report

Phase: `FUTSUB-P25`  
Sample type: tiny deterministic synthetic metadata  
Data scope: counts and metadata only

This report contains no per-row observations, prices, outcomes, provider
payloads, local paths, heavy artifacts, or deployment language.

## Estimator Reference

Contract: `docs/futures_substrate_scaleout/N_EFF.md`

Formula:

```text
implied_discount_factor = max(1, horizon / sampling_cadence)
n_eff = floor(rows / discount_factor), bounded to [0, rows]
```

The estimator requires explicit horizon, cadence, and discount-factor metadata.
It fails closed if that metadata is missing or understates the implied
horizon/cadence overlap.

## Per-Horizon Rows Versus N_eff

Synthetic cadence: one sample per minute.

| Horizon | Rows | Discount factor | Implied factor | N_eff | Marker |
| --- | ---: | ---: | ---: | ---: | --- |
| 30m primary | 2,400 | 30 | 30 | 80 | rows are not independent samples |
| 240m extended | 2,400 | 240 | 240 | 10 | rows are not independent samples |

The 240m extended horizon reports a stronger discount than the 30m primary
horizon at the same cadence.

## Session / Day Aggregation Hook

Synthetic observations: eight value-free metadata rows.

Configured fields:

- session: `session_label`, `session`, `session_segment`
- trade date: `trade_date`, `trade_date_id`

Aggregate counts:

| Metric | Count |
| --- | ---: |
| observation_count | 8 |
| session_unit_count | 2 |
| trade_date_unit_count | 2 |
| session_trade_date_unit_count | 4 |
| missing_session_count | 0 |
| missing_trade_date_count | 0 |

No session or trade date was inferred from timestamps.

## Walk-Forward Fold N_eff

Synthetic P24-shaped walk-forward metadata:

- `half_life_protocol`: `FAST`
- `train_window`: 360
- `validation_window`: 120
- `step_size`: 120
- `purge_gap`: 30
- `embargo_gap`: 30
- fold count: 3

30m primary horizon, discount factor 30:

| Split | Train rows | Train N_eff | Validation rows | Validation N_eff |
| --- | ---: | ---: | ---: | ---: |
| `walk_forward_0` | 330 | 11 | 120 | 4 |
| `walk_forward_1` | 330 | 11 | 120 | 4 |
| `walk_forward_2` | 330 | 11 | 120 | 4 |

240m extended horizon, discount factor 240:

| Split | Train rows | Train N_eff | Validation rows | Validation N_eff |
| --- | ---: | ---: | ---: | ---: |
| `walk_forward_0` | 330 | 1 | 120 | 1 |
| `walk_forward_1` | 330 | 1 | 120 | 1 |
| `walk_forward_2` | 330 | 1 | 120 | 1 |

The fold records preserve the P24 fold identity fields (`split_id`,
`purge_gap`, `embargo_gap`, and protocol name) and add train/validation
rows/N_eff blocks beside them.

## Fail-Closed Verification

Synthetic checks covered these cases:

| Case | Expected result |
| --- | --- |
| Missing horizon-overlap metadata | explicit `NEffSampleReportingError` |
| Discount factor below implied horizon/cadence overlap | explicit `NEffSampleReportingError` |
| Label diagnostics requested with fold metadata but no N_eff metadata | `DIAGNOSTICS_FAILED` with `n_eff_overlap_metadata_unavailable` |
| Label diagnostics without an N_eff request | prior payload shape, no `label_n_eff_report` |

Focused unit coverage lives in:
`tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py`.
