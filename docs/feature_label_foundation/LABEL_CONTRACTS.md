# Label Contracts

`alpha_system.labels.version` defines immutable metadata contracts for label
families, label versions, lineage, and value-row availability. The module is
contract-only: it does not calculate labels, materialize values, persist
registries, read raw provider files, call external providers, or expose labels
as live features.

## Object Catalogue

`LabelFamily` enumerates the planned label-family namespaces: fixed-horizon,
midprice-forward, cost-adjusted, path, and event labels.

`LabelInputSpec` declares the canonical input views and fields a label family
may read. Inputs are accepted DatasetVersion-derived canonical views, not raw
provider fields, and may carry DatasetVersion id references.

`LabelHorizonSpec` adapts the governed `LabelSpec.horizon` value and records the
declarative horizon-end rule.

`LabelPathSpec` adapts governed `LabelSpec.path_rules`. It may reference an
FLF-P07/FLF-P06 offline future `WindowSpec`; future windows are valid here only
because this is label contract metadata, not a live feature contract.

`BarrierSpec` adapts governed `LabelSpec.target_stop_rules`.

`CostAdjustmentSpec` adapts governed `LabelSpec.cost_model`.

`LabelAvailabilityPolicy` adapts governed `LabelSpec.availability_time`,
`forbidden_feature_overlap`, and `leakage_checks`. It records the
`label_available_ts` derivation rule and fixes forward-looking data legality to
`labels_only`.

`LabelContractSpec` is the central label-layer contract. It cannot be
constructed without a validated governance `LabelSpec` with an `lspec_` id. Its
component specs must match the governed horizon, path rules, cost model,
target/stop rules, availability time, forbidden feature overlap, and leakage
checks.

`LabelVersion` is a deterministic content-addressed id for the complete
`LabelContractSpec` payload.

`LabelValueRecord` is the value-row contract. It requires `label_version_id`,
entity id, event timestamp, horizon-end timestamp, `label_available_ts`, value,
a bound `LabelContractSpec`, and optional quality flags. It validates that the
version id matches the contract and that `label_available_ts` is not before
event time, horizon-end time, or the governed `LabelSpec.availability_time`.

`LabelLineageRecord` links a `LabelVersion` to its `LabelContractSpec`, governed
`lspec_` id, and contract provenance. It carries no materialized values.

## Governance Consumption

The label contracts consume the existing governance layer; they do not define a
second `LabelSpec` schema. `LabelContractSpec.from_label_spec(...)` validates the
governance record through `alpha_system.governance.label_spec`, copies a frozen
snapshot into the contract payload, and derives label contract components from
the governed fields.

The live-feature exclusion path delegates to
`alpha_system.governance.label_leakage_guard.check_label_leakage(...)`. A label
reference that matches `forbidden_feature_overlap`, or a feature reference whose
information time violates `availability_time`, is blocking. The contract layer
therefore adapts the existing `label_as_feature` and `availability_time` checks
instead of re-implementing leakage logic.

No `LabelSpec` means no `LabelContractSpec`; no `LabelContractSpec` means no
valid `LabelValueRecord`.

## Availability Rule

Every label value must carry `label_available_ts`. The policy rule is:

```text
label.label_available_ts = max(horizon_end_ts, path_rules terminal availability, LabelSpec.availability_time)
```

The contract layer does not compute label values, but it fails closed when a
value row omits `label_available_ts`, passes a null or naive timestamp, or uses
a `label_available_ts` before the governed availability boundary.

## Forward Data Boundary

Labels may describe future or forward-looking windows because labels are
offline supervised targets. This legality is confined to
`LabelAvailabilityConsumer.LABELS_ONLY`. The same future window remains invalid
for a live `FeatureSpec`, and label contracts expose
`validate_live_feature_references(...)` so callers can reject label-as-feature
and lookahead feature references through the governance guard.

The contract records `forbidden_feature_overlap` from the governed `LabelSpec`
so no label series, alias, or transform can be reused as a live feature input.

## LabelVersion Derivation

`LabelVersion.derive(spec)` serializes a canonical payload containing the
algorithm name and the complete `LabelContractSpec` dictionary, then hashes that
payload with SHA-256. The id is `lver_<64-hex-content-hash>`.

Equal contract content yields the same `LabelVersion` across runs and machines.
Any contract-content change, including a governed `LabelSpec` change, path rule,
input metadata, or availability-policy change, changes the content hash and
therefore the version id.

## Boundary

A valid `LabelContractSpec`, `LabelVersion`, `LabelValueRecord`, or
`LabelLineageRecord` is substrate metadata only. It does not imply an alpha,
tradable signal, profitable signal, production-readiness, promotion, backtest,
portfolio, broker, paper-trading, live-trading, order-routing, account, or
deployment capability.
