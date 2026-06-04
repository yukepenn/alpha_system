# DATA-P13 Handoff - Roll Policy and Roll Calendar

## Branch and Commit Status

Branch:

```text
auto/alpha_data_foundation_v1/data-p13-roll-policy-and-roll-calendar
```

Local executor commit was created on this branch with the curated phase files.
Push status is recorded at the end of this handoff.

## Scope Completed

Implemented DATA-P13 roll-policy and roll-calendar records in
`src/alpha_system/data/foundation/rolls.py`.

`RollPolicy` is now a frozen, fail-closed record with the campaign-required
fields:

- `roll_policy_id`
- `method`
- `roll_trigger`
- `adjustment_method`
- `fallback_rule`
- `uses_volume`
- `uses_open_interest`
- `source`

Validation requires a closed roll method, closed trigger, method/trigger
consistency, trigger/volume/open-interest consistency, an explicit closed
`adjustment_method`, a closed fallback rule, boolean volume/open-interest flags,
and a `dsrc_` source that does not label the policy as provider-continuous or
claim exchange/CME finality unless reconciled.

`RollCalendarRecord` is now a frozen, fail-closed record with the
campaign-required fields:

- `roll_calendar_id`
- `root_symbol`
- `from_contract`
- `to_contract`
- `roll_date`
- `method`
- `evidence`
- `validation_status`

Validation requires `root_symbol` to be one of `ES`, `NQ`, `RTY`, `MES`,
`MNQ`, or `M2K` and present in the futures instrument master. `from_contract`
and `to_contract` must validate as DATA-P06 `FuturesContractRecord` identities,
must match the roll root, and must be distinct by `contract_id`; discovered
`con_id` values must also be distinct when both are present. `roll_date` must
be a date, `method` must be closed, `evidence` must be a non-empty mapping, and
`validation_status` must be one of `unvalidated`, `discovered`, or
`reconciled`.

## Adjustment, Evidence, and Non-Claims

Adjusted vs unadjusted state is explicit on `RollPolicy.adjustment_method`:

- `none` is the unadjusted state.
- `back_adjusted` and `ratio_adjusted` are adjusted states.

Missing or ambiguous adjustment values are validation errors. The
`adjusted_vs_unadjusted` property reports the distinction without implying a
price-adjustment computation.

Roll-calendar `method`, `evidence`, and `validation_status` are required.
`RollCalendarRecord.from_mapping()` rejects missing `method`, missing
`evidence`, missing `validation_status`, empty evidence, and unknown validation
status values. The record exposes conservative negative properties:
`describes_provider_continuous = False`,
`implies_provider_continuous_dated_truth = False`,
`implies_best_execution_roll = False`, and `implies_tradability = False`.

No field, method, helper, test, doc, or README text introduces a tradable roll,
best-execution roll, execution-quality claim, slippage model, fill model, order
timing rule, broker route, paper/live behavior, alpha claim, profitability
claim, or production-readiness claim.

## Continuous vs Derived/Stitched Separation

DATA-P13 keeps provider-continuous and derived/stitched dated-contract rolls
separate. `RollPolicy` and `RollCalendarRecord` reject provider-continuous,
`CONTFUT`, and continuous-as-dated-truth labels. A
`RollCalendarRecord` carries the derived roll provenance label
`derived_stitched_dated_contract_roll`; it does not transform provider
continuous history into dated-contract truth.

`RollCalendarRecord.validate_against_policy()` and
`require_roll_calendar_matches_policy()` fail closed unless the calendar method
matches a concrete `RollPolicy.method`.

## Documentation and README Snapshot

Added `docs/data_foundation/ROLL_POLICY.md`, documenting:

- `RollPolicy` and `RollCalendarRecord` field contracts;
- explicit adjusted vs unadjusted representation;
- required evidence and validation status;
- continuous-vs-derived roll separation;
- non-claims for execution quality, broker/order scope, alpha, profitability,
  tradability, and production readiness.

Updated `README.md` with a concise DATA-P13 snapshot: the
`provenance_sessions_rolls` gate is complete through the DATA-P13 executor
snapshot, `DATA-P14` - Parser and Parsed Bar Records is next, the new roll
module/doc are listed, and existing safety boundaries remain unchanged.

## Validation Results

No requested phase checks were skipped.

```text
git status --short
```

Result before handoff/staging:

```text
 M README.md
 M src/alpha_system/data/foundation/rolls.py
?? .claude/scheduled_tasks.lock
?? docs/data_foundation/ROLL_POLICY.md
?? tests/unit/data/test_roll_policy_calendar.py
```

`.claude/scheduled_tasks.lock` was pre-existing untracked local state and was
not touched or staged.

```text
python tools/verify.py --smoke
```

Result: passed with exit code 0 and no output.

```text
python -m pytest tests/unit/data/test_roll_policy_calendar.py -q
```

Result:

```text
17 passed in 0.04s
```

```text
python -m pytest tests/unit/data -q
```

Result:

```text
257 passed in 0.20s
```

```text
test -f docs/data_foundation/ROLL_POLICY.md
```

Result: passed with exit code 0 and no output.

```text
git ls-files runs
```

Result: passed with empty output.

```text
find data -type f ! -name README.md ! -name ".gitkeep" -print
```

Result: passed with empty output.

