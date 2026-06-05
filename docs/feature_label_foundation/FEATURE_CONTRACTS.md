# Feature Contracts

`alpha_system.features.contracts` defines immutable metadata contracts for
feature specifications and feature versions. The module is contract-only: it
does not calculate features, materialize values, persist registries, read raw
provider files, call external providers, or create any broker/live/paper/order
scope.

## Object Catalogue

`FeatureFamily` enumerates the planned feature families: base OHLCV,
BBO/tradability, session/calendar/roll, cross-market, and liquidity/structure.

`FeatureInputSpec` declares the canonical input view names and fields a feature
may read. Inputs are canonical feature-layer views, not raw provider fields, and
may carry accepted DatasetVersion ids as references.

`TransformSpec` records the transform identity and JSON-compatible parameters.
It does not implement transform logic.

`WindowSpec` records the window kind, positive length, causality, offline-only
flag, anchor, and optional parameters. Centered and future windows must be
marked `offline_only`.

`NormalizationSpec` records the normalization identity, parameters, fit
partition policy, and optional contamination metadata. The default fit policy is
development/validation. `locked_test` is rejected unless governance
contamination metadata is supplied.

`FeatureSpec` is the central contract. It binds a feature id, `FeatureFamily`,
governed `freq_` FeatureRequest id, `FeatureInputSpec`, `TransformSpec`,
`WindowSpec`, `NormalizationSpec`, availability assumptions, an explicit
`available_ts` derivation rule, and live/offline eligibility metadata.

`FeatureVersion` is a deterministic content-addressed id for the complete
`FeatureSpec` contract payload.

`FeatureSetSpec` is the feature-layer bundle contract. Its namespace is fixed to
`features`, so it does not collide with the pre-existing
`alpha_system.experiments.feature_sets.FeatureSetSpec`.

`FeatureValueRecord` is the value-row contract. It requires
`feature_version_id`, entity id, event timestamp, `available_ts`, value, and
optional quality flags. This phase defines the record shape only; it produces no
feature values.

`FeatureLineageRecord` links a `FeatureVersion` to its `FeatureSpec`, bound
FeatureRequest id, and contract provenance. It carries no materialized values.

## Required Fields

Contract validation fails closed. `FeatureSpec` requires input, transform,
window, normalization, non-empty availability assumptions, and a non-empty
`available_ts` derivation rule. The bound request id must validate as a
governance `FeatureRequest` id with the `freq_` prefix.

`FeatureValueRecord.available_ts` is mandatory and must be a timezone-aware
`datetime`. Missing or null availability timestamps are invalid.

Metadata and parameter fields are frozen into deterministic JSON-compatible
structures so the contracts remain hashable and stable across runs.

## Availability Rule

Every `FeatureSpec` must state how output `available_ts` is derived from input
availability. The rule is declarative contract text, for example
`feature.available_ts = max(input.available_ts)`. Later materialization phases
must implement values only from validated specs and must retain the explicit
`available_ts` on every value row.

## Live And Offline Windows

Live feature contracts can use only causal windows that are not marked
offline-only. Centered and future windows are allowed only as offline-only
contracts and are rejected if attached to a live `FeatureSpec`.

This preserves the campaign boundary that centered/future windows are not valid
live feature inputs. Offline contracts still make no alpha, tradability, or
deployment claim.

## FeatureVersion Derivation

`FeatureVersion.derive(spec)` serializes a canonical payload containing the
algorithm name and the complete `FeatureSpec` contract dictionary, then hashes
that payload with SHA-256. The id is `fver_<64-hex-content-hash>`.

Equal contract content yields the same `FeatureVersion` across runs and
machines. Any contract-content change, such as a transform parameter or window
change, changes the content hash and therefore the version id.

## Governance Consumption

The contracts consume governance rather than duplicating it. `FeatureSpec`
validates only the governed request id shape directly. A spec can be marked
`implementation_eligible` only when the caller supplies an FLF-P05
`FeatureRequestGateDecision` whose decision admits implementation and whose
checked request id matches the spec.

The feature-contract layer does not define a new FeatureRequest schema,
approval workflow, duplicate-exposure detector, registry, or governance state.

## Boundary

A valid `FeatureSpec`, `FeatureSetSpec`, `FeatureVersion`, or
`FeatureLineageRecord` is substrate metadata only. It does not imply an alpha,
tradable signal, profitable signal, production-readiness, promotion, backtest,
portfolio, broker, paper-trading, live-trading, order-routing, account, or
deployment capability.
