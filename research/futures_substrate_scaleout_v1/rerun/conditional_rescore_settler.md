# FUTSUB Conditional / Interaction Re-score Settler

Read-only diagnostic settler for the A-vs-B question on the four FUTSUB
kill-shot mechanisms: are they ALSO null under a conditional / interaction lens,
or is the linear `|Pearson IC|` gate blind to a regime-gated edge?

Research-only. This file records diagnostics. It makes no profitability,
tradability, alpha, promotion, or production claim. It does not change any
campaign verdict, registry, lock, run-state, or `ACTIVE_CAMPAIGN`.

Scope: `regime`, `liquidity_pa`, `vwap_session`. `bbo_tradability` is excluded
as substrate-defective (time-sampled forward-filled top-of-book proxy), per the
P28/P29 caveat. The two `liquidity_pa` and the two `vwap_session` V2 StudySpecs
are within-family near-duplicates (identical P28 factor summaries), so one spec
per mechanism covers all six rerun studies.

## (a) Were the conditional metrics already computed?

Two-part answer.

1. NOT in P28. The P28 rerun (`runs/2026-06-07T235209Z_.../phases/FUTSUB-P28/`,
   scratch `/tmp/futsub_p28_repair_rerun.json` and siblings, committed
   `rerun_diagnostics_summary.md`) computed only factor diagnostics (Pearson/rank
   IC, buckets, walk-forward), label diagnostics, and N_eff. It did NOT invoke
   `regime_filter_uplift`, `conditional_strategy_improvement`, or
   `build_regime_split_report`, and it did not persist the per-row observation
   samples (only aggregate scalars survive). Grep of every P28 artifact and the
   four scratch JSONs returns no `uplift` / `conditional_*` / `regime_split`
   output values.

2. YES in the ORIGINAL Core Pilot (FUTCORE-P17/P18/P19,
   `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`). `build_regime_split_report` /
   spread-liquidity / session-view split reports WERE computed and persisted,
   on the pre-scaleout (ES-only, ~20k-obs) substrate, with status `INCONCLUSIVE`
   (most regime buckets fell to `low_sample`). Provenance:
   - `research/futures_core_alpha_pilot_v1/diagnostics_reports/regime/sspec_267cc052e37668339c38d179/runtime_reports.json`
     -> `standard_runtime_reports.regime_split_report.split_summaries`
   - `research/futures_core_alpha_pilot_v1/diagnostics_reports/liquidity_pa/sspec_27bf1262b0bd23d27191cc86/runtime_reports.json`
     -> `standard_runtime_reports.spread_liquidity_split_diagnostics.split_summaries`
   - `research/futures_core_alpha_pilot_v1/diagnostics_reports/vwap_session/sspec_aff70fcbc4b7ff226fcc8149/runtime_reports.json`
     -> `diagnostics_reports.splits.split_summaries`

Because the persisted artifacts were small-sample and partly `low_sample`, a
fresh, fully-powered conditional re-score over the locked scaleout substrate was
also run (read-only) to settle the question. Both sources agree.

## Persisted original-pilot conditional metrics (FUTCORE, ~20k obs, INCONCLUSIVE)

`regime` (`regime_split_report`, status INCONCLUSIVE; trend/gate buckets
`low_sample`):

| split | n_with | uplift | cond_mean_delta | cond_hit_delta |
| --- | ---: | ---: | ---: | ---: |
| volatility:high | 10157 | +8.12e-05 | +4.08e-05 | +0.0385 |
| volatility:low | 10159 | -7.95e-05 | -3.99e-05 | -0.0366 |
| range:compression | 5510 | -2.21e-07 | -1.61e-07 | -0.0359 |
| range:not_compression | 14809 | +2.56e-06 | +7.03e-07 | +0.0148 |
| trend:* / gate:* | 0 | None | None | None (low_sample) |

`liquidity_pa` (`spread_liquidity_split_diagnostics`, INCONCLUSIVE; spread/trend
buckets `low_sample` / unresolved-no-BBO):