```text
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

Result: passed with empty output.

Because this phase replaces an exported data-foundation placeholder module with
shared validation behavior, the broader commands were also run.

```text
python -m ruff check src/alpha_system/data/foundation/rolls.py tests/unit/data/test_roll_policy_calendar.py
```

Result:

```text
All checks passed!
```

```text
python tools/hooks/canary_runner.py
```

Result:

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
PASS governance_future_shift
PASS governance_permuted_labels
PASS governance_optimistic_fill
All Frontier canaries passed.
```

```text
python tools/verify.py --all
```

Result: failed with exit code 1 in existing Workflow/GitHub tests, after the
DATA-P13 data tests passed inside the run.

Failing tests:

```text
tests/test_github_utils.py::test_dry_run_pr_does_not_call_network
tests/test_ralph_driver.py::test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase
tests/test_ralph_driver.py::test_provider_mock_commit_updates_active_campaign_and_leaves_git_clean
tests/test_ralph_driver.py::test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase
tests/test_ralph_driver.py::test_mock_review_rework_then_repair_passes
tests/test_ralph_driver.py::test_resume_from_spec_ready_continues_without_regenerating_spec
tests/test_ralph_driver.py::test_resume_from_executed_continues_to_review
```

Representative output:

```text
FAILED tests/test_github_utils.py::test_dry_run_pr_does_not_call_network - AssertionError: assert False
FAILED tests/test_ralph_driver.py::test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase - AssertionError: assert 'PUSH_BLOCKED' == 'STOPPED'
FAILED tests/test_ralph_driver.py::test_provider_mock_commit_updates_active_campaign_and_leaves_git_clean - AssertionError: assert 'PUSH_BLOCKED' == 'PASS'
FAILED tests/test_ralph_driver.py::test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase - AssertionError: assert 'PUSH_BLOCKED' == 'COMPLETED'
======================= 7 failed, 1603 passed in 23.05s ========================
```

Environment observed after the failure:

```text
FRONTIER_ALLOW_AUTOMERGE=1
FRONTIER_CREATE_PR=1
FRONTIER_MERGE_DRY_RUN=0
FRONTIER_REAL_GITHUB_E2E=1
```

The failures are in pre-existing Workflow/GitHub behavior under real-PR/push
environment variables and are outside DATA-P13 roll-policy scope. The
DATA-P13-specific test and all `tests/unit/data` tests passed.

## Explicit Staging Set

Curated commit-eligible paths for explicit staging:

```text
README.md
docs/data_foundation/ROLL_POLICY.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P13.md
src/alpha_system/data/foundation/rolls.py
tests/unit/data/test_roll_policy_calendar.py
```

No `runs/**` path is included. `git add .` and `git add -A` were not used.
No run-local `handoff.md`, `review.md`, `verdict.json`, or repair artifact was
created or staged.

## Artifact and Scope Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the curated staging set.
- No raw data, canonical data, factor data, label data, cache data, provider
  response, account artifact, SQLite/DB/WAL file, log, Parquet, Arrow, Feather,
  model artifact, secret, credential, or heavy artifact was created or staged.
- No tiny synthetic fixture or config file was needed for this phase.
- No external IBKR/provider data call, provider pull, data pull, IBKR
  connection, broker operation, order routing, account access, position access,
  paper trading, live trading, real-time behavior, production deployment, PR
  creation, merge, Claude call, reviewer call, review artifact, `review.md`,
  `verdict.json`, or phase PASS marking was performed.
- No broker/order/account/paper/live surface or order API was added under
  `src/alpha_system/data/**`.
- No parser, canonical-bar construction, quality/coverage report,
  dataset-version registry, alpha, factor, label, strategy, ML, portfolio,
  profitability, tradability, or production-readiness scope was introduced.

## Risks and Caveats

- `python tools/verify.py --all` failed in existing Workflow/GitHub tests when
  real PR/push environment variables were present. The requested DATA-P13 and
  data-foundation validation commands passed.
- No real roll calendar was produced. The new records validate policy/calendar
  metadata only and intentionally do not stitch, adjust, or certify real data.
- No optional synthetic roll config was added; the unit tests construct tiny
  synthetic contract identities directly.

## Review Request Focus

Please focus review on:

- fail-closed construction of `RollPolicy` and `RollCalendarRecord`;
- missing `method`, `evidence`, and `validation_status` as hard errors;
- adjusted vs unadjusted explicitness through `adjustment_method`;
- distinct dated `FuturesContractRecord` transition validation;
- provider-continuous vs derived/stitched roll separation;
- absence of tradable-roll, best-execution, broker/order/account/paper/live,
  alpha, profitability, or production-readiness claims;
- artifact-policy compliance and the `verify --all` caveat.

## Next Recommended Step

Ralph should validate this handoff and route the required fresh semantic review.
Codex did not create a review, verdict, PR, merge, done-check, or PASS marker.

## Commit and Push Status

- Local executor commit was created on branch
  `auto/alpha_data_foundation_v1/data-p13-roll-policy-and-roll-calendar`.
- Push was attempted with `GIT_TERMINAL_PROMPT=0 git push origin HEAD`.
- Push failed because network DNS could not resolve GitHub:

```text
fatal: unable to access 'https://github.com/yukepenn/alpha_system.git/': Could not resolve host: github.com
```

No force push, PR, merge, reviewer call, verdict, or PASS marking was
performed.
