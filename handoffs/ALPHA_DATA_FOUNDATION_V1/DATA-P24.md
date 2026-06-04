# DATA-P24 Handoff - End-to-End Data Foundation Dry Run and Closeout

## Branch And Commit State

- Branch: `auto/alpha_data_foundation_v1/data-p24-end-to-end-data-foundation-dry-run-and-closeout`
- Commits by Codex in this execution: none. Files are prepared for explicit
  staging and Ralph-owned downstream validation/review/PR/merge gates.
- Phase outcome from Codex: `BLOCKED`, because the required broad verifier
  command `python tools/verify.py --all` failed outside the DATA-P24
  data-foundation scope. This handoff does not mark the phase `PASS`.

## Scope Executed

Implemented `src/alpha_system/data/foundation/dry_run.py`, a synthetic-only
dry-run driver that composes the existing data-foundation contracts. The driver
walks:

```text
source -> connection -> request/manifest -> pacing/chunk/resume
-> raw object metadata -> parsed bars -> canonical bars
-> quality/coverage -> dataset version -> optional registry round-trip
-> partitions
```

The default run uses `DataAccessMode.synthetic()` with
`allows_external_api = false`, clientId `201`, the existing tiny
`synthetic_ibkr_e2e_provider_fixture_v1` fixture, and the existing conservative
to-be-verified pacing policy. It performs no external IBKR call, no socket
probe, no real data pull, no raw write, and no canonical write.

The dry-run aggregate result was:

- status: `SYNTHETIC_COMPLETE`
- manifest: `hrm_synthetic_ibkr_e2e_v1`
- pacing policy: `rpp_ibkr_historical_conservative_tobeverified_v1`
- manifest chunk count: `1`
- completed ledger chunks: `1`
- pending resume chunks: `0`
- raw object metadata records: `1`
- parsed bars: `3`
- canonical bars: `3`
- quality status: `PASSING`
- coverage status: `PASSING`
- dataset version: `dsv_data_p24_synthetic_e2e_v1`
- external call attempted: `false`

## Lifecycle Blocks And Boundary Assertions

Added unit coverage in `tests/unit/data/test_data_foundation_dry_run.py` and
integration coverage in
`tests/integration/data/test_end_to_end_data_foundation_dry_run.py`.

The lifecycle-block assertions cover:

- missing manifest blocks provider-pull preflight;
- clientId `101` and `102` hard-block connection/profile validation;
- clientIds outside `201-209` fail closed;
- missing pacing guard blocks pull preflight and naive loops;
- missing `LocalDataRootPolicy` / raw layout policy blocks raw writes;
- missing `available_ts` blocks canonicalization;
- `available_ts < bar_end_ts` blocks canonicalization;
- quality gaps block dataset versioning;
- incomplete chunks block dataset versioning through coverage;
- `READY_FOR_TRADING`, `LIVE_FEED_READY`, `BROKER_ENABLED`,
  `ALPHA_VALIDATED`, and `PROFITABLE` are rejected lifecycle states;
- order/account/position/execution-style methods remain unreachable through
  the data module boundary.

## Documentation And Closeout

Added `docs/data_foundation/END_TO_END_DRY_RUN.md` with a curated synthetic
summary, lifecycle-block summary, and boundary interpretation policy.

Added `campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md` with final closeout
verdict `BLOCKED`. The blocker is the required broad verifier failure listed
below, not an in-scope DATA-P24 dry-run failure.

Updated `ACTIVE_CAMPAIGN.md` to show DATA-P24 as the final phase, no next phase
in this campaign, and the executor closeout verdict `BLOCKED`.

Updated `README.md` with a compact DATA-P24 snapshot and unchanged safety
boundaries. Updated `docs/data_foundation/README.md` to link the dry-run doc.

## Validation Results

No required validation command was skipped. One required command failed.