| split | n_with | uplift | cond_mean_delta | cond_hit_delta |
| --- | ---: | ---: | ---: | ---: |
| volatility:high | 24558 | +4.57e-05 | +2.21e-05 | +0.0254 |
| volatility:low | 22913 | -4.39e-05 | -2.28e-05 | -0.0251 |
| liquidity:thick | 11269 | +2.53e-05 | +1.93e-05 | +0.0134 |
| liquidity:thin | 17309 | -1.44e-05 | -9.17e-06 | -0.0139 |

`vwap_session` (`splits`, INCONCLUSIVE; RTH buckets `low_sample`):

| split | n_with | uplift | cond_mean_delta | cond_hit_delta |
| --- | ---: | ---: | ---: | ---: |
| session_view:pre_RTH | 450 | +5.08e-05 | +4.75e-05 | +0.0717 |
| session_view:ETH_overnight | 2399 | -4.01e-05 | -2.61e-05 | -0.0149 |
| session_view:ETH_evening | 1783 | -6.27e-06 | -4.64e-06 | -0.0435 |
| session_view:post_RTH | 280 | +1.63e-05 | +1.56e-05 | -0.0198 |

Pattern: a small, regime-dependent SIGN FLIP (high-vol positive, low-vol
negative; thick vs thin) on tiny magnitudes (uplift ~1e-5). Symmetric linear IC
averages these opposing micro-effects toward zero. But every populated bucket is
microscopic and the report status is `INCONCLUSIVE` (low sample / unresolved
spread-bucket inputs), so these are not evidence of a recoverable edge.

## (b) Fresh full-population conditional re-score (locked scaleout substrate)

