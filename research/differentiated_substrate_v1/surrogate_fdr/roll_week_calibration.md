# Real-Data Surrogate Calibration: sspec_61b60a8ca735bddea7feb9ff

This coordinator report is value-free: it records ids, run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, diagnostic, signal, or cost values.

## Scope

- Declared K per perturbation config: 60
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.
- Declared primary horizon used for this run: `30m`.
- Perturbation configs: trade_date_block_shuffle, trade_date_block_bootstrap.
- Runtime factor derivation path: `alpha_system.governance.surrogate_run.study_config_for_surrogate_scope` -> `StudyConfig.from_mapping`.
- Declared feature family: `session_calendar_roll`.
- Declared factor count: 1.
- Declared factors: `session_calendar_roll_in_roll_window_flag`.
- Declared feature pack lock count: 24.
- Declared label pack count: 24.
- Pooled instruments: `ES`, `NQ`, `RTY`.
- Declared partition years: 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026.
- Excluded all-null/constant factor partitions: 24.
- Staged surrogate sub-config count: 0.
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_dk_p02_roll_week`.

## Calibration Outcome

- Threshold verdict: `CALIBRATION_BLOCKED`.
- Block reason code: `no_numeric_declared_factors_for_surrogate`.
- Block reason: "real surrogate calibration has no declared factor with numeric content after recorded all-null exclusions".
- Sanctioned all-null exclusion fired on every one of the 24 declared feature-pack lock partitions; reason `all_null_values`.
- Run count: 0 (no admissible sub-config survived the all-null exclusion, so no surrogate perturbation runs were staged or executed).
- Statistic pass count: not applicable (no runs).
- This is a DATA_GAP block, not a `LEAKAGE_BLOCKED` result and not a `zero-pass-met` pass. No real-metric pass was claimed.

## Threshold

- Declared threshold: zero shuffled runs may clear the shared detection statistic.
- Statistic: `directional.pearson_ic` absolute value against threshold `0.950000`.
- This threshold was never evaluated because no admissible declared-factor partition reached scoring.
- Any shuffled statistic pass would have been `LEAKAGE_BLOCKED` and would require diagnosis before the kill-shot resumes.

## Root Cause

- The single declared conditioning factor `session_calendar_roll_in_roll_window_flag` is all-null / zero-variance across all 24 declared feature-pack lock partitions (ES, NQ, RTY for years 2019-2026).
- This is consistent with the R-036 offline-roll-metadata constraint: the roll-window flag has no usable signal variation on this offline substrate over the materialized window. The roll-related calendar conditioning is effectively populated only over the 2024-26 calendar coverage, and the roll-window flag carries no usable variation there for this factor.
- Because every partition was excluded under the sanctioned all-null path, the tool fail-closed with `no_numeric_declared_factors_for_surrogate` rather than fabricating a pass.

## Disposition

- `roll_week_flow` has no clean surrogate-FDR gate on this substrate and is therefore excluded from DK-P03 real-metric inspection.
- The active testable surface for DK-P03 is the four mechanisms that reached `zero-pass-met`: `day_of_week_effect`, `opex_pinning`, `month_end_flow`, and `open_close_auction_flow`.
- Re-admitting `roll_week_flow` would require a substrate with a non-degenerate roll-window conditioning feature; that is out of scope for this phase and is not a kill-shot blocker.
