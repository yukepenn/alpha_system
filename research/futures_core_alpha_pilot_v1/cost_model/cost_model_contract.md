# FUTCORE-P04 Cost Model Contract

Campaign: `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1`  
Phase: `FUTCORE-P04`  
Contract type: value-free cost model and session stress contract  
Recorded on: 2026-06-07

This contract pins the `CostModelVersion` and stress-profile ladder that later
StudySpecs, diagnostics, cost-stress consolidation, and reviewer artifacts must
cite. It defines policy, parameter names, units, and ordering relationships
only. It does not run the runtime `cost` tool, read BBO or market values,
compute slippage, resolve provider files, access broker/account data, or make
any profitability, tradability, capacity-proven, paper/live, production, or
capital-allocation claim.

## CostModelVersion

| Field | Contract value |
| --- | --- |
| `CostModelVersion` id | `cmv_futcore_pilot_three_layer_session_stress_v1` |
| Semantic version | `1.0.0` |
| Human description | Three-layer futures pilot cost contract with session-specific stress overlays for ES/NQ/RTY research diagnostics. |
| Campaign binding | `ALPHA_FUTURES_CORE_ALPHA_PILOT_V1` |
| Phase binding | `FUTCORE-P04` |
| Input-pack binding | `FUTCORE-P03` input pack lock, by id/hash only. |
| Layer set | hard transaction cost, spread crossing, slippage proxy. |
| Profile set | exactly `zero_cost`, `base`, `stress_1`, `stress_2`, `double_cost`. |
| Slippage semantics | proxy only; never realized slippage, market impact, broker fill quality, or tradability evidence. |
| Zero-cost boundary | `zero_cost` is diagnostic-only and `promotion_basis_allowed=false`. |

No other `CostModelVersion` id or cost-stress profile name is part of this
pilot contract unless a later reviewed phase explicitly supersedes this file.

## Locked Input-Pack Cross-Reference

This cost contract is bound to the `FUTCORE-P03` input lock only by ids and
hashes. It does not copy value rows or registry/database files.

| Surface | Locked id or hash |
| --- | --- |
| DatasetVersion id | `dsv_databento_ohlcv_05404069799decb0` |
| Dataset manifest hash | `abbf9ebbecfe97f2c4b31900d9ae44421549e08a65e90ec64e235a958c1d2d31` |
| Dataset code hash | `87fb8de7760c3635fb883948971bc12ee21ed64562713975bb20028ae3f92139` |
| Dataset config hash | `206bc27869bcedfde89e483828534c5778bb72cf7e66b69a9d3304c7e7f03b5b` |
| Dataset quality report hash | `7e46966bdc6921a0bb338097fa82ec94fcdf401e1913d81b288052bd6c9c66b4` |
| FeatureVersion id | `fver_c365f971fe0c25d435eed9233bc7caa30a07dd761f43c3f288316b3a74894b0f` |
| Feature value content hash | `sha256:58c42ab7515299d64ea4f90348290e88e3510849b3f31490a22f5a56638c7705` |
| FeatureVersion id | `fver_17dfceba75a9883d2f78fdca07ebd4f59a40c5e98d9d5503d5a853395eedd978` |
| Feature value content hash | `sha256:d953e7f4bd32998b0fc5d3db7e28b968dc25bf0896bc491b8fb5ba6442fc8278` |
| LabelVersion id | `lver_11d66acbdc1c7ebe9127d51387fed05aa897eb34d00e0c3f36898cd34c8af395` |
| Label value content hash | `sha256:abb5f53c7ede5f359a79541b237d71d44e79304ebbb6333a101a3c0588e32a9f` |
| Partition reference | `development_partition` |

The FeaturePack and LabelPack storage paths remain outside this contract. Later
data-contract audits must still confirm symbol-level coverage, partition
fitness, and any BBO-capable surface required by an approved StudySpec before
diagnostics rely on those inputs.

## Layer 1 - Hard Transaction Cost

Layer 1 models mandatory hard charges as reviewed parameters, not account
observations and not live fee data.

| Parameter | Unit | Contract rule |
| --- | --- | --- |
| `fee_schedule_ref` | text id | Reviewed schedule reference or placeholder; must not identify a live account. |
| `fee_schedule_effective_date` | date | Date attached to the reviewed schedule when supported. |
| `commission_per_side_per_contract` | account currency / contract / side | Broker commission placeholder; no account-specific amount is recorded here. |
| `exchange_fee_per_side_per_contract` | account currency / contract / side | Exchange fee placeholder; versioned/dated where later config supports it. |
| `clearing_fee_per_side_per_contract` | account currency / contract / side | Clearing fee placeholder. |
| `regulatory_fee_per_side_per_contract` | account currency / contract / side | Regulatory or NFA-style fee placeholder. |
| `other_hard_fee_per_side_per_contract` | account currency / contract / side | Optional reviewed fee bucket; must be named before use. |
| `hard_cost_round_turn_policy` | text enum | Declares whether downstream diagnostics aggregate one side or round turn. |
| `profile_hard_cost_multiplier` | symbolic multiplier | Selected by the stress profile ladder; no amount recorded here. |

