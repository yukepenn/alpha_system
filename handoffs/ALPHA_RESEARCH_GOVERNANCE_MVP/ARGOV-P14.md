# ARGOV-P14 Handoff - No-Lookahead / Label Leakage / Optimistic Fill Canary Harness

## Summary

Implemented the ARGOV-P14 synthetic governance canary harness in
`alpha_system.governance.canaries.harness`.

The harness executes three deterministic, synthetic dry-run controls:

- `future_shift` - loads `evals/canaries/future_shift/synthetic_fixture.json`,
  invokes the label-leakage guard's availability-time check, and expects
  `guard_rejects_or_flags_future_shift_lookahead`.
- `permuted_labels` - loads
  `evals/canaries/permuted_labels/synthetic_fixture.json`, invokes the
  label-leakage guard's forbidden-feature-overlap check, and expects
  `guard_rejects_or_flags_permuted_label_signal`.
- `optimistic_fill` - loads
  `evals/canaries/optimistic_fill/synthetic_fixture.json`, invokes the
  conservative execution-assumption guards against same-bar optimistic timing
  and same-bar fill assumptions, and expects
  `guard_rejects_or_flags_optimistic_fill_assumption`.

Each executable canary uses the ARGOV-P13 catalog via
`expected_failure_for_canary_type(...)` and returns a validated
`NegativeControlResult` via `create_negative_control_result(...)`. The harness
does not add new canary types or change the `NegativeControlResult` contract.
`random_target` remains catalogued but is not executable in ARGOV-P14.

The synthetic fixtures are tiny metadata-only JSON files. They contain no real
data, raw/canonical/factor/label data, materialized labels, computed factors,
diagnostics output, research evidence, or market evidence.

## Fail-Closed Behavior

The harness records guard behavior explicitly:

- Guard catches the injected known-bad fault:
  `observed_result == expected_failure`, so `pass_fail == PASS`.
- Guard misses the injected known-bad fault:
  `observed_result != expected_failure`, so `pass_fail == FAIL`.

The missed-guard path is tested by injecting guard callables that return
`False`; those results are valid `NegativeControlResult` records with
`pass_fail == FAIL`. Guard exceptions are not converted into pass results.

## Canary Runner Integration

`tools/hooks/canary_runner.py` now appends three governance scenarios:

- `governance_future_shift`
- `governance_permuted_labels`
- `governance_optimistic_fill`

The existing Frontier safety scenarios remain present. No existing canary was
removed, skipped, relaxed, or weakened. Existing long string literals in the
runner were only wrapped without changing their content. The full canary runner
reports all existing scenarios and all three governance scenarios as `PASS`.

## Staged Files

Exact files staged by explicit path:

- `README.md`
- `docs/governance/CANARY_HARNESS.md`
- `docs/governance/NEGATIVE_CONTROLS.md`
- `docs/governance/README.md`
- `evals/canaries/future_shift/README.md`
- `evals/canaries/future_shift/synthetic_fixture.json`
- `evals/canaries/optimistic_fill/README.md`
- `evals/canaries/optimistic_fill/synthetic_fixture.json`
- `evals/canaries/permuted_labels/README.md`
- `evals/canaries/permuted_labels/synthetic_fixture.json`
- `handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P14.md`
- `src/alpha_system/governance/canaries/__init__.py`
- `src/alpha_system/governance/canaries/harness.py`
- `tests/no_lookahead/test_governance_canaries.py`
- `tests/unit/governance/test_canary_harness.py`
- `tools/hooks/canary_runner.py`

No `runs/**` path is staged.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging with only allowed ARGOV-P14
  paths:

```text
 M README.md
 M docs/governance/NEGATIVE_CONTROLS.md
 M docs/governance/README.md
 M evals/canaries/future_shift/README.md
 M evals/canaries/optimistic_fill/README.md
 M evals/canaries/permuted_labels/README.md
 M src/alpha_system/governance/canaries/__init__.py
 M tools/hooks/canary_runner.py
?? docs/governance/CANARY_HARNESS.md
?? evals/canaries/future_shift/synthetic_fixture.json
?? evals/canaries/optimistic_fill/synthetic_fixture.json
?? evals/canaries/permuted_labels/synthetic_fixture.json
?? src/alpha_system/governance/canaries/harness.py
?? tests/no_lookahead/test_governance_canaries.py
?? tests/unit/governance/test_canary_harness.py
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python -m pytest tests/unit/governance/test_canary_harness.py -q` -
  passed:

