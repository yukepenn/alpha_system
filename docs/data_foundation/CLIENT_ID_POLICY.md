# IBKR Client ID Policy

`IBKRClientIdPolicy` is the DATA-P03 fail-closed client ID guard for read-only
historical IBKR data configuration. It exists to prevent data pulls from
colliding with reserved non-data client sessions.

## Canonical Policy

The policy fields are:

- `forbidden_client_ids`
- `allowed_range`
- `default_client_id`
- `worker_client_ids`
- `collision_policy`

Canonical values:

```text
forbidden_client_ids = {101, 102}
allowed_range = 201-209
default_client_id = 201
worker_client_ids = ES=201, NQ=202, RTY=203
collision_policy = fail_closed
```

clientId `101` and `102` are hard-blocked with
`DataFoundationValidationError`. This is not a warning path and not a
best-effort policy. Any client ID outside `201-209` also fails closed.

## Worker Assignments

Default worker lookup is:

```text
ES  -> 201
NQ  -> 202
RTY -> 203
```

Unknown workers fail closed. Worker assignments are validated for uniqueness;
two workers sharing the same client ID raise `DataFoundationValidationError`.
Requested client IDs are also checked against an active-client set, and reuse of
an already active ID fails closed.

The policy does not claim that multiple workers are always safe. It only records
the campaign namespace and rejects known unsafe or colliding client IDs before a
future authorized historical data request can proceed.

## Boundary

This client ID policy is for historical data configuration only. It does not
authorize account access, order routing, paper trading, live trading, real-time
market data, production use, or alpha/tradability claims.
