# Cost-Adjusted / Spread-Adjusted Label Family

`alpha_system.labels.families.cost_adjusted` defines the FLF-P18
cost-adjusted and spread-adjusted forward-return label family. It is
descriptive label substrate for offline research targets only. It does not
materialize label values, read raw provider files, call external providers,
persist registries, expose labels as live features, or make alpha, tradability,
profitability, broker, paper, live, or production claims.

## Governance Binding

Each family definition is built with
`build_cost_adjusted_label_definition(...)`, which consumes a governed
`alpha_system.governance.label_spec.LabelSpec` through
`LabelContractSpec.from_label_spec(...)`. The resulting contract adapts the
governed horizon, path rules, `cost_model`, target/stop rules,
`availability_time`, `forbidden_feature_overlap`, and `leakage_checks`.

No `lspec_` governance binding means no label definition. The family does not
define a second `LabelSpec` schema.

## Label Coverage

The FLF-P18 family covers:

- `cost_adjusted_fwd_ret`: BBO mid-to-mid forward return minus the governed
  spread fractions and explicit `fixed_cost_bps`.
- `spread_adjusted_fwd_ret`: BBO mid-to-mid forward return minus the governed
  spread adjustment only.

Both labels use exact-horizon terminal BBO rows. A missing exact-horizon row is
reported as a label gap; neighboring quotes are not used as replacements.

## Cost Model

`CostAdjustmentSpec` adapts the governance `LabelSpec.cost_model`. The family
requires explicit cost-model fields:

- `model="spread_plus_bps"` with `fixed_cost_bps` for
  `cost_adjusted_fwd_ret`;
- `model="spread_adjusted"` or `model="spread_plus_bps"` for
  `spread_adjusted_fwd_ret`;
- `spread_adjustment="half_spread_round_trip"` or
  `spread_adjustment="full_spread_round_trip"`, or
  `spread_adjustment="custom_fraction"` with `entry_spread_fraction` and
  `exit_spread_fraction`.

The adjustment is expressed as a return fraction from BBO `spread / mid` at the
entry and exact-horizon terminal quote. This is a documented friction
assumption for label construction, not a fill, execution, or portfolio model.

## BBO And Dense-Grid Semantics

The family consumes canonical BBO input views from
`alpha_system.features.input_views`. Quote validity is delegated to FLF-P04 BBO
semantics. Rows carrying `missing_bbo` or `bbo_quarantined`, rows with broken
`mid == (bid + ask) / 2`, or rows with broken `spread == ask - bid` produce
`None` label values with quality flags. They are not filled, interpolated, or
carried forward.

When dense-grid trade rows are supplied for anchor context, canonical
synthetic no-trade rows are flagged as label gaps with `synthetic_no_trade` and
`no_trade`; they are not treated as trade bars.

## Availability Boundary

Every returned `LabelValueRecord` carries `label_available_ts`. The timestamp is
the maximum of the horizon end, the exact terminal BBO row availability when a
terminal row exists, and the governed `LabelSpec.availability_time`.

The records are label-only outputs. They are not valid live feature inputs, and
the underlying `LabelContractSpec` preserves the governed
`forbidden_feature_overlap` and leakage checks.
