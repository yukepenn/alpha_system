# DATA-P07 Handoff - Historical Request Spec and Manifest

## Scope Executed

Implemented DATA-P07 request-planning records under
`src/alpha_system/data/foundation/requests.py`.

`HistoricalRequestSpec` now carries the required fields:

- `request_spec_id`
- `source_id`
- `symbol_root`
- `contract_ref`
- `sec_type`
- `exchange`
- `currency`
- `bar_size`
- `what_to_show`
- `use_rth`
- `duration`
- `end_datetime_policy`
- `start_ts`
- `end_ts`
- `chunk_policy`
- `client_id`

`HistoricalRequestManifest` now carries the required fields:

- `manifest_id`
- `batch_id`
- `request_specs`
- `chunk_count`
- `expected_coverage`
- `pacing_policy_id`
- `data_root`
- `created_by`
- `created_at`
- `manifest_hash`

Both records are frozen dataclasses and validate fail-closed. Request specs
reject missing fields, unknown roots, embedded payload references, unsupported
`sec_type`, exchange/currency mismatches against the instrument master,
non-boolean `use_rth`, naive timestamps, `end_ts < start_ts`, empty or
zero-valued `chunk_policy`, and unsafe client IDs. Manifests reject missing
fields, empty request sets, duplicate `request_spec_id` values, non-positive
`chunk_count`, too-small `chunk_count`, empty `expected_coverage`, invalid
`data_root`, and mismatched persisted `manifest_hash`.

## Manifest Hash

`manifest_hash` is computed by
`compute_historical_request_manifest_hash()` as a SHA-256 digest over stable
JSON content with sorted keys and compact separators. The hash body includes:

- schema id `alpha_system.historical_request_manifest.v1`
- `manifest_id`
- `batch_id`
- normalized `request_specs`
- `chunk_count`
- `expected_coverage`
- `pacing_policy_id`
- `data_root`
- `created_by`

`created_at` is excluded as wall-clock audit metadata, and `manifest_hash` is
excluded because it is the digest being computed. Determinism evidence:
`tests/unit/data/test_historical_requests.py` creates two manifests with
identical non-wall-clock content and different `created_at` values, then
asserts their hashes match and match a direct recomputation. Persisted
mismatched hashes are rejected.

## DATA-P03 Client ID Reuse

Request-spec client ID validation delegates directly to
`IBKRClientIdPolicy.default().validate_client_id()` from DATA-P03. The DATA-P03
policy was not edited or weakened. clientId `101` and `102` remain
hard-blocked, the data namespace remains `201-209`, and the default data client
remains `201`.

## Lifecycle Block

DATA-P07 encodes the lifecycle block in request-planning predicates:

- `plan_historical_request_transition()` validates
  `NOT_REQUESTED -> REQUEST_PLANNED` with a `HistoricalRequestSpec`.
- `require_validated_manifest_for_provider_pull()` fails closed unless a valid
  `HistoricalRequestManifest` exists before provider-pull preflight.
- `provider_pull_manifest_guard()` returns `True` only for a valid manifest and
  `False` for missing/invalid manifests.
- `authorize_historical_request_transition()` validates
  `REQUEST_PLANNED -> REQUEST_AUTHORIZED` with a validated manifest.

No external call is wired in this phase. The module imports no IBKR client,
opens no socket, performs no provider pull, writes no raw/canonical data, and
does not authorize a pull.

## Synthetic Sample

Added `templates/data/synthetic_historical_request_manifest.json`. It is a tiny
synthetic-only manifest for schema and validation examples. It sets
`synthetic: true`, `coverage_status: planned_only_not_requested`,
`real_coverage_claim: false`, and `authorization_claim: false`. It is not a
provider response, real coverage statement, raw/canonical data artifact, or
pull authorization.

## Documentation And README Snapshot

Added `docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md` documenting both
records, required fields, `manifest_hash`, the no-manifest-no-pull block, and
the synthetic-sample policy.

Updated `README.md` with a compact DATA-P07 snapshot: the
`request_and_storage` gate begins at DATA-P07; the active phase is DATA-P07;
the next phase is DATA-P08 - Pacing, Chunking, Retry, and Resume Ledger; and
the new durable records/docs/template and unchanged safety boundaries are
recorded without run-local paths or data-root contents.

## Validation Results

No checks were skipped.

| Command | Result |
| --- | --- |
| `git status --short` | Passed before handoff/staging; showed only DATA-P07 commit-eligible README/source/doc/template/test changes. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `174 passed in 0.11s`. |
| `test -f docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md` | Passed with no output. |
| `git ls-files runs` | Passed with empty output. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed with empty output. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed with empty output. |
| `git diff --check` | Passed with no output. |

Additional phase-local checks:

- `python -m pytest tests/unit/data/test_historical_requests.py -q` passed:
  `6 passed in 0.04s`.
- `python -m ruff format --check src/alpha_system/data/foundation/requests.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_historical_requests.py`
  passed: `3 files already formatted`.
- `python -m ruff check src/alpha_system/data/foundation/requests.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_historical_requests.py`
  passed: `All checks passed!`.

## Explicit Staged File Set

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

```text
README.md
docs/data_foundation/REQUEST_SPEC_AND_MANIFEST.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P07.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/requests.py
templates/data/README.md
templates/data/synthetic_historical_request_manifest.json
tests/unit/data/test_historical_requests.py
```

No `runs/**` path is included. `git add .` and `git add -A` were not used.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the staged set.
- No run-local handoff, review, verdict, checks, or repair artifact was staged.
- No raw data, canonical data, factor data, label data, cache data, provider
  response, account artifact, DB file, SQLite/WAL/journal file, log,
  Parquet/Arrow/Feather file, pickle, NumPy artifact, model artifact, secret,
  credential, or heavy artifact was produced or staged.
- The synthetic manifest is under `templates/data/`, tiny, and explicitly
  synthetic.
- Explicit staging only was used for the listed commit-eligible paths.

## Commit And Push Status

- Local executor commit was created.
- Push was attempted with `GIT_TERMINAL_PROMPT=0 git push origin HEAD`.
- Push failed because network DNS could not resolve GitHub:
  `fatal: unable to access 'https://github.com/yukepenn/alpha_system.git/': Could not resolve host: github.com`.
- No PR, merge, verdict, PASS marker, or reviewer artifact was created.

## Scope Boundaries

No broker, order, account, position, paper, live, real-time, production
deployment, provider pull, external IBKR call, credential read, real-data write,
alpha search, factor/label research, profitability claim, tradability claim, or
production-readiness claim was introduced.

Codex did not call Claude, run a reviewer, create `review.md`, create
`verdict.json`, create a PR, merge, or mark the phase PASS. Ralph owns review,
verdict parsing, done-checks, PR, CI, merge gate, and final phase outcome.