Method (read-only): resolve each V2 StudySpec's declared-factor feature locks and
`fwd_ret_5m` label locks through `FeatureStore.resolve_active_feature` /
`LabelRegistry.resolve_active_label` (pure SELECTs), load the registered local
Parquet value stores, filter each pack to the exact `feature_version_id` /
`label_version_id`, join feature->label by `(entity_id, event_ts)`, stack all
declared factors x `fwd_ret_5m` (the same construction P28's IC used), then apply
the SAME conditional lens as `alpha_system.research.regimes` — filter =
`factor_value > 0` (the `regimes._active` fallback when no explicit
`regime_filter` field is present):

- `uplift = mean(ret|factor>0) - mean(ret|factor<=0)`
- `conditional_mean = mean(ret|factor>0) - mean(ret|all)`
- `conditional_hit_rate = hitrate(factor>0) - hitrate(all)`

Math was cross-validated against the actual `regime_filter_uplift` /
`conditional_strategy_improvement` library functions on a 332,675-row ES_2019
trendiness sample: outputs matched to floating precision (uplift
-2.161459924489953e-06 identical). Script: `/tmp/futsub_conditional_rescore_fast.py`.
Raw JSON: `/tmp/futsub_conditional_rescore.json` (local-only).

| mechanism | N (obs) | reproduced Pearson IC | reproduced rank IC | uplift | cond_mean | cond_hit | mean(ret\|all) | mean(ret\|factor>0) | mean(ret\|factor<=0) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| regime | 51,136,561 | +0.00183 | -6.8e-05 | -4.73e-06 | -1.06e-06 | -0.00137 | +3.686e-06 | +2.629e-06 | +7.356e-06 |
| liquidity_pa | 66,215,181 | -0.00175 | -0.00561 | -3.99e-06 | -2.46e-06 | -0.00095 | +3.636e-06 | +1.181e-06 | +5.167e-06 |
| vwap_session | 39,430,802 | -0.00013 | -0.00090 | -3.12e-07 | -2.62e-08 | -0.00058 | +3.510e-06 | +3.484e-06 | +3.796e-06 |

Notes:
- The reproduced IC is in the same near-zero regime as P28 (|IC| <= 0.0019).
  Exact equality with P28's capped numbers is not expected: P28 capped to ~75k
  observations on a partition subset; this re-score uses the full multi-year,
  multi-instrument locked population (39-66M obs), so it is the more powered view.
- Mean 5-minute forward returns are ~3.5e-06 (~0.035 bps) across the board;
  conditional means barely move off that. `uplift` magnitudes are ~1e-6
  (~0.0001 bps) and hit-rate deltas |.| <= 0.0014 (<0.14 percentage points).
- This factor>0 lens does not reproduce the original-pilot volatility-bucket
  sign flip (it conditions on factor sign, not on an external volatility regime
  field). The persisted FUTCORE regime-split IS the volatility-bucketed lens, and
  it too is microscopic and `INCONCLUSIVE` (see above).

## (c) Verdict

NULL. The three live mechanisms are also null under the conditional / interaction
lens.

- The existing conditional diagnostics (`regime_filter_uplift`,
  `conditional_strategy_improvement`, `build_regime_split_report`) return
  effectively-zero conditional effects in BOTH the persisted FUTCORE artifacts
  and the fully-powered scaleout re-score.
- Where a regime-conditioned sign structure exists (FUTCORE volatility buckets:
  high-vol +, low-vol -), the magnitudes are ~1e-5 uplift / ~0.025-0.038
  hit-rate, on `INCONCLUSIVE` low-sample buckets — not a recoverable edge, and
  consistent with noise that a symmetric linear IC averages toward zero.
- At full power (tens of millions of observations), conditional uplift collapses
  to ~1e-6 and hit-rate deltas to < 0.0015.

The linear `|Pearson IC|` gate is NOT hiding a material conditional/interaction
edge for these three mechanisms. The conditional concern is closed; the four
mechanisms (three live + substrate-defective bbo) remain dead under the current
detector shape. An interaction/regime-gated detector is not warranted by this
evidence for these specific mechanisms.

## (d) Caveats and limitations

- Population is not identical to P28's: this re-score uses the full locked
  multi-year / multi-instrument 5m population (39-66M obs) rather than P28's
  ~75k cap. This is intentional (more power) and the IC stays in the same
  near-zero regime, but the numbers are not a byte-for-byte P28 replay.
- The `factor_value > 0` lens is the symmetric two-sided conditioning the
  library applies when no explicit `regime_filter` field is supplied. It is one
  interaction shape, not an exhaustive search of all possible regime gates,
  thresholds, or multi-factor interactions. It does NOT prove no nonlinear
  structure of any kind exists — only that the sanctioned conditional primitives,
  and the persisted regime/spread/session split reports, are null here.
- Observations are stacked across all declared factors per study (matching P28's
  IC construction). A single strong factor could be diluted by stacking; e.g. the
  persisted FUTCORE `vwap_session` `factor_session_minute` shows Pearson IC
  +0.068 / rank IC +0.057 (n=6862) in isolation vs the stacked aggregate ~0.
  That is a STACKING-blindness flag, distinct from the conditional question, and
  is not resolved here.
- Rows are not independent samples (5m forward returns overlap; N_eff << N).
  Magnitudes, not significance tests, drive this read; the conditional effects
  are too small for sign/significance to matter.
- `build_regime_split_report` at scaleout scale was NOT re-invoked here because
  its conditioning fields (`volatility_bucket`, `spread_bucket`,
  `liquidity_bucket`, `trend_state`) are not present as columns in the locked
  observation rows; the persisted FUTCORE split reports are the available
  evidence for that bucketed lens and agree with the null read.

## Provenance

- Persisted conditional artifacts: the three `runtime_reports.json` paths above.
- Fresh re-score script (local-only): `/tmp/futsub_conditional_rescore_fast.py`.
- Fresh re-score raw output (local-only): `/tmp/futsub_conditional_rescore.json`.
- Library cross-check: `regime_filter_uplift` / `conditional_strategy_improvement`
  in `src/alpha_system/research/regimes.py` matched the polars math exactly.
- No registry, lock, run-state, `ACTIVE_CAMPAIGN`, or core diagnostics code was
  modified. All value reads were read-only against the locked local Parquet
  stores under `ALPHA_DATA_ROOT`.
