# DATA-P06 Handoff - Contract Details Snapshot and Contract Discovery

## Scope Executed

Implemented DATA-P06 contract-details and dated-contract scaffolding under
`src/alpha_system/data/foundation/instruments.py`.

`FuturesContractRecord` now carries the campaign-required dated-contract fields:

- `contract_id`
- `root_symbol`
- `contract_month`
- `ib_symbol`
- `trading_class`
- `con_id`
- `last_trade_date_or_contract_month`
- `expiration`
- `multiplier`
- `exchange`
- `currency`
- `include_expired_support_status`

`ContractDetailsSnapshot` now carries the campaign-required snapshot fields:

- `snapshot_id`
- `contract_id`
- `raw_details_ref`
- `normalized_fields`
- `retrieved_at`
- `client_id`
- `source`
- `hash`

The foundation namespace also exports the DATA-P06 discovery scaffold:
`IncludeExpiredSupportStatus`, `ContractDiscoveryRequest`,
`ContractDiscoveryAvailabilityLogEntry`, `ContractDiscoveryResult`, and
`record_contract_discovery()`.

## Snapshot Design

`ContractDetailsSnapshot` is a frozen dataclass. It stores a `raw_details_ref`
reference only, such as a synthetic fixture reference or future local-only raw
object reference. It does not embed a raw provider payload.

`normalized_fields` is recursively frozen into immutable mappings and tuples.
The snapshot hash is a SHA-256 digest over:

- `contract_id`
- `raw_details_ref`
- `normalized_fields`
- `retrieved_at`
- `client_id`
- `source`

`snapshot_id` is intentionally excluded from the hash so two snapshot records
for the same content produce the same digest. `from_mapping()` requires all
required fields including `hash` and rejects mismatched hashes. Mutation
attempts fail through frozen dataclass behavior and immutable nested mappings.

`client_id` validation delegates to the DATA-P03 `IBKRClientIdPolicy`, so
`101`, `102`, and out-of-range ids fail closed. The accepted namespace remains
`201-209`.

## Dated Contract Design

`FuturesContractRecord` is a frozen dataclass for one dated futures contract.
It validates:

- root membership in the DATA-P05 instrument master (`ES`, `NQ`, `RTY`, `MES`,
  `MNQ`, `M2K`);
- `ib_symbol`, `multiplier`, `exchange`, and `currency` reconciliation against
  the root `InstrumentMasterRecord`;
- `contract_month` in `YYYY-MM` or futures month-code form;
- `con_id` as a positive integer or `None` until discovered;
- `expiration` as an ISO calendar date;
- `include_expired_support_status` as one of `not_checked`, `unknown`,
  `supported`, or `unsupported`.

The includeExpired support status defaults to `not_checked`, never silently to
`supported`.

## Discovery Scaffold

`record_contract_discovery()` is pure Python over declarative or synthetic
inputs. It performs no network I/O, opens no socket, and calls no IBKR client.

The discovery request accepts a root, `sec_type=FUT`, optional
`include_expired`, client id, and source label. It rejects invalid roots,
`CONTFUT`, and out-of-policy client ids.

The availability log records what was requested and what was discovered:

- `include_expired=True` with no supplied support status records `unknown`;
- omitted or false `include_expired` records `not_checked`;
- `supported` or `unsupported` requires `include_expired=True` and an
  `evidence_ref`.

The log entry has no history-depth field and makes no full-history or CME
economic-finality claim.

## Tests And Fixtures

Added `tests/unit/data/test_contract_discovery.py` covering:

- required-field and fail-closed validation for `FuturesContractRecord`;
- instrument-master reconciliation for root, multiplier, exchange, currency,
  and IB symbol;
- default includeExpired status of `not_checked`;
- stable content hashing for `ContractDetailsSnapshot`;
- persisted hash mismatch rejection;
- clientId `101` rejection through DATA-P03 policy;
- frozen snapshot and nested `normalized_fields` immutability;
- reference-only `raw_details_ref` rejection of embedded JSON-like payloads;
- discovery defaulting to `unknown` or `not_checked`, never assumed supported;
- evidence-required `supported` discovery;
- invalid root, `CONTFUT`, out-of-policy client id, and unsupported status
  assumptions.

Added the tiny synthetic fixture
`tests/fixtures/data/synthetic_contract_details_es_h5.json`. It is explicitly
synthetic and stores normalized contract details only; it is not a provider
response.

## Documentation And README Snapshot

Added `docs/data_foundation/CONTRACT_DISCOVERY.md` documenting:

- the dated contract record;
- the immutable content-addressed snapshot;
- clientId validation and reference-only raw details;
- discovered-not-assumed includeExpired availability logging;
- the no-live-call boundary;
- unchanged broker/order/account/paper/live/real-time and no-claims boundaries.

