# IBKR Read-Only Boundary

`DATA-P04` adds the read-only IBKR API boundary for the data foundation. The
boundary is local-first scaffolding only: it imports no IBKR client library,
opens no socket, reads no credentials, and performs no provider call.

## Boundary Design

`IBKRReadOnlyApiBoundary` is the single IBKR access seam exposed by
`alpha_system.data.foundation.ibkr`. It stores:

- an `IBKRConnectionProfile` that must have `read_only_mode = true`;
- a `DataAccessMode` runtime gate;
- a mapping of explicitly registered historical read-only callables.

The boundary does not store a generic IBKR API client, adapter, broker object,
or account object. Future connector code must register only approved historical
read callables through `read_only_methods`. Any registered method name outside
the approved surface fails closed at construction time.

The approved DATA-P04 method names are:

- `reqHistoricalData`
- `cancelHistoricalData`
- `reqHeadTimeStamp`
- `reqHistoricalSchedule`

These names are the only low-level method names the boundary dispatches. The
public Python wrappers are `request_historical_data()`,
`cancel_historical_data()`, `request_head_timestamp()`, and
`request_historical_schedule()`.

## Kill Switch

The kill switch is implemented by `ReadOnlyBoundaryViolation` and the boundary's
method validator. It refuses methods whose names imply broker, account,
execution, order, position, paper, live, portfolio, fill, or trading scope. It
also refuses every unknown method, even when the name is not recognized as one
of those categories.

Refusal is a hard raise, not a warning. Each refusal logs an error that includes
the requested method name and reason. `ReadOnlyBoundaryViolation` is also an
`AttributeError`, so normal Python attribute checks report forbidden methods as
absent while direct access still raises the phase-specific fail-closed error.

## DataAccessMode

`DataAccessMode` is an immutable record with the required fields:

- `mode`
- `requires_env`
- `allows_external_api`
- `allows_raw_write`
- `allows_canonical_write`
- `ci_allowed`

The canonical modes are:

| Mode | External API | Raw Write | Canonical Write | CI Allowed | Required Env |
| --- | --- | --- | --- | --- | --- |
| `dry_run` | false | false | false | true | none |
| `synthetic` | false | false | true | true | none |
| `smoke` | true | false | false | false | `ALPHA_DATA_PULL_AUTHORIZED`, `ALPHA_ALLOW_EXTERNAL_IBKR`, `ALPHA_IBKR_READ_ONLY_MODE` |
| `authorized_pull` | true | true | false | false | `ALPHA_DATA_PULL_AUTHORIZED`, `ALPHA_ALLOW_EXTERNAL_IBKR`, `ALPHA_IBKR_READ_ONLY_MODE`, `ALPHA_ALLOW_RAW_LOCAL_WRITE` |

Unknown modes and tampered field combinations raise
`DataFoundationValidationError`. External modes validate that required env flags
are true before an API call can proceed. No mode grants broker, account, order,
position, paper, live, or trading authorization.

## Unreachable-Order Proof

Unit tests under `tests/unit/data/` prove the boundary behavior:

- `test_read_only_boundary_exposes_only_historical_read_methods` verifies the
  boundary exposes only historical wrappers and that forbidden concrete IB API
  method names are not attributes.
- `test_order_account_and_position_methods_fail_closed_when_reached` verifies
  direct attribute access and dispatch attempts raise `ReadOnlyBoundaryViolation`
  and are logged.
- `test_read_only_boundary_rejects_forbidden_method_registration` verifies a
  forbidden method cannot be registered as a read-only callable.
- `test_read_only_boundary_rejects_unknown_ibkr_methods` verifies non-approved
  IBKR methods fail closed.
- `test_registered_historical_method_requires_external_enabled_mode` verifies an
  approved historical method still cannot run under `dry_run`.
- `test_external_mode_boundary_is_forbidden_in_ci` verifies external-enabled
  boundary calls fail in CI.
- `test_boundary_stores_no_generic_api_client_path` verifies the boundary has no
  public generic API, adapter, or client path.
- `test_external_data_access_modes_are_forbidden_in_ci` verifies `DataAccessMode`
  blocks external modes in CI.

## CI Rule

CI never allows external IBKR calls. `dry_run` and `synthetic` are CI-safe
because `allows_external_api = false`. `smoke` and `authorized_pull` set
`allows_external_api = true` and `ci_allowed = false`, so
`validate_runtime_env(..., ci=True)` fails before any registered callable can be
invoked.
