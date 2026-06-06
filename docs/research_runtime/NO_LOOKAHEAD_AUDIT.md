# No-Lookahead Runtime Audit

`alpha_system.runtime.audit.NoLookaheadRuntimeAudit` is the Research Runtime
point-in-time integrity guard. It inspects resolved runtime metadata and scalar
probe outputs, then returns a visible `NoLookaheadAuditResult`.

An accepted audit result means only that the inspected run metadata is
point-in-time safe under this guard. It is not alpha validation, not strategy
validation, not a candidate, not promotion, and not evidence of tradability or
profitability.

## Inputs

The audit consumes resolved, value-free runtime objects and metadata:

- `RuntimeInputPack` feature and label pack handles from the input resolver;
- the decision timestamp for live feature availability ordering;
- optional `SignalProbeSpec` / `SignalProbeReport` fill-policy and fill-summary
  metadata from the signal probe runtime;
- optional resolved feature/label input metadata for row-level synthetic tests
  or later runtime adapters;
- optional live feature window metadata;
- partition scope and governance contamination metadata.

It does not resolve DatasetVersions, read FeatureStore or LabelStore values,
open raw provider files, import provider readers, calculate diagnostics, run a
probe, or call an external provider.

## Fail-Closed Checks

The audit rejects every violation class below with a structured reason:

- Feature inputs must carry `available_ts`, and `available_ts` must be ordered
  against `event_ts` and no later than the decision timestamp.
- Label inputs must carry `label_available_ts`, and it must be ordered against
  `event_ts` and any declared horizon end.
- Live feature or signal metadata must not expose label-valued fields, label
  refs, or label views.
- Live feature windows must be causal trailing windows. Centered and
  forward-looking windows are rejected; forward horizons remain legal only for
  labels.
- Signal-probe fills must not be same-bar optimistic. Fill policies must delay
  at least one bar, reports must expose zero same-bar fills, and supplied fill
  records must fill after their originating signal.
- `locked_test_candidate` and `latest_shadow_candidate` use requires recorded
  governance contamination metadata, and selection on those partitions is
  rejected.

## Result Shape

Failures remain visible. A rejected result carries
`NoLookaheadAuditReason` records with:

- `code`;
- `category` (`leakage_risk` or `blocked_by_policy`);
- `message`;
- `field`;
- `decision_state`;
- `expected`;
- `actual`.

`NoLookaheadAuditResult.runtime_entry_reasons` exposes the same failures in the
existing `RuntimeEntryReason` shape so later runtime decision-state work can
adapt them without hiding the failure.

## Boundary

The audit orchestrates and inspects existing runtime objects. It does not
duplicate research, diagnostics, cost, grid, governance, feature, label, or data
primitive math. It stores no observations, feature values, label values, market
data, provider responses, local database state, caches, logs, or heavy
artifacts.

The package is local-only and has no broker, live, paper, order, account,
provider-call, deployment, CLI, candidate creation, or promotion scope.