```text
..........                                                               [100%]
10 passed in 0.03s
```

- `python -m pytest tests/no_lookahead/test_governance_canaries.py -q` -
  passed:

```text
...                                                                      [100%]
3 passed in 0.02s
```

- `python -m pytest tests/unit/governance -q` - passed:

```text
........................................................................ [ 15%]
........................................................................ [ 30%]
........................................................................ [ 46%]
........................................................................ [ 61%]
........................................................................ [ 77%]
........................................................................ [ 92%]
..................................                                       [100%]
466 passed in 0.31s
```

- `python -m pytest tests/no_lookahead -q` - passed:

```text
..........................................................               [100%]
58 passed in 0.30s
```

- `python tools/hooks/canary_runner.py` - passed:

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

- `git ls-files runs` - passed with empty output.

- `find data -type f ! -name README.md ! -name ".gitkeep" -print` - passed
  with empty output.

- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` -
  passed with empty output.

- `find artifacts -type f -size +1M -print` - passed with empty output.

- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` -
  passed with empty output.

Supplemental formatting check:

- `python -m ruff check src/alpha_system/governance/canaries/harness.py src/alpha_system/governance/canaries/__init__.py tests/unit/governance/test_canary_harness.py tests/no_lookahead/test_governance_canaries.py tools/hooks/canary_runner.py`
  - passed:

```text
All checks passed!
```

No requested validation command was skipped.

Post-staging audit:

- `git diff --cached --name-only` - passed with exactly the staged files listed
  in this handoff.

- `git diff --cached --name-only | rg '^runs/'` - passed with no matches. The
  audited command reported:

```text
NO_RUNS_STAGED
```

- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/.*\.(sqlite|sqlite3|db|db-journal|wal)$|^artifacts/|\.(parquet|arrow|feather|pkl|onnx|npy|log)$)'`
  - passed with no matches. The audited command reported:

```text
NO_FORBIDDEN_ARTIFACTS_STAGED
```

- `git status --short` - passed after explicit staging with only curated
  ARGOV-P14 paths:

```text
M  README.md
A  docs/governance/CANARY_HARNESS.md
M  docs/governance/NEGATIVE_CONTROLS.md
M  docs/governance/README.md
M  evals/canaries/future_shift/README.md
A  evals/canaries/future_shift/synthetic_fixture.json
M  evals/canaries/optimistic_fill/README.md
A  evals/canaries/optimistic_fill/synthetic_fixture.json
M  evals/canaries/permuted_labels/README.md
A  evals/canaries/permuted_labels/synthetic_fixture.json
A  handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P14.md
M  src/alpha_system/governance/canaries/__init__.py
A  src/alpha_system/governance/canaries/harness.py
A  tests/no_lookahead/test_governance_canaries.py
A  tests/unit/governance/test_canary_harness.py
M  tools/hooks/canary_runner.py
```

## README Snapshot

`README.md` now records that ARGOV-P14 executor deliverables add the synthetic
no-lookahead, label-integrity, and optimistic-fill canary harness; identifies
`ARGOV-P15 - Governance Registry Integration` as the next phase; names the new
`alpha_system.governance.canaries.harness` module and
`docs/governance/CANARY_HARNESS.md`; and preserves the governance-only safety
boundary. It records no phase PASS verdict and no run-local details.

## Artifact Policy

Explicit staging was used by path. `git add .`, `git add -A`, force push,
destructive cleanup, run-local handoff staging, and `runs/**` staging were not
used. `git ls-files runs` returned empty output. No raw data, canonical data,
factor data, label data, cache, SQLite or DB file, log, generated report bundle,
Parquet, Arrow, Feather, model binary, credential, or heavy artifact path is
staged.

## Scope And Claims

No broker, live, paper, order-routing, real-data-ingestion, alpha-search,
strategy-optimization, portfolio-allocation, production-deployment, PR creation,
merge, reviewer invocation, `review.md`, or `verdict.json` scope was introduced.

The harness validates guard behavior only. It introduces no alpha validity,
profitability, tradability, capital-allocation, live-readiness, or
production-readiness claim.
