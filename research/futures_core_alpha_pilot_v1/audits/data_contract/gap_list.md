# FUTCORE-P13 Minimal Gap List

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`
Phase: `FUTCORE-P13`
Downstream owner: `FUTCORE-P15`
Cap: `research_budget_policy.max_new_feature_or_label_requests <= 5`

This list contains only primitives or grouped primitive bindings required by at
least one accepted AlphaSpec that do not resolve through the locked
`FUTCORE-P03` FeaturePack or LabelPack. It is value-free and does not create
FeatureRequests, LabelSpecs, source code, data, or materialized values.

## Gap List

| Budget item | Missing primitive(s) | Needed by accepted AlphaSpec(s) | One-line justification |
| --- | --- | --- | --- |
| `P15-G1` | `fwd_ret_15m` LabelPack binding | `aspec_a41dcccac5552de945aba825`; also the full primary horizon matrix for accepted VWAP/session, regime, liquidity/PA, and BBO specs. | `5m`, `10m`, and `30m` labels resolve in P03, but no `15m` LabelPack member resolves. |
| `P15-G2` | VWAP/session FeaturePack binding for running VWAP, completed ETH/anchored VWAP, distance-to-VWAP, and opening-range context | `aspec_b40aee52d4399dd5b855a6ed`; `aspec_43cd6c154bca2fcc419eee83` | Accepted VWAP/session specs require these point-in-time session primitives, but P03 locks no VWAP FeaturePack member. |
| `P15-G3` | Cross-market derived-state FeaturePack binding for beta residual, ES/RTY basket residual, relative-rank/catch-up, pair divergence, and agreement state | `aspec_8d9e272e4b78eedcd27f0bec`; `aspec_a41dcccac5552de945aba825`; `aspec_fa4895a43a80d4eef0a607a4` | Base returns resolve, but the accepted cross-market derived states do not resolve as locked FeaturePack primitives. |
| `P15-G4` | Additional base-OHLCV derived-state FeaturePack binding for trendiness, ATR, fixed prior-range/compression boundaries, sweep flags, breakout flags, and failure-deadline flags | `aspec_eb962fc197eaf3955c5e4711`; `aspec_df2d040e45564c259ef3de6d`; `aspec_39ffc190cfbfa6ba0b1a2a25` | Rolling volatility/range, returns, range position, and volume zscore resolve, but these accepted regime/liquidity primitives are not separately registered in P03. |
| `P15-G5` | BBO top-book confirmation FeaturePack binding for spread, spread ticks, spread zscore, top-book depth, wide-spread flag, low-depth flag, missing-BBO flag, and bad-quote flag | `aspec_1284e49b083df11eeb0481ea` | The accepted BBO AlphaSpec is confirmation/risk-control only, but P03 locks no BBO DatasetVersion or BBO FeaturePack member. |

## Non-Gaps Confirmed By P13

| Primitive | Reason it is not a gap |
| --- | --- |
| `fwd_ret_5m` | Resolves as `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` with valid `label_available_ts`. |
| `fwd_ret_10m` | Resolves as `lver_4170332f366d6945a37cfe8980395626c393b40c2e1c36944ffb784b88cc7941` with valid `label_available_ts`. |
| `fwd_ret_30m` | Resolves as `lver_69c9900cbac5e679f8d97d350e30f493f30a498eb3d47463e6ab9995f1c0310a` with valid `label_available_ts`. |
| Session context features | `base_ohlcv_rth_flag` and `base_ohlcv_session_minute` resolve by primitive name in P03, although accepted source drafts cite stale FeatureVersion ids that P14 must replace with P03 ids. |
| Base OHLCV pack members | `base_ohlcv_returns`, `base_ohlcv_log_returns`, `base_ohlcv_rolling_volatility`, `base_ohlcv_rolling_range`, `base_ohlcv_range_position`, and `base_ohlcv_volume_zscore` resolve with valid `available_ts`. |

## No-Op Alternative

A strict no-op remains possible only if `FUTCORE-P14` constrains StudySpecs to
the locked primitive set and explicitly defers or rejects the portions of the
accepted AlphaSpecs that depend on `P15-G1` through `P15-G5`. That path would
preserve the input-pack boundary but would not satisfy the full accepted
AlphaSpec set as written.

## Budget Outcome

The gap list has exactly five candidate P15 budget items. It matches but does
not exceed the campaign cap, does not expand the universe, and does not request
fragile `1m` or `3m` labels as promotion-basis inputs.

P15 still owns the implementation or no-op decision for each item. Any P15 work
must remain point-in-time, registry-bound, value-free in git, and no-claims.
