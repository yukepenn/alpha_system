# ARGOV-P08 Handoff — TrialLedger and Variant Accounting

## Summary

Implemented `TrialLedgerRecord` in
`alpha_system.governance.trial_ledger` as governance metadata only. The record
uses a frozen slots dataclass, the existing governance ID primitive, canonical
serialization, and fail-closed `GovernanceValidationError` validation.

The record carries the campaign-required fields:

- `trial_id`
- `alpha_spec_id`
- `study_spec_id`
- `run_id`
- `variant_id`
- `status`
- `parameters`
- `metrics_summary`
- `failure_reason`
- `oos_touched_flag`
- `locked_test_contamination_flag`
- `code_hash`
- `config_hash`

`trial_id` is a deterministic `trial_...` ID generated from the non-ID content
fields and verified during validation. `alpha_spec_id` and `study_spec_id` are
validated as `aspec_...` and `sspec_...` governance IDs. `run_id` is treated as
an opaque reference and rejects filesystem-style paths. `code_hash` and
`config_hash` are lowercase SHA-256 content hash strings.

`TrialStatus` is a closed `StrEnum` with `PLANNED`, `RUNNING`, `COMPLETED`,
`FAILED`, and `ABANDONED`. `FAILED` and `ABANDONED` require a substantive
`failure_reason`; non-failed statuses require `failure_reason` to be null or
empty. Empty `metrics_summary` remains explicit and is accepted for failed or
abandoned records without fabricating metrics.

Implemented `account_trial_ledger(...)` /
`evaluate_trial_ledger_accounting(...)` as pure metadata accounting. The helper
validates every supplied record, selects matching records for a `study_spec_id`,
counts every matching attempt, accumulates per-variant attempt counts, status
counts, failed/abandoned counts, and OOS/locked-test contamination counts. It
has no flag or default that omits failed or abandoned records. Empty matching
ledger input raises a validation error rather than returning clean zero-count
metadata. Observed variants are checked against the declared budget by reusing
`evaluate_variant_budget(...)` from `study_spec.py`.

Added `docs/governance/TRIAL_LEDGER.md` describing the record, field contract,
variant accounting, failed-run visibility, contamination flags, and the
`No TrialLedger -> no promotion` invariant. Updated the README snapshot for
`ARGOV-P08`, including the next phase `ARGOV-P09 — EvidenceBundle and Manifest
Contract` and the unchanged safety boundaries.

## Staged Files

Exact files staged after explicit staging:

- `README.md`
- `docs/governance/TRIAL_LEDGER.md`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P08.md`
- `src/alpha_system/governance/trial_ledger.py`
- `tests/unit/governance/test_trial_ledger.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` — passed before staging. Output:

```text
 M README.md
 M src/alpha_system/governance/trial_ledger.py
?? docs/governance/TRIAL_LEDGER.md
?? tests/unit/governance/test_trial_ledger.py
```

- `python -c "import alpha_system.governance.trial_ledger"` — failed with exit
  1:

```text
ModuleNotFoundError: No module named 'alpha_system'
```

  Reason: the current shell environment does not put `src/` on `sys.path` for a
  bare `python -c` invocation. This appears to be an environment/import-path
  setup issue rather than a module syntax issue: `PYTHONPATH=src python -c
  "import alpha_system.governance.trial_ledger"` passed with exit 0, and pytest
  uses `pyproject.toml` `pythonpath = ["src"]`.

- `python tools/verify.py --smoke` — passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_trial_ledger.py -q` — passed:

```text
.....................................................                    [100%]
53 passed in 0.03s
```

- `python -m pytest tests/unit/governance -q` — passed:

```text
........................................................................ [ 32%]
........................................................................ [ 65%]
........................................................................ [ 98%]
...                                                                      [100%]
219 passed in 0.13s
```

- `test -f docs/governance/TRIAL_LEDGER.md` — passed with exit 0 and no
  output.

- `git ls-files runs` — passed with empty output.

Additional local validation and inspection:

- `python -m ruff format --check src/alpha_system/governance/trial_ledger.py
  tests/unit/governance/test_trial_ledger.py` — passed:

```text
2 files already formatted
```

- `python -m ruff check src/alpha_system/governance/trial_ledger.py
  tests/unit/governance/test_trial_ledger.py` — passed:

```text
All checks passed!
```

- `python tools/verify.py --typecheck` — passed:

```text
+ /usr/bin/python -m compileall -q src tests tools
```

- `python tools/hooks/canary_runner.py` — passed:

```text
PASS forbidden_git_add_dot
PASS policy_doc_mentions_forbidden_command
PASS forbidden_test_tamper
PASS forbidden_secret
PASS forbidden_large_binary
PASS forbidden_destructive_op
PASS forbidden_boundary_import
PASS forbidden_raw_data_commit
PASS forbidden_cache_data_commit
PASS forbidden_local_artifacts
PASS forbidden_scope_drift
PASS generated_scaffold_allowed
All Frontier canaries passed.
```

- `find data -type f ! -name README.md ! -name .gitkeep -print` — passed with
  empty output.

- `find metadata -type f ! -name README.md ! -name .gitkeep -print` — passed
  with empty output.

- `find . -name '*.parquet' -not -path './tests/fixtures/*' -print` — passed
  with empty output.

- `git diff --check` — passed with exit 0 and no output.

- `python tools/verify.py --lint` — failed with exit 1 due existing repo-wide
  formatting/lint debt outside this phase. Current summary:

```text
193 files would be reformatted, 418 files already formatted
Found 1258 errors.
```

  The ARGOV-P08 touched files were formatted and passed the scoped ruff checks
  listed above.

Skipped checks: none of the spec-requested executor validation commands were
skipped. Claude review, reviewer execution, `review.md`, and `verdict.json`
were not run or created by Codex because the executor prompt reserves review
and verdict handling for Ralph and the independent reviewer.

## Artifact Policy

- `git ls-files runs` returned empty.
- `git diff --cached --name-only` contains no `runs/` path after explicit
  staging.
- The data, metadata, and Parquet artifact audits returned empty output.
- No forbidden data, raw/canonical/factor/label/cache data, local DB, DB
  journal, WAL, Parquet, Arrow, Feather, log, cache, model binary, heavy
  artifact, or run artifact is staged.
- No run-local `handoff.md`, `review.md`, `verdict.json`, `checks.json`, or
  `repair_attempts/` artifact was created or staged by Codex.

## Staging Discipline

- Explicit staging only.
- The staged set was built with explicit file paths.
- `git add .` was not used.
- `git add -A` was not used.
- No force push was performed.
- No commit was created by Codex in this executor step.
- No PR was created.
- No merge was performed.

## Scope Confirmation

- No broker, live, paper, order-routing, production deployment, PR creation, or
  merge scope was introduced.
- No diagnostics, studies, backtests, variant searches, factor computations,
  label computations, metric computations from market data, real-data
  ingestion, alpha search, strategy optimization, portfolio allocation, CLI, or
  registry persistence scope was introduced.
- No edits were made to forbidden broker/live/paper/order-router paths, data
  roots, metadata DB paths, artifact roots, or `runs/**`.
- Tests were added only under authorized governance paths. Existing tests were
  not weakened, skipped, deleted, or relaxed.
- No fixtures were added in this phase.
- No alpha, profitability, tradability, candidate, validated, factor-library,
  promotion-success, or production-readiness claim was introduced.
- No hidden-failure path exists in the accounting API: failed and abandoned
  records are validated and counted in matching attempt totals, status counts,
  variant attempt counts, and contamination metadata.
- The README snapshot was updated for `ARGOV-P08` and the next phase
  `ARGOV-P09`.
