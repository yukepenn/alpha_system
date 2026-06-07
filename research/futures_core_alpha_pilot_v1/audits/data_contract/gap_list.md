# FUTCORE-P13 Minimal Gap List

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P13`  
Downstream owner: `FUTCORE-P15`  
Cap: `research_budget_policy.max_new_feature_or_label_requests <= 5`

This list contains only primitives or grouped primitive bindings that are
required by at least one accepted AlphaSpec and do not resolve through the
locked `FUTCORE-P03` FeaturePack/LabelPack. It is value-free and does not create
FeatureRequests, LabelSpecs, code, data, or materialized values.

## Gap List

| Budget item | Missing primitive(s) | Needed by accepted AlphaSpec(s) | One-line justification |
| --- | --- | --- | --- |
| `P15-G1` | `fwd_ret_10m` LabelPack binding | `aspec_8d9e272e4b78eedcd27f0bec`; also required for full primary horizon matrix in accepted VWAP, regime, liquidity/PA, and BBO specs. | Campaign primary horizons include `10m`, but P03 locks only `fwd_ret_5m`. |
| `P15-G2` | `fwd_ret_15m` LabelPack binding | `aspec_a41dcccac5552de945aba825`; also required for full primary horizon matrix in accepted VWAP, regime, liquidity/PA, and BBO specs. | Campaign primary horizons include `15m`, but no P03 LabelPack record resolves and the inspected fixed-horizon label enum does not expose `fwd_ret_15m`. |
| `P15-G3` | `fwd_ret_30m` LabelPack binding | `aspec_fa4895a43a80d4eef0a607a4`; also required for full primary horizon matrix in accepted VWAP, regime, liquidity/PA, and BBO specs. | Campaign primary horizons include `30m`, but P03 locks only `fwd_ret_5m`. |
| `P15-G4` | Causal OHLCV derived FeaturePack binding for `VWAP`, `ANCHORED_VWAP`, `DISTANCE_TO_VWAP`, `OPENING_RANGE`, `RETURNS`, `ROLLING_VOLATILITY`, `ROLLING_RANGE`, `ATR`, `RANGE_POSITION`, `TRENDINESS`, `VOLUME_ZSCORE`, and fixed prior/compression range levels from completed bars | `aspec_8d9e272e4b78eedcd27f0bec`, `aspec_a41dcccac5552de945aba825`, `aspec_fa4895a43a80d4eef0a607a4`, `aspec_b40aee52d4399dd5b855a6ed`, `aspec_43cd6c154bca2fcc419eee83`, `aspec_eb962fc197eaf3955c5e4711`, `aspec_df2d040e45564c259ef3de6d`, `aspec_39ffc190cfbfa6ba0b1a2a25` | Existing OHLCV feature names or causal constructions are declared, but P03 locks no derived OHLCV FeaturePack member beyond session metadata. |
| `P15-G5` | BBO top-book confirmation FeaturePack binding for `SPREAD`, `SPREAD_TICKS`, `SPREAD_ZSCORE`, `TOP_BOOK_DEPTH`, `WIDE_SPREAD_FLAG`, `LOW_DEPTH_FLAG`, `MISSING_BBO_FLAG`, `BAD_QUOTE_FLAG` | `aspec_1284e49b083df11eeb0481ea` | The accepted BBO AlphaSpec is confirmation/risk-control only, but P03 locks no BBO DatasetVersion or BBO FeaturePack member. |

## No-Op Alternative

A strict no-op remains possible only if `FUTCORE-P14` constrains every
StudySpec to the locked `5m` label and the two locked session-context features,
and either defers or rejects the derived-OHLCV and BBO-dependent accepted specs.
That path would preserve the input-pack boundary but would not satisfy the
full accepted AlphaSpec set as written.

## Budget Outcome

The gap list has exactly 5 candidate P15 budget items. It does not exceed the
campaign cap, does not expand the universe, and does not request fragile `1m` or
`3m` labels as promotion-basis inputs.

P15 must still decide whether each item is feasible within its own spec and
must keep any implementation value-free in git, point-in-time, registry-bound,
and no-claims.
