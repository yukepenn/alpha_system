# DATA-P02 Handoff - Data Source Profiles and Local Data Root Policy

## Scope Completed

Implemented fail-closed data-source and local-data-root policy records in
`alpha_system.data.foundation.sources`.

`DataSourceProfile` now carries the required fields:

- `source_id`
- `provider_name`
- `provider_type`
- `allowed_modes`
- `forbidden_modes`
- `requires_authorization`
- `market_data_permissions_note`
- `created_at`

Construction raises `DataFoundationValidationError` on invalid field values,
empty mode sets, overlapping allowed/forbidden modes, non-boolean authorization
flags, invalid source IDs, provider types that imply forbidden capabilities,
allowed modes that imply broker/execution/order/account/paper/live/real-time
or completeness scope, and naive or missing timestamps. Missing required
constructor arguments fail through Python `TypeError`.

The IBKR source profile is exposed as `DataSourceProfile.ibkr_historical()`.
It uses `source_id = dsrc_ibkr_historical`, `provider_type =
historical_data_provider`, `requires_authorization = true`, and allowed modes
limited to:

- `historical_data`
- `read_only_historical`

Its forbidden modes include broker readiness, execution permission, orders,
order routing, account/account access, positions, paper trading, live trading,
real-time market data, and a data-completeness claim. The allowed and forbidden
mode sets are disjoint. The profile is a provider usage-boundary record only; it
does not imply broker readiness, execution permission, order/account access,
paper/live capability, real-time feed availability, data coverage, or data
completeness.

`LocalDataRootPolicy` now carries the required fields:

- `data_root`
- `must_be_local`
- `must_be_ignored`
- `forbidden_repo_paths`
- `allowed_subdirs`
- `max_file_policy`

`LocalDataRootPolicy.from_env()` reads `ALPHA_DATA_ROOT`, defaulting to
`~/alpha_data/alpha_system` when the environment variable is absent. Validation
is path-based and does not require the directory to exist. It rejects roots
inside the repository tree, roots under forbidden repo paths, Windows mounts
including `/mnt/c`, `/mnt/d`, and `/mnt/e`, cloud/synced path markers such as
OneDrive, Dropbox, Google Drive, and Windows-synced folders, network paths, and
temporary paths including `/tmp`, `/var/tmp`, and `/dev/shm`.

The default forbidden repo paths are:

- `data/raw`
- `data/canonical`
- `data/factors`
- `data/labels`
- `data/cache`
- `metadata`
- `artifacts`

The default allowed local-root subdirs are:

- `raw`
- `canonical`
- `manifests`
- `metadata`
- `quality`
- `coverage`

The default max-file policy requires `max_bytes_per_file` to be a positive
integer and `oversize_action = fail_closed`. `must_be_local` and
`must_be_ignored` must both be `true`. A missing local-data-root policy blocks
raw writes through `require_local_data_root_policy(None)`, which raises a hard
validation error before any write path can proceed.

Created durable docs:

- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`

Updated `README.md` with a compact DATA-P02 snapshot covering the active
campaign, active phase, next phase, newly added records/docs, and unchanged
safety boundaries.

## Explicit Staged File List

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

- `README.md`
- `docs/data_foundation/DATA_SOURCE_PROFILE.md`
- `docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md`
- `handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P02.md`
- `src/alpha_system/data/foundation/sources.py`
- `tests/unit/data/test_data_source_profiles.py`
- `tests/unit/data/test_local_data_root_policy.py`

No `runs/**` path is included. `git add .` and `git add -A` were not used.

## Validation Results

- `git status --short` passed before staging and showed only DATA-P02
  commit-eligible changes:
  `README.md`, `src/alpha_system/data/foundation/sources.py`, the two
  `docs/data_foundation/` docs, and the two `tests/unit/data/` test files.
- `python tools/verify.py --smoke` passed.
- `python -m pytest tests/unit/data -q` passed: `54 passed in 0.04s`.
- `test -f docs/data_foundation/DATA_SOURCE_PROFILE.md` passed.
- `test -f docs/data_foundation/LOCAL_DATA_ROOT_POLICY.md` passed.
- `python -c "import alpha_system.data"` failed with
  `ModuleNotFoundError: No module named 'alpha_system'`.
  Reason: this shell has not installed the src-layout package and the exact
  command does not set `PYTHONPATH`. Companion source-path import check
  `PYTHONPATH=src python -c "import alpha_system.data; import alpha_system.data.foundation"`
  passed.
- `git ls-files runs` passed and returned empty.
- `git diff --cached --name-only` passed and returned exactly the explicit
  staged file list above.
- `git diff --cached --check` passed with no output.
- `find data -type f ! -name README.md ! -name ".gitkeep" -print` passed and
  returned empty.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` passed
  and returned empty.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` passed and
  returned empty.

## Artifact Policy

- `runs/**` remains local-only and was not staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  repair artifact was created or staged.
- No raw data, canonical data, provider response, account information, local DB,
  cache, log, Parquet, Arrow, Feather, pickle, NumPy, model binary, credential,
  token, secret, heavy artifact, broker path, live path, paper path,
  order-routing path, real-time feed, or deployment artifact was added.
- `git ls-files runs` returned empty.
- Artifact audit commands for `data`, `metadata`, and non-fixture Parquet files
  returned empty.
- Explicit staging only was used for the listed commit-eligible paths.

## Commit And Push Status

- Local commit was created with message
  `ALPHA_DATA_FOUNDATION_V1/DATA-P02: Data Source Profiles and Local Data Root Policy`.
- `GIT_TERMINAL_PROMPT=0 git push -u origin auto/alpha_data_foundation_v1/data-p02-data-source-profiles-and-local-data-root-policy`
  failed with exit 128:
  `fatal: unable to access 'https://github.com/yukepenn/alpha_system.git/': Could not resolve host: github.com`.
  Reason: outbound DNS/network access to GitHub is unavailable in this execution
  environment. No force push was attempted.

## Scope Boundaries

No IBKR connection code, connection doctor, client ID policy, read-only API
boundary, order-method kill switch, provider call, external call, real-data
write, raw data lake, persistence integration, broker/order/account/paper/live
surface, real-time surface, alpha/factor/label/strategy work, profitability
claim, tradability claim, or production-readiness claim was introduced.

README snapshot update was factual and compact: it records DATA-P02 executor
snapshot scope, active/next phase context, the two durable records/docs, and the
unchanged safety boundaries without run details, local data contents, broker
behavior, alpha claims, or duplicated handoff content.
