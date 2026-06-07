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
| DatasetVersion | `dsv_databento_ohlcv_05404069799decb0` | Resolved by reference for ES/NQ/RTY 1 minute OHLCV bars; symbol-level row coverage remains a downstream observation because P13 does not read values. |
| FeaturePack | Eight base OHLCV/session primitives | All eight resolve through registry/resolver metadata and carry valid `available_ts` windows. |
| LabelPack | `fwd_ret_5m`, `fwd_ret_10m`, `fwd_ret_30m` | All three resolve and carry valid `label_available_ts` windows. |

## Audit Outcome

All accepted AlphaSpecs can bind the locked DatasetVersion and the available
base/session FeaturePack members by reference. `5m`, `10m`, and `30m` labels
resolve; `15m` does not.

The consolidated P15 gap list has five grouped budget items:

- `fwd_ret_15m`
- VWAP/session feature binding
- cross-market derived-state feature binding
- additional regime/liquidity base-OHLCV derived-state binding
- BBO top-book confirmation feature binding

The audit also flags stale FeatureVersion ids in accepted source drafts: P14
must bind the P03 session feature ids, not the older draft ids.

No primitive, FeatureRequest, LabelSpec, StudySpec, diagnostic, feature value,
label value, provider response, raw/canonical data file, local DB, review
artifact, verdict, PR, merge, or trading/broker surface is added by this phase.

## Carry Forward

`FUTCORE-P14` should bind only references that resolve through P03, or
explicitly defer specs/horizons that depend on the P15 gap list. `FUTCORE-P15`
owns any approved minimal primitive/request work. `FUTCORE-P16` and
`FUTCORE-P23` must still check cross-instrument timestamp alignment,
same-bar/no-lookahead handling, stale inputs, and symbol/session missingness
without reading or committing value rows in this audit phase.
