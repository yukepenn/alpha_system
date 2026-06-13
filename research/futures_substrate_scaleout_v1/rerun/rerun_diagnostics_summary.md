# FUTSUB-P28 Core Pilot Re-run Diagnostics Summary

Value-free executor summary for `FUTSUB-P28` in
`ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1`.

## Execution Status

The six prior-INCONCLUSIVE Core Pilot StudySpecs identified by the P110000 V2
re-lock report were re-executed under the research interpreter with
`ALPHA_DATA_ROOT=/home/yuke_zhang/alpha_data/alpha_system`. Every committed
feature and label lock resolved exactly to a registered local pack, and every
registered pack pointed at an existing current Parquet value-store manifest.

The repair replay loaded locked feature and label values from local Parquet,
joined them into runtime observation rows by exact `entity_id,event_ts`, required
feature availability before label availability, and invoked the sanctioned
runtime diagnostics builders. No values, registries, Parquet extracts, local
databases, or raw provider data are committed here.

This file is not a verdict refresh and does not promote any study.

## Runtime Surfaces Used

- `alpha_system.data.foundation.version_registry.resolve_dataset_version`
- `alpha_system.runtime.input_resolver.FeatureLabelPackResolver.resolve_feature_packs`
- `alpha_system.runtime.input_resolver.FeatureLabelPackResolver.resolve_label_packs`
- `alpha_system.runtime.diagnostics.factor.build_factor_diagnostics_run`
- `alpha_system.runtime.diagnostics.label.build_label_diagnostics_report`
- `alpha_system.runtime.diagnostics.splits.n_eff.build_n_eff_sample_report`

No external provider, broker, paper/live trading, order-routing, registry-write,
feature/label materialization, verdict, promotion, or PR/merge action was
performed.

## Re-runnable Set

The P110000 V2 re-lock report classifies all six prior-INCONCLUSIVE studies as
P28 rerun candidates. The four re-locked cross-market StudySpecs remain
prior-REJECT audit-only inputs and were not rerun in this phase.

| Family | Original StudySpec | V2 StudySpec | Feature locks | Label locks | Resolver outcome |
| --- | --- | --- | ---: | ---: | --- |
| `regime` | `sspec_267cc052e37668339c38d179` | `sspec_dec89a327a9c50957adca780` | 456/456 | 96/96 | clean |
| `liquidity_pa` | `sspec_27bf1262b0bd23d27191cc86` | `sspec_840e8342564226f2c3257903` | 552/552 | 96/96 | clean |
| `liquidity_pa` | `sspec_02c400a561891171a33c0c66` | `sspec_c237c6a8ce40c2585836fae0` | 552/552 | 96/96 | clean |
| `bbo_tradability` | `sspec_9f6f741192a4b534f06e51c0` | `sspec_533f665ec4ac063dbb664a54` | 600/600 | 96/96 | clean |
| `vwap_session` | `sspec_aff70fcbc4b7ff226fcc8149` | `sspec_1604b063f3a3401208ee0239` | 480/480 | 96/96 | clean |
| `vwap_session` | `sspec_69c22ec5847395ac8e81b5b6` | `sspec_f6cbd88caa0445f0f56d81fd` | 480/480 | 96/96 | clean |

## Inputs Consumed

The resolver consumed only committed StudySpec locks and local registry
metadata. The value replay read only the locked local feature and label Parquet
stores behind those registry records. It did not read raw provider files and did
not call external providers.

| Family | V2 StudySpec | Feature families present | Parquet value stores current |
| --- | --- | --- | --- |
| `regime` | `sspec_dec89a327a9c50957adca780` | `base_ohlcv`, `regime_volatility_compression`, `session_calendar_maintenance` | 456 feature, 96 label |
| `liquidity_pa` | `sspec_840e8342564226f2c3257903` | `base_ohlcv`, `liquidity_sweep_pa_structure`, `session_calendar_maintenance` | 552 feature, 96 label |
| `liquidity_pa` | `sspec_c237c6a8ce40c2585836fae0` | `base_ohlcv`, `liquidity_sweep_pa_structure`, `session_calendar_maintenance` | 552 feature, 96 label |
| `bbo_tradability` | `sspec_533f665ec4ac063dbb664a54` | `base_ohlcv`, `bbo_tradability_top_book`, `session_calendar_maintenance` | 600 feature, 96 label |
| `vwap_session` | `sspec_1604b063f3a3401208ee0239` | `base_ohlcv`, `session_calendar_maintenance`, `vwap_session_auction` | 480 feature, 96 label |
| `vwap_session` | `sspec_f6cbd88caa0445f0f56d81fd` | `base_ohlcv`, `session_calendar_maintenance`, `vwap_session_auction` | 480 feature, 96 label |