Layer 1 is independent of realized fills. Downstream configs may populate these
parameters from reviewed offline references, but this contract records no fee
amount, tier, account, broker credential, or trading authorization.

## Layer 2 - Spread Crossing

Layer 2 defines how a BBO surface is used when a downstream StudySpec binds a
valid BBO-capable input. It records methodology only.

| Parameter | Unit | Contract rule |
| --- | --- | --- |
| `bid_price` | price | Best bid at the decision timestamp, if valid and point-in-time. |
| `ask_price` | price | Best ask at the decision timestamp, if valid and point-in-time. |
| `mid_price` | price | Midpoint derived from valid bid/ask only. |
| `spread_ticks` | ticks | Ask minus bid expressed in instrument tick units. |
| `crossing_side` | text enum | Aggressive buy crosses toward ask; aggressive sell crosses toward bid. |
| `spread_crossing_policy` | text enum | Half-spread from mid or full-spread side convention, declared by StudySpec/config. |
| `profile_spread_crossing_multiplier` | symbolic multiplier | Selected by the stress profile ladder; no spread value recorded here. |
| `missing_bbo_policy` | text enum | Mark missing/bad BBO explicitly and use the approved proxy fallback; never fabricate a spread. |

Valid BBO means bid/ask are present, ordered, point-in-time, and attached to the
same instrument/session decision context. Invalid, crossed, stale, or missing
BBO must be visible in diagnostics as a limitation or rejection reason. The
contract does not contain BBO observations or quoted spread values.

## Layer 3 - Slippage Proxy

Layer 3 is a bucketed adverse-slippage proxy. It is not realized slippage,
market impact, queue position, passive-fill probability, or broker fill quality.

| Parameter | Unit | Contract rule |
| --- | --- | --- |
| `slippage_proxy_bucket_id` | text id | Bucket key derived from reviewed dimensions such as instrument, session view, horizon zone, BBO availability, and liquidity/spread state. |
| `slippage_proxy_unit` | ticks or basis points | Unit must be declared by downstream config before use. |
| `slippage_proxy_base_amount` | symbolic parameter | Central bucket placeholder; no value recorded here. |
| `spread_sensitive_slippage_component` | symbolic parameter | Optional component that scales with valid `spread_ticks`; no spread value recorded here. |
| `adverse_selection_proxy_component` | symbolic parameter | Optional deterministic offline proxy component; must remain local and reviewed. |
| `capacity_proxy_cap` | participation or notional/contract proxy unit | Conservative local cap or haircut placeholder; not capacity proof. |
| `profile_slippage_multiplier` | symbolic multiplier | Selected by the profile ladder below. |
| `profile_capacity_proxy_haircut` | symbolic multiplier | Selected by the profile ladder below; stricter stress means no relaxed cap. |
| `session_slippage_overlay` | symbolic multiplier | Selected by the thin-session rules below. |
| `missing_bbo_slippage_fallback` | symbolic parameter | Approved fallback bucket for missing or unusable BBO; must be flagged. |

Downstream diagnostics may aggregate Layer 3 into cost-stress summaries, but any
such output remains a proxy sensitivity description. It cannot be used alone to
claim liquidity capacity, tradability, production readiness, or capital fitness.

## Stress Profile Ladder

The profile ladder has exactly five profiles. The non-zero profiles are ordered
from central to more conservative. Thin-session overlays are applied after the
profile selection for the affected session views.

For every non-zero profile, downstream config must declare the profile-specific
settings for `profile_hard_cost_multiplier`,
`profile_spread_crossing_multiplier`, `profile_slippage_multiplier`, and
`profile_capacity_proxy_haircut`. `zero_cost` disables these cost contributions
only for diagnostic contrast and still records the zero-cost boundary.

| Profile | Relationship | Promotion boundary |
| --- | --- | --- |
| `zero_cost` | Disables hard cost, spread crossing, and slippage proxy only for diagnostic contrast. | Diagnostic only; never a promotion basis; `promotion_basis_allowed=false`. |
| `base` | Central assumption for non-zero hard cost, spread crossing, and slippage proxy parameters. | May be reviewed as one required sensitivity, but never as standalone proof. |
| `stress_1` | Not less conservative than `base` for hard cost, spread crossing, slippage proxy, and capacity proxy. | Required stress sensitivity. |
| `stress_2` | Not less conservative than `stress_1` for hard cost, spread crossing, slippage proxy, and capacity proxy. | Required stress sensitivity. |
| `double_cost` | Upper stress bound; configured so modeled non-zero cost is the double-cost bound relative to `base` before thin-session overlays under the same inputs. | Required upper-bound sensitivity. |

