# DATA-P03 Handoff - IBKR Connection Profile and Client ID Guard

## Scope Completed

Implemented fail-closed IBKR historical connection configuration in
`alpha_system.data.foundation.ibkr`.

`IBKRConnectionProfile` now carries the required fields:

- `host`
- `port`
- `client_id`
- `read_only_mode`
- `environment`
- `connection_timeout`
- `doctor_status`
- `validated_at`

The default profile is `host = 127.0.0.1`, `port = 4002`, `client_id = 201`,
`read_only_mode = true`, `environment = local_wsl2`, and
`connection_timeout = 10.0`. Construction raises
`DataFoundationValidationError` for invalid hosts, invalid ports, forbidden or
out-of-range client IDs, non-boolean or false `read_only_mode`, invalid
environment values, non-positive timeouts, malformed doctor status mappings,
and naive or missing `validated_at` timestamps. `from_env()` reads
`ALPHA_IBKR_HOST`, `ALPHA_IBKR_PORT`, `ALPHA_IBKR_CLIENT_ID`, and
`ALPHA_IBKR_READ_ONLY_MODE`, applying the campaign defaults when unset and
failing closed on malformed or unsafe values.

`IBKRClientIdPolicy` now carries the required fields:

- `forbidden_client_ids`
- `allowed_range`
- `default_client_id`
- `worker_client_ids`
- `collision_policy`

The policy hard-blocks clientId `101` and `102` with
`DataFoundationValidationError`; this is a hard validation error, not a
warning. The allowed data namespace is the inclusive range `201-209`, default
clientId is `201`, worker IDs are `ES=201`, `NQ=202`, `RTY=203`, and
`collision_policy = fail_closed`. Worker lookup fails closed for unknown
workers. Worker assignment validation fails closed when two workers share a
clientId, and requested-client collision checks fail closed when a requested
clientId is already active.

The connection-doctor scaffold validates the profile and clientId, then returns
a new `IBKRConnectionProfile` with `doctor_status.status =
configuration_validated`, `reachability = not_probed_scaffold`,
`probe_performed = false`, `external_call_performed = false`, and
`retry_target = None`. It does not import socket, does not import an IBKR client
library, does not call IBKR, opens no external connection, and performs no
silent wrong-host retry.

Created durable docs:

- `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`
- `docs/data_foundation/CLIENT_ID_POLICY.md`

Updated `README.md` with a compact DATA-P03 snapshot covering the active
campaign, active phase, next phase, new records/docs, and unchanged safety
boundaries.

## Explicit Staged File List

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

- `README.md`
- `docs/data_foundation/CLIENT_ID_POLICY.md`
- `docs/data_foundation/IBKR_CONNECTION_PROFILE.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P03.md`
- `src/alpha_system/data/foundation/ibkr.py`
- `tests/unit/data/test_ibkr_client_id_policy.py`
- `tests/unit/data/test_ibkr_connection_profile.py`

No `runs/**` path is included. `git add .` and `git add -A` were not used.

## Validation Results

- `git status --short` passed before staging and showed only DATA-P03
  commit-eligible changes:
  `README.md`, `src/alpha_system/data/foundation/ibkr.py`, the two
  `docs/data_foundation/` docs, and the two `tests/unit/data/` test files.
- `python -m pytest tests/unit/data/test_ibkr_client_id_policy.py tests/unit/data/test_ibkr_connection_profile.py -q`
  passed: `57 passed in 0.04s`.
- `python tools/verify.py --smoke` passed with no stdout.
- `python -m pytest tests/unit/data -q` passed: `111 passed in 0.07s`.
- `test -f docs/data_foundation/IBKR_CONNECTION_PROFILE.md` passed.
- `test -f docs/data_foundation/CLIENT_ID_POLICY.md` passed.
- `git ls-files runs` passed and returned empty.
- Pre-staging `git diff --cached --name-only` passed and returned empty.
- Pre-staging `find data -type f ! -name README.md ! -name ".gitkeep" -print`
  passed and returned empty.
- Pre-staging `find metadata -type f ! -name README.md ! -name ".gitkeep" -print`
  passed and returned empty.
- Pre-staging `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`
  passed and returned empty.
- `git diff --check` passed with no output.

No validation command was skipped.

## Artifact Policy

- `runs/**` remains local-only and was not staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  repair artifact was created or staged.
- No commit-eligible review artifact was created by the executor. The prompt
  explicitly forbids Claude calls, reviewer execution, `review.md`, and
  `verdict.json`; Ralph and the reviewer own those later YELLOW-lane steps.
- No raw data, canonical data, provider response, account information, local DB,
  cache, log, Parquet, Arrow, Feather, pickle, NumPy, model binary, credential,
  token, secret, heavy artifact, broker path, live path, paper path,
  order-routing path, real-time feed, or deployment artifact was added.
- `git ls-files runs` returned empty.
- Artifact audit commands for `data`, `metadata`, and non-fixture Parquet files
  returned empty.
- Explicit staging only was used for the listed commit-eligible paths.

## Scope Boundaries

No broker, order, account, position, paper, live, real-time, production
deployment, provider pull, external call, credential read, data write, alpha
search, factor/label research, profitability claim, tradability claim, or
production-readiness claim was introduced.

README snapshot update is factual and compact: it records DATA-P03 executor
snapshot scope, active/next phase context, the new durable records/docs, and the
unchanged safety boundaries without run details, local data contents, broker
behavior, alpha claims, or duplicated reviewer content.
