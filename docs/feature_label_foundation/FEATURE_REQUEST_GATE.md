# FeatureRequest Gate

`alpha_system.features.request_gate` is the Feature/Label layer gate from a
governed `FeatureRequest` to feature implementation work. It consumes existing
governance objects and guard results; it does not define a new request schema,
approval workflow, duplicate-exposure detector, registry, FeatureSpec, feature
family, or materialization path.

## Gate Semantics

The gate is fail-closed. A caller must provide a valid governance
`FeatureRequest` whose `feature_request_id` has the `freq_` prefix and whose
metadata has already passed `alpha_system.governance.feature_request`
validation. Missing requests, malformed mappings, unchecked duplicate notes,
invalid ids, and invalid approval statuses are rejected before any feature-layer
implementation permission is returned.

For every valid request, the gate invokes the governance duplicate-exposure
guard through `check_duplicate_exposure(...)` and applies the resulting guard
notes through `apply_duplicate_exposure_notes(...)`. The feature layer records
the result in the gate decision as a `DuplicateExposureReport`.

Only an `APPROVED` checked request is admitted. These statuses fail closed:

- `PENDING`
- `NEEDS_REVIEW`
- `BLOCKED_DUPLICATE`

An unavailable duplicate-exposure registry check also fails closed because the
feature layer cannot treat the request as clean without a successful guard
record. A blocking duplicate finding updates the governed request status through
the governance helper and is rejected as `BLOCKED_DUPLICATE`.

## Public Views

`DuplicateExposureReport` is an immutable feature-layer view over
`ExposureCheckResult`. It exposes:

- the governance registry status;
- the count of registry entries checked;
- any registry error string supplied by the guard;
- the duplicate/equivalent findings as `EquivalentFeatureGroup` values.

`EquivalentFeatureGroup` is an immutable view over `ExposureFinding`. It exposes
the governance finding kind, severity, matched registry reference, and
rationale. The matched registry reference is copied into a read-only mapping so
feature-layer callers can inspect it without mutating guard output.

These views add presentation only. They do not score, rank, merge, suppress, or
reinterpret duplicate/equivalent exposure findings.

## Consume, Do Not Duplicate

The gate imports and delegates to:

- `FeatureRequest`, `FeatureRequestApprovalStatus`, and
  `validate_feature_request` from
  `alpha_system.governance.feature_request`;
- `check_duplicate_exposure` and `apply_duplicate_exposure_notes` from
  `alpha_system.governance.duplicate_exposure`.

No module under `src/alpha_system/governance/` is modified by this phase. If the
governance validators reject a request or guard note payload, the feature gate
also rejects it. The feature layer does not create alternate governance states,
alternate ids, alternate approval rules, or alternate duplicate-exposure logic.

## Boundary

The request gate allows only implementation planning for a governed feature
request. It does not implement a concrete feature family, create a FeatureSpec
or FeatureVersion, materialize feature or label values, read raw provider data,
call external providers, write registry databases, or create broker, paper,
live, account, order-routing, strategy, backtest, portfolio, alpha,
tradability, profitability, or deployment behavior.

The broader Feature/Label boundary is unchanged: feature and label code consume
accepted DatasetVersions through the sanctioned DatasetVersion and canonical
record APIs, keep values local-only, and preserve governance as the source of
truth.
