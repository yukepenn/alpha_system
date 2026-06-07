# Data Contract Audit

`FUTCORE-P13` maps the 10 accepted AlphaSpecs from the P12 critique/budget
audit to the locked `FUTCORE-P03` DatasetVersion, FeaturePack, and LabelPack
references.

Durable audit artifacts:

- `research/futures_core_alpha_pilot_v1/audits/data_contract/AUDIT.md`
- `research/futures_core_alpha_pilot_v1/audits/data_contract/gap_list.md`

## Locked Inputs

| Surface | Locked by P03 | P13 result |
| --- | --- | --- |
| DatasetVersion | `dsv_databento_ohlcv_05404069799decb0` | Resolved by reference for ES/NQ/RTY OHLCV 1 minute bars; coverage hash remains a downstream observation. |
| FeaturePack | `base_ohlcv_rth_flag`, `base_ohlcv_session_minute` | Both resolve through `FeatureLabelPackResolver` and carry non-empty `available_ts` windows. |
| LabelPack | `fwd_ret_5m` | Resolves through `FeatureLabelPackResolver` and carries a non-empty `label_available_ts` window. |

## Audit Outcome

All accepted AlphaSpecs can bind the locked DatasetVersion, the two
session-context FeaturePack members, and the locked `5m` LabelPack member by
reference. The full accepted set still has five bounded P15 gap budget items:

- `fwd_ret_10m`
- `fwd_ret_15m`
- `fwd_ret_30m`
- a grouped causal OHLCV derived FeaturePack binding
- a grouped BBO top-book confirmation FeaturePack binding

No primitive, FeatureRequest, LabelSpec, StudySpec, diagnostic, feature value,
label value, provider response, raw/canonical data file, local DB, review
artifact, verdict, PR, merge, or trading/broker surface is added by this phase.

## Carry Forward

`FUTCORE-P14` should bind only the references that actually resolve, or
explicitly defer specs/horizons that depend on the P15 gap list. `FUTCORE-P15`
owns any approved minimal primitive/request work. The safety boundary remains
research-only, evidence-only, registry-resolved, and no-claims.
