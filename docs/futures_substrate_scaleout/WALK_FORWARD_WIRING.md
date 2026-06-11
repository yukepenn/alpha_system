# Purged / Embargo Walk-Forward Wiring

`FUTSUB-P24` wires the existing experiment split primitives into runtime
diagnostics without changing the primitives themselves.

## Runtime Surface

The callable path is:

- `alpha_system.runtime.diagnostics.splits.build_walk_forward_split_plan`
- `alpha_system.runtime.diagnostics.splits.build_walk_forward_split_plan_for_observations`
- optional factor diagnostics argument `walk_forward_config=...`

The split-plan builder delegates to:

- `alpha_system.experiments.splits.walk_forward_splits`
- `alpha_system.experiments.splits.apply_purge_embargo`
- `alpha_system.experiments.splits.assert_chronological_split`

Every generated fold exposes `SplitWindow.to_dict()` metadata. This is
position-only metadata: split id, train indices, validation indices, purge gap,
and embargo gap. It does not embed market rows, feature values, label values,
provider payloads, local paths, or heavy artifacts.

## Protocol Hooks

The shared diagnostics contract exposes three protocol names through
`DiagnosticsHalfLifeProtocol`:

- `STRUCTURAL`
- `MEDIUM`
- `FAST`

The defaults are bounded sample-count configurations and are caller-overridable
through `WalkForwardSplitConfig` or an equivalent mapping. These names are
routing metadata only. They do not assert factor persistence, label
independence, statistical power, profitability, tradability, or promotion
eligibility.

## Fail-Closed Behavior

Walk-forward is opt-in for factor diagnostics. Existing callers that omit
`walk_forward_config` keep the prior report behavior.

When a caller requests walk-forward metadata, invalid geometry or too-small
input produces a visible `walk_forward_split_unavailable` rejection reason and
an inconclusive diagnostics report. The runtime does not silently fall back to
an unsplit evaluation path.

## Deferred Scope

`FUTSUB-P24` does not implement N_eff reporting, DSR, PBO, PSR, a
multiple-testing engine, a locked-test contamination ledger, portfolio-level
walk-forward, alpha ideation, promotion logic, or broker/live/paper behavior.
`FUTSUB-P25` owns overlap-aware N_eff reporting and the downstream Validation
Governance handoff owns the statistical correction scope.