## Factor Diagnostics Observed

Factor diagnostics were run over deterministic in-memory observation samples
loaded from the locked Parquet stores across the locked 5m, 10m, 15m, and 30m
label horizons. The diagnostics below are aggregate runtime summaries only; they
do not embed per-row feature or label values.

| V2 StudySpec | Family | Runtime status | Rows | Numeric pairs | Coverage | Missingness | Pearson IC | Rank IC | WF folds |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sspec_dec89a327a9c50957adca780` | `regime` | `DIAGNOSTICS_COMPLETE` | 74,592 | 72,441 | 0.9712 | 0.0288 | -0.0204 | -0.0002 | 67 |
| `sspec_840e8342564226f2c3257903` | `liquidity_pa` | `DIAGNOSTICS_COMPLETE` | 74,304 | 72,595 | 0.9770 | 0.0230 | 0.0072 | 0.0008 | 67 |
| `sspec_c237c6a8ce40c2585836fae0` | `liquidity_pa` | `DIAGNOSTICS_COMPLETE` | 74,304 | 72,595 | 0.9770 | 0.0230 | 0.0072 | 0.0008 | 67 |
| `sspec_533f665ec4ac063dbb664a54` | `bbo_tradability` | `DIAGNOSTICS_COMPLETE` | 74,976 | 66,877 | 0.8920 | 0.1080 | -0.0050 | 0.0008 | 61 |
| `sspec_1604b063f3a3401208ee0239` | `vwap_session` | `DIAGNOSTICS_COMPLETE` | 74,880 | 66,067 | 0.8823 | 0.1177 | 0.0033 | -0.0011 | 61 |
| `sspec_f6cbd88caa0445f0f56d81fd` | `vwap_session` | `DIAGNOSTICS_COMPLETE` | 74,880 | 66,067 | 0.8823 | 0.1177 | 0.0033 | -0.0011 | 61 |

All six factor runs used purge gap 10 and embargo gap 10. Bucket direction was
`mixed` and bucket monotonicity was false for every run. These descriptive
statistics are not a promotion rule, a significance claim, a profitability
claim, or a tradability claim.

## Label Diagnostics Observed

Locked label rows loaded for all six studies. The corrected label replay used
the runtime's established observation-summary configuration for supplied label
observations without a separate feature/label audit bundle. Numeric label
outcomes loaded, missing outcome rate was 0, horizon coverage was complete,
label `available_ts` checks passed, and declared cost-model metadata was
present.

The label diagnostics runtime still returned
`DIAGNOSTICS_FAILED` statuses with `weak_diagnostics` because the
`label_coverage_missingness_gate` fails closed when no separate audit bundle is
supplied. This is a real residual diagnostic caveat for `FUTSUB-P29`. It is
not a missing-reader, missing-row, stale-lock, or missing-substrate result, but
it also means this phase should not be described as a clean label-diagnostics
rerun.

| V2 StudySpec | Runtime status | Reason codes | Label rows | Numeric outcomes | Pos / Neg / Neutral | Horizon coverage | Failing gate |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| `sspec_dec89a327a9c50957adca780` | `DIAGNOSTICS_FAILED` | `weak_diagnostics` | 74,976 | 74,976 | 36,940 / 33,294 / 4,742 | 4/4 | `label_coverage_missingness_gate` |
| `sspec_840e8342564226f2c3257903` | `DIAGNOSTICS_FAILED` | `weak_diagnostics` | 74,976 | 74,976 | 36,940 / 33,294 / 4,742 | 4/4 | `label_coverage_missingness_gate` |
| `sspec_c237c6a8ce40c2585836fae0` | `DIAGNOSTICS_FAILED` | `weak_diagnostics` | 74,976 | 74,976 | 36,940 / 33,294 / 4,742 | 4/4 | `label_coverage_missingness_gate` |
| `sspec_533f665ec4ac063dbb664a54` | `DIAGNOSTICS_FAILED` | `weak_diagnostics` | 74,976 | 74,976 | 36,940 / 33,294 / 4,742 | 4/4 | `label_coverage_missingness_gate` |
| `sspec_1604b063f3a3401208ee0239` | `DIAGNOSTICS_FAILED` | `weak_diagnostics` | 74,976 | 74,976 | 36,940 / 33,294 / 4,742 | 4/4 | `label_coverage_missingness_gate` |
| `sspec_f6cbd88caa0445f0f56d81fd` | `DIAGNOSTICS_FAILED` | `weak_diagnostics` | 74,976 | 74,976 | 36,940 / 33,294 / 4,742 | 4/4 | `label_coverage_missingness_gate` |

## N_eff And Walk-Forward Context

N_eff context was produced through the P25 runtime reporting surface,
`alpha_system.runtime.diagnostics.splits.n_eff.build_n_eff_sample_report`, not
by a detached post-hoc spreadsheet calculation. For each fixed label horizon,
the replay supplied explicit horizon-overlap metadata with 1-minute sampling
cadence and discount factors equal to the locked horizon minutes
(`5`, `10`, `15`, `30`). The runtime surface validates that metadata via
`coerce_horizon_overlap_metadata`, applies the documented formula
`floor(rows / discount_factor)` bounded to `[0, rows]`, marks
`rows_are_not_independent_samples`, and can attach P24-shaped fold metadata via
`attach_n_eff_to_walk_forward_metadata`.

The scratch replay summary at `/tmp/futsub_p28_repair_rerun.json` preserved the
value-free derived fields used here: registered rows, discount factor,
`rows_are_not_independent_samples`, session/day aggregation, compact fold count,
purge gap 10, and embargo gap 10. The same contract is covered by
`tests/unit/futures_substrate_scaleout/test_n_eff_reporting.py`, including
per-fold attachment to P24 fold metadata and fail-closed behavior when overlap
metadata is missing or inconsistent. Rows are not independent samples. The
factor diagnostics replay also exercised purged/embargoed walk-forward folds
over the runtime observation samples.

The same label grid is locked for all six studies:

| Label horizon | Registered rows | Overlap discount | N_eff | Compact fold metadata |
| --- | ---: | ---: | ---: | --- |
| `fwd_ret_5m` | 7,455,294 | 5 | 1,491,058 | two compact folds, purge 10, embargo 10 |
| `fwd_ret_10m` | 7,416,879 | 10 | 741,687 | two compact folds, purge 10, embargo 10 |
| `fwd_ret_15m` | 7,379,178 | 15 | 491,945 | two compact folds, purge 10, embargo 10 |
| `fwd_ret_30m` | 7,294,349 | 30 | 243,144 | two compact folds, purge 10, embargo 10 |

These counts are reporting metadata only. They are not a significance test, a
multiple-testing correction, a promotion rule, a profitability claim, or a
tradability claim.

## Residual Gaps And Warnings

- No stale-lock, missing-pack, or missing-Parquet gap remains for the six V2
  StudySpecs in this P28 rerun set.
- Label diagnostics remain conservative because the runtime coverage/missingness
  gate expects a separate feature/label audit bundle. P28 did not fabricate that
  bundle; the value replay reports the fail-closed gate alongside the loaded
  numeric label rows. `FUTSUB-P29` must carry this as an explicit caveat when
  refreshing verdict evidence.
- BBO diagnostics remain a proxy context only. The BBO inputs are time-sampled
  and forward-filled top-of-book proxies, not execution truth and not passive
  fill, queue-position, or impact evidence.
- `FUTSUB-P29` owns any verdict refresh. This summary does not update
  `REJECT`, `INCONCLUSIVE`, `WATCH`, or `CANDIDATE_RESEARCH` states.
