# IBKR Connection Profile

`IBKRConnectionProfile` is the DATA-P03 record for local read-only historical
IBKR connection settings. It is a configuration and diagnostic object only. It
does not open a network connection, read credentials, assert market-data
coverage, or expose account, order, paper, live, or real-time behavior.

## Fields

The record carries exactly these fields:

- `host`
- `port`
- `client_id`
- `read_only_mode`
- `environment`
- `connection_timeout`
- `doctor_status`
- `validated_at`

Default values:

```text
host = 127.0.0.1
port = 4002
client_id = 201
read_only_mode = true
environment = local_wsl2
connection_timeout = 10.0
```

`validated_at` must be a timezone-aware timestamp. `doctor_status` is a
diagnostic mapping and records whether the DATA-P03 scaffold has validated the
configuration. In this phase, `probe_performed` and `external_call_performed`
must remain `false`.

## Environment

`IBKRConnectionProfile.from_env()` reads:

```text
ALPHA_IBKR_HOST
ALPHA_IBKR_PORT
ALPHA_IBKR_CLIENT_ID
ALPHA_IBKR_READ_ONLY_MODE
```

Unset variables use the defaults above. Invalid values fail closed with
`DataFoundationValidationError`. `ALPHA_IBKR_READ_ONLY_MODE=false` is rejected;
the DATA-P03 profile is always read-only historical.

## Windows Host / WSL2 Caveat

The default `127.0.0.1:4002` describes the intended local scaffold profile, not
a promise that WSL2 can reach a Windows-hosted TWS or IB Gateway process through
that address. Windows host, WSL2 networking, gateway binding, and firewall
settings can make the configured host unreachable.

The DATA-P03 connection doctor records the configured host and port and reports
`reachability = not_probed_scaffold`. It does not silently retry an alternate
host and does not guess a Windows host IP. Future external exercise phases own
any guarded reachability probe.

## Connection Doctor Scaffold

`run_connection_doctor()` validates:

- the profile fields;
- the client ID through `IBKRClientIdPolicy`;
- the read-only mode;
- the diagnostic status shape.

It returns a new `IBKRConnectionProfile` with `doctor_status.status =
configuration_validated` and `retry_target = None`. The scaffold performs no
external IBKR call, opens no socket, reads no credentials, and introduces no
broker/account/order surface.