| Command | Result |
| --- | --- |
| `git status --short` | Passed; showed only DATA-P24 working-tree changes. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed: `344 passed in 0.30s`. |
| `python -m pytest tests/integration/data -q` | Passed: `9 passed in 1.16s`. |
| `python -m pytest tests/no_lookahead -q` | Passed: `61 passed in 0.37s`. |
| `python tools/verify.py --all` | Failed: `7 failed, 1704 passed in 24.07s`. Failures were `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` (`GitHubResult.dry_run` was `False`) and six `tests/test_ralph_driver.py` provider-wired/mock-resume tests where state/status was `PUSH_BLOCKED` instead of expected `STOPPED`, `PASS`, or `COMPLETED`. These failures are outside DATA-P24 allowed edit scope. |
| `test -f campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md` | Passed with no output. |
| `test -f docs/data_foundation/END_TO_END_DRY_RUN.md` | Passed with no output. |
| `python -m pytest tests/unit/data/test_data_foundation_dry_run.py -q` | Passed: `4 passed in 0.05s`. |
| `python -m pytest tests/integration/data/test_end_to_end_data_foundation_dry_run.py -q` | Passed: `2 passed in 0.29s`. |
| `PYTHONPATH=src python -m alpha_system.data.foundation.dry_run` | Passed; emitted aggregate JSON summary with `SYNTHETIC_COMPLETE` and `external_call_attempted: false`. Intentional boundary assertions also logged refused order/account method names. |
| `python -m ruff check src/alpha_system/data/foundation/dry_run.py tests/unit/data/test_data_foundation_dry_run.py tests/integration/data/test_end_to_end_data_foundation_dry_run.py` | Passed: `All checks passed!`. |
| `python -m ruff format --check src/alpha_system/data/foundation/dry_run.py tests/unit/data/test_data_foundation_dry_run.py tests/integration/data/test_end_to_end_data_foundation_dry_run.py` | Passed: `3 files already formatted`. |
| `git diff --check` | Passed with no output. |
| `git diff --cached --name-only` | Passed; matched the exact staged file set below. |
| `git diff --cached --name-only \| rg '^runs/'` | Passed by returning no matches; no `runs/**` path is staged. |
| staged forbidden-path grep | Passed by returning no matches for raw/canonical/cache/data, metadata, artifacts, DB, log, Parquet, Arrow, or Feather paths. |

An initial unrequired CLI probe,
`python -m alpha_system.data.foundation.dry_run`, failed before rerun because
the local source tree was not on `PYTHONPATH` (`ModuleNotFoundError:
No module named 'alpha_system'`).

## Artifact Audit

All required artifact-audit commands returned empty output:

```text
git ls-files runs
find data -type f '!' -name README.md '!' -name .gitkeep -print
find metadata -type f '!' -name README.md '!' -name .gitkeep -print
find artifacts -type f -size +1M -print
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

No raw data, canonical data, provider response, account information, local DB,
SQLite/WAL/journal file, log, cache, Parquet/Arrow/Feather file, model file,
secret, credential, heavy artifact, review artifact, verdict artifact, or
`runs/**` path was produced for commit.

## Exact Staged File Set

The exact explicit staged set for DATA-P24 is:

```text
ACTIVE_CAMPAIGN.md
README.md
campaigns/ALPHA_DATA_FOUNDATION_V1/CLOSEOUT.md
docs/data_foundation/END_TO_END_DRY_RUN.md
docs/data_foundation/README.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P24.md
src/alpha_system/data/foundation/dry_run.py
tests/integration/data/test_end_to_end_data_foundation_dry_run.py
tests/unit/data/test_data_foundation_dry_run.py
```

No `runs/**` path is included.

## Scope Boundary Confirmation

Codex did not call Claude, run a reviewer, create review artifacts, create
`review.md`, create `verdict.json`, create a PR, merge, mark the phase `PASS`,
perform a real IBKR pull, place orders, query account or position data, touch
broker/paper/live paths, deploy, or make alpha, profitability, tradability, or
production-readiness claims.

Ralph owns handoff validation, final validation disposition, independent
review, verdict parsing, semantic done-check, PR, CI, merge gate, merge, and
final phase outcome.

## Next Step

Ralph should treat DATA-P24 as blocked on the required broad verifier failure
unless the Workflow/GitHub driver failures are repaired or explicitly accepted
by the appropriate gate.