`zero_cost` must never support `WATCH`, `CANDIDATE_RESEARCH`, survivor status,
or any favorable evidence claim. If an idea survives only under `zero_cost` or
fails to survive required non-zero profiles, later phases must flag it as
cost-fragile or reject/inconclusive according to their review policy.

## Thin-Session Stress Rules

The session views are inherited from `FUTCORE-P02`:
`full_session`, `RTH_only`, `ETH_only`, `ETH_evening`, `ETH_overnight`,
`pre_RTH`, `RTH`, `post_RTH`, and `RTH_with_ETH_context`.

The following views are thin-session views for this contract and must receive
stricter spread, slippage, and capacity treatment on every non-zero profile:
`ETH_only`, `ETH_evening`, `ETH_overnight`, `pre_RTH`, and `post_RTH`.

| Thin-session view | Required overlay rule |
| --- | --- |
| `ETH_only` | Apply an ETH thin-session overlay after the selected non-zero profile; spread and slippage penalties must not be lower than the comparable RTH bucket, and the capacity proxy cap must be stricter than the comparable RTH bucket. |
| `ETH_evening` | Inherit the `ETH_only` floor and use an evening ETH sub-bucket or overlay where downstream config supports it; never less conservative than `ETH_only`. |
| `ETH_overnight` | Inherit the `ETH_only` floor and use an overnight ETH sub-bucket or overlay where downstream config supports it; never less conservative than `ETH_only`. |
| `pre_RTH` | Apply a pre-RTH transition overlay; spread/slippage penalties must not be lower than the comparable RTH bucket, and capacity proxy caps must be stricter than RTH. |
| `post_RTH` | Apply a post-RTH transition overlay; spread/slippage penalties must not be lower than the comparable RTH bucket, and capacity proxy caps must be stricter than RTH. |

Additional thin-session rules:

- Thin-session overlays never reduce modeled cost or relax the capacity proxy.
- `1m` and `3m` horizons are execution-fragile diagnostics only; when combined
  with a thin-session view, downstream reports must show the stricter horizon
  and thin-session limitation.
- ETH evidence is research-in-scope but not trading-approved.
- `RTH_with_ETH_context` may use completed ETH context only as allowed by the
  session scope contract; if the modeled decision/execution view is RTH, the
  execution session overlay is RTH, while separate ETH-context limitations must
  remain visible.
- No modeled holding period may cross the exchange daily maintenance /
  trade-date break.
- Thin-session capacity outputs are capacity proxies only and must never be
  described as proven fill capacity or tradability.

## Downstream Application Order

Later phases that consume this contract should apply the model in this order:

1. Bind the approved StudySpec to the `FUTCORE-P03` input-pack ids and this
   `CostModelVersion` id.
2. Resolve the session view, horizon, instrument, and BBO availability from the
   approved point-in-time inputs.
3. Build Layer 1 hard-cost parameters from reviewed offline descriptors.
4. Build Layer 2 spread-crossing parameters from valid BBO or mark the approved
   missing-BBO fallback.
5. Build Layer 3 slippage-proxy bucket parameters and capacity proxy.
6. Select exactly one profile from `zero_cost`, `base`, `stress_1`, `stress_2`,
   or `double_cost`.
7. Apply any required thin-session overlay to non-zero profiles.
8. Emit cost sensitivity diagnostics and limitations without committing value
   rows or claiming alpha, tradability, or production readiness.

## Consumer Phases

- `FUTCORE-P05` must make AlphaSpec authors cite this contract rather than
  inventing ad hoc costs.
- `FUTCORE-P14` must bind approved StudySpecs to the `CostModelVersion` id and
  the exact profile ladder.
- `FUTCORE-P16` through `FUTCORE-P20` consume the profile ladder when diagnostics
  are later run through sanctioned runtime tools.
- `FUTCORE-P21` consolidates cost-stress and thin-session stress results and
  flags zero-cost-only, under-stressed, and thin-session-fragile outcomes.
- `FUTCORE-P22` carries the session x horizon implications into the broader
  matrix consolidation.
- `FUTCORE-P25` and later evidence/ledger phases must preserve the zero-cost
  diagnostic-only boundary and the proxy-only capacity language.

## Non-Goals Confirmed

- No runtime diagnostic or cost tool was run for this contract.
- No BBO, spread, fee, slippage, capacity, feature, label, or market value is
  recorded here.
- No raw/canonical provider data, Parquet value file, SQLite registry, provider
  response, heavy artifact, local database, run log, or cache is committed.
- No consumed `src/alpha_system/**` primitive is edited here.
- No live, paper, broker, order, account, deployment, strategy-readiness,
  profitability, tradability, production, or capital-allocation claim is made.
