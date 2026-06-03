# DATA-P04 Handoff - Read-Only API Boundary and Order-Method Kill Switch

## Scope Completed

Implemented the DATA-P04 read-only IBKR API boundary in
`alpha_system.data.foundation.ibkr`.

`IBKRReadOnlyApiBoundary` is the single data-module seam for IBKR API access.
It requires an `IBKRConnectionProfile` with `read_only_mode = true`, a validated
`DataAccessMode`, and a mapping of explicitly registered historical read-only
callables. It does not store or expose a generic IBKR API client, adapter,
broker object, account object, or order-capable object. The only low-level
method names it will dispatch are:

- `reqHistoricalData`
- `cancelHistoricalData`
- `reqHeadTimeStamp`
- `reqHistoricalSchedule`

The public Python wrappers are `request_historical_data()`,
`cancel_historical_data()`, `request_head_timestamp()`, and
`request_historical_schedule()`.

Implemented `ReadOnlyBoundaryViolation` as the fail-closed kill switch. The
boundary refuses any method name that implies broker, account, execution, order,
position, paper, live, portfolio, fill, or trading scope. It also refuses every
unknown method. Refusal raises immediately and logs an error with the refused
method name and reason. `ReadOnlyBoundaryViolation` also subclasses
`AttributeError`, so Python attribute checks see forbidden attributes as absent
while direct access still raises the phase-specific hard failure.

Implemented `DataAccessMode` in `alpha_system.data.foundation.sources` with the
required fields:

- `mode`
- `requires_env`
- `allows_external_api`
- `allows_raw_write`
- `allows_canonical_write`
- `ci_allowed`

Canonical mode semantics:

- `dry_run`: no external API, no raw write, no canonical write, CI allowed.
- `synthetic`: no external API, no raw write, synthetic canonical write allowed,
  CI allowed.
- `smoke`: external API allowed only when `ALPHA_DATA_PULL_AUTHORIZED`,
  `ALPHA_ALLOW_EXTERNAL_IBKR`, and `ALPHA_IBKR_READ_ONLY_MODE` are true; no raw
  or canonical write; CI forbidden.
- `authorized_pull`: external API and raw write allowed only when the smoke env
  gates plus `ALPHA_ALLOW_RAW_LOCAL_WRITE` are true; canonical write disabled;
  CI forbidden.

Unknown modes and tampered field combinations raise
`DataFoundationValidationError`. External-API modes fail before dispatch in CI.
No `DataAccessMode` grants broker, account, order, position, paper, live, or
trading authorization.

Created `docs/data_foundation/READ_ONLY_BOUNDARY.md` documenting the boundary,
kill switch, `DataAccessMode` gate, unreachable-order proof, and CI-never-
external rule.

Updated `README.md` with the compact DATA-P04 executor snapshot: the
`ibkr_read_only_boundary` gate is progressing with DATA-P04 executor scope
complete, active phase `DATA-P04`, next phase `DATA-P05 - Futures Instrument
Master and Contract Economics`, the new durable boundary/mode/doc surfaces, and
unchanged read-only historical-only safety boundaries.

## Unreachable-Order Proof

New unit tests under `tests/unit/data/` assert the boundary behavior:

- `test_read_only_boundary_exposes_only_historical_read_methods` confirms the
  boundary exposes only historical wrappers and forbidden concrete IB API method
  names are not attributes.
- `test_order_account_and_position_methods_fail_closed_when_reached` confirms
  direct attribute probes and dispatch attempts raise `ReadOnlyBoundaryViolation`
  and are logged.
- `test_read_only_boundary_rejects_forbidden_method_registration` confirms a
  forbidden method cannot be registered as a read-only callable.
- `test_read_only_boundary_rejects_unknown_ibkr_methods` confirms non-approved
  IBKR methods fail closed.
- `test_registered_historical_method_requires_external_enabled_mode` confirms an
  approved historical method still cannot run under `dry_run`, and only runs
  through a fake callable when `DataAccessMode.smoke()` and required env gates
  are supplied.
- `test_external_mode_boundary_is_forbidden_in_ci` confirms external-enabled
  boundary calls fail in CI before invoking a callable.
- `test_boundary_stores_no_generic_api_client_path` confirms the boundary has no
  public generic API, adapter, or client path.
- `test_external_data_access_modes_are_forbidden_in_ci` confirms
  `DataAccessMode` blocks external modes in CI.
- `test_external_data_access_mode_fails_closed_on_malformed_ci_env` confirms a
  malformed `CI` env value fails closed rather than being treated as non-CI.

## Explicit Staged File List

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

- `README.md`
- `docs/data_foundation/READ_ONLY_BOUNDARY.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P04.md`
- `src/alpha_system/data/foundation/__init__.py`
- `src/alpha_system/data/foundation/ibkr.py`
- `src/alpha_system/data/foundation/sources.py`
- `tests/unit/data/test_data_access_mode.py`
- `tests/unit/data/test_data_foundation_package_skeleton.py`
- `tests/unit/data/test_ibkr_read_only_boundary.py`

No `runs/**` path is included. `git add .` and `git add -A` were not used.

## Validation Results

- `git status --short` passed before handoff/staging and showed only DATA-P04
  commit-eligible changes in `README.md`, `src/alpha_system/data/foundation/`,
  `tests/unit/data/`, and `docs/data_foundation/READ_ONLY_BOUNDARY.md`.
- `python -m pytest tests/unit/data/test_data_access_mode.py tests/unit/data/test_ibkr_read_only_boundary.py tests/unit/data/test_data_foundation_package_skeleton.py tests/unit/data/test_ibkr_connection_profile.py -q`
  passed: `53 passed in 0.03s`.
- `python -m pytest tests/unit/data -q` passed after formatting:
  `132 passed in 0.08s`.
- `python -m compileall -q src/alpha_system/data tests/unit/data` passed with
  no output.
- `git grep -nE 'placeOrder|reqPositions|reqAccount|reqOpenOrders|reqExecutions' -- 'src/alpha_system/data' || echo "no order/account API surface in data module"`
  passed and printed `no order/account API surface in data module`.
- `python tools/verify.py --smoke` passed with no output.
- `python -m pytest tests/unit/data -q` passed for the recorded spec
  validation: `132 passed in 0.08s`.
- `test -f docs/data_foundation/READ_ONLY_BOUNDARY.md` passed with no output.
- `git ls-files runs` passed and returned empty.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` passed and
  returned empty.
- `git diff --cached --name-only` passed after explicit staging and returned
  exactly the staged file list documented above.
- `git diff --cached --name-only | grep '^runs/' && printf 'RUNS_STAGED\n' || printf 'NO_RUNS_STAGED\n'`
  passed after explicit staging and printed `NO_RUNS_STAGED`.
- `git diff --cached --check` passed after explicit staging with no output.

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
  order-routing path, real-time feed, production deployment artifact, or PR/merge
  artifact was added.
- `git ls-files runs` returned empty.
- Artifact audit commands for `data` and the concrete forbidden IBKR API method
  surface returned clean.
- Explicit staging only was used for the listed commit-eligible paths.

## Scope Boundaries

No order, account, position, broker, paper, live, real-time, order-routing, or
production execution surface was introduced. No external IBKR call, broker call,
paper trade, live trade, order route, credential read, raw real-data write,
canonical real-data write, provider response write, data pull, PR creation,
merge, deployment, Claude call, reviewer run, `review.md`, or `verdict.json` was
performed by the executor.

No alpha, profitability, tradability, broker-readiness, execution-readiness,
data-completeness, or production-readiness claim was introduced.