`README.md` was updated per the snapshot policy: campaign
`ALPHA_DATA_FOUNDATION_V1` is shown as progressed through DATA-P06 in gate
`futures_contract_master`; the next phase is `DATA-P07` - Historical Request
Spec and Manifest; new durable additions are `ContractDetailsSnapshot`,
`FuturesContractRecord`, the contract-discovery scaffold, and
`docs/data_foundation/CONTRACT_DISCOVERY.md`; safety boundaries remain
unchanged.

## Validation Results

No checks were skipped. One required full-repo lint command failed because the
repository has a pre-existing Ruff backlog outside the DATA-P06 touched files;
the phase-local touched Python files pass Ruff format and Ruff check.

| Command | Result |
| --- | --- |
| `git status --short` | Ran before handoff/staging; showed only expected DATA-P06 README/source/doc/test/fixture changes. |
| `python tools/verify.py --smoke` | Passed with no output. |
| `python -m pytest tests/unit/data -q` | Passed after final edits: `168 passed in 0.11s`. |
| `test -f docs/data_foundation/CONTRACT_DISCOVERY.md` | Passed with no output. |
| `git ls-files runs` | Passed; output empty. |
| `python tools/verify.py --lint` | Failed. Exact failure: `ruff format --check .` reported `202 files would be reformatted`; `ruff check .` reported `Found 1291 errors`. Reason: pre-existing repo-wide Ruff backlog outside this phase scope. |
| `python tools/verify.py --typecheck` | Passed: `compileall -q src tests tools`. |
| `python tools/hooks/canary_runner.py` | Passed; all Frontier canaries passed. |
| `find data -type f ! -name README.md ! -name ".gitkeep" -print` | Passed; output empty. |
| `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` | Passed; output empty. |
| `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` | Passed; output empty. |
| `git grep -nE "placeOrder\|reqAccount\|reqPositions\|reqMktData" -- src/alpha_system/data \|\| echo "no order/account/live API surface in data module"` | Passed; output: `no order/account/live API surface in data module`. |
| `python -m ruff format --check src/alpha_system/data/foundation/instruments.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_contract_discovery.py` | Passed: `3 files already formatted`. |
| `python -m ruff check src/alpha_system/data/foundation/instruments.py src/alpha_system/data/foundation/__init__.py tests/unit/data/test_contract_discovery.py` | Passed: `All checks passed!`. |
| `git diff --check` | Passed with no output. |

## Explicit Staged File Set

Files staged with explicit paths only and verified by
`git diff --cached --name-only`:

```text
README.md
docs/data_foundation/CONTRACT_DISCOVERY.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P06.md
src/alpha_system/data/foundation/__init__.py
src/alpha_system/data/foundation/instruments.py
tests/fixtures/data/synthetic_contract_details_es_h5.json
tests/unit/data/test_contract_discovery.py
```

Explicit staging discipline was used. `git add .` and `git add -A` were not
used. The run-local mirror
`runs/2026-06-03T215249Z_ALPHA_DATA_FOUNDATION_V1/phases/DATA-P06/handoff.md`
is local-only and must not be staged or committed.

## Artifact Policy Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the verified staged set.
- The `data` and `metadata` audits returned empty except allowed README
  placeholders.
- No raw data, canonical data, factor data, label data, cache data, provider
  responses, account artifacts, DB files, logs, Parquet/Arrow/Feather files,
  model artifacts, or heavy artifacts were produced or staged.
- The synthetic fixture under `tests/fixtures/data/` is tiny and explicitly
  synthetic.
- No external IBKR call, network provider pull, broker call, paper/live action,
  order routing, account access, real-time feed, or deployment was performed.

## Commit And Push Status

- Local executor commit was created.
- Push was attempted with `GIT_TERMINAL_PROMPT=0 git push origin HEAD`.
- Push failed because network DNS could not resolve GitHub:
  `fatal: unable to access 'https://github.com/yukepenn/alpha_system.git/': Could not resolve host: github.com`.
- No PR, merge, verdict, PASS marker, or reviewer artifact was created.

## Non-Goals Preserved

- No external IBKR call, contract-details request, or network I/O was
  performed.
- No continuous `CONTFUT` series was treated as dated-contract truth.
- No request spec, manifest, pacing, chunking, parser, canonical bars,
  sessions, rolls, quality, coverage, or dataset version was implemented.
- No broker/order/account/position/paper/live/real-time API surface was
  introduced.
- No alpha, profitability, tradability, production-readiness, full-history, or
  CME economic-finality claim was introduced.

## Review Status

Codex did not call Claude, run a reviewer, create `review.md`, create
`verdict.json`, create a PR, merge, or mark the phase PASS. Ralph owns review,
verdict parsing, done-checks, PR, CI, merge gate, and final phase outcome.
