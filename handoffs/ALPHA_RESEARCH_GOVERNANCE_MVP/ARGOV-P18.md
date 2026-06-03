# ARGOV-P18 Handoff - Synthetic End-to-End Governance Dry Run

## Summary

Implemented the ARGOV-P18 synthetic end-to-end governance dry run.

Added `tests/integration/governance/test_end_to_end_dry_run.py`, which composes
the existing governance objects, promotion gate, registry, CLI commands,
negative-control canary harness, and unsupported-claim guard. The test builds
one deterministic synthetic idea from
`tests/fixtures/governance/end_to_end/synthetic_lifecycle_fixture.json`, writes
temporary command JSON files under pytest's temp directory, persists governance
objects to a temporary SQLite registry, and discards all local runtime state.

No new governance object type, gate rule, canary type, generated-report runtime
surface, broker scope, live scope, paper scope, order-routing scope, real-data
ingestion, alpha search, or market-result claim was added.

## End-to-End Path

The dry run walks the synthetic idea through:

```text
HypothesisCard
  -> AlphaSpec
  -> FeatureRequest / LabelSpec
  -> StudySpec
  -> TrialLedgerRecord
  -> EvidenceBundle
  -> ReviewerVerdict
  -> PromotionDecision
```

Lifecycle states asserted through existing gates and registry/CLI surfaces:

- `DRAFT` - `HypothesisCard` validation and registry persistence.
- `REGISTERED` - `alpha governance validate-spec` and pre-registration gate.
- `IMPLEMENTATION_ALLOWED` - no-code gate plus duplicate-exposure and
  label-leakage guard clearance.
- `IMPLEMENTED` - implementation handoff reference gate.
- `DIAGNOSTICS_ALLOWED` - `StudySpec` diagnostics gate.
- `DIAGNOSTICS_RUN` - `TrialLedgerRecord` gate and CLI `register-trial`.
- `EVIDENCE_READY` - `EvidenceBundle` gate and CLI `build-evidence`.
- `REVIEWED` - independent `ReviewerVerdict` gate and CLI `review`.
- `CANDIDATE` - promotion gate and CLI `promote`.
- `VALIDATED` - promotion gate and CLI `promote`.

`CANDIDATE` and `VALIDATED` are governance-only states in this dry run. They do
not authorize live activity, capital allocation, order routing, deployment, or
broker activity.

## Gate Assertions

The integration test asserts that these missing-prerequisite and negative paths
fail closed:

- missing `AlphaSpec` blocks `IMPLEMENTATION_ALLOWED`;
- missing `StudySpec` blocks diagnostics;
- missing `TrialLedgerRecord` blocks diagnostics and promotion;
- missing `EvidenceBundle` blocks `CANDIDATE`;
- missing independent `ReviewerVerdict` blocks `VALIDATED`;
- reviewer self-approval is rejected;
- unrecorded locked-test contamination blocks promotion;
- failed-run omission blocks promotion;
- unsupported claim text is rejected by the claim guard;
- `LIVE_APPROVED`, `CAPITAL_ALLOCATED`, and `PRODUCTION_READY` remain
  unreachable and are rejected by the lifecycle parser.

## Negative Controls

The dry run asserts all required negative controls in guard-behavior terms:

- `random_target` through the catalogued `NegativeControlResult` contract;
- `future_shift` through the executable canary harness;
- `permuted_labels` through the executable canary harness;
- `optimistic_fill` through the executable canary harness;
- `python tools/hooks/canary_runner.py` reports all governance canaries as
  caught.

These canary results validate guard behavior only. They are not market evidence
and do not assert research quality.

## Documentation And README

Added `docs/governance/END_TO_END_DRY_RUN.md` as the curated dry-run summary.
Updated `docs/governance/README.md` to reference the new summary.

Updated the root `README.md` snapshot to record that ARGOV-P18 adds the
synthetic end-to-end governance dry run, that the active/next planned phase is
`ARGOV-P19 - Workflow 2 Integration, Acceptance Audit, and Closeout`, and that
the safety boundaries remain unchanged.

## Staged Files

Exact files staged explicitly:

```text
README.md
docs/governance/END_TO_END_DRY_RUN.md
docs/governance/README.md
handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P18.md
tests/fixtures/governance/end_to_end/README.md
tests/fixtures/governance/end_to_end/synthetic_lifecycle_fixture.json
tests/integration/governance/test_end_to_end_dry_run.py
```

No `runs/**` path is included.

## Validation Results

Spec-requested validation:

- `git status --short` - passed before staging with only allowed ARGOV-P18
  paths:

```text
 M README.md
 M docs/governance/README.md
?? docs/governance/END_TO_END_DRY_RUN.md
?? tests/fixtures/governance/end_to_end/
?? tests/integration/governance/test_end_to_end_dry_run.py
```

- `python tools/verify.py --smoke` - passed with exit 0 and no output.

- `python tools/verify.py --all` - initially failed with 7 existing
  Frontier/GitHub/Ralph driver test failures because the shell had live
  external-operation flags set:
  `FRONTIER_CREATE_PR=1`, `FRONTIER_ALLOW_AUTOMERGE=1`,
  `FRONTIER_MERGE_DRY_RUN=0`, and `FRONTIER_REAL_GITHUB_E2E=1`. The failed
  tests were:

```text
tests/test_github_utils.py::test_dry_run_pr_does_not_call_network
tests/test_ralph_driver.py::test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase
tests/test_ralph_driver.py::test_provider_mock_commit_updates_active_campaign_and_leaves_git_clean
tests/test_ralph_driver.py::test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase
tests/test_ralph_driver.py::test_mock_review_rework_then_repair_passes
tests/test_ralph_driver.py::test_resume_from_spec_ready_continues_without_regenerating_spec
tests/test_ralph_driver.py::test_resume_from_executed_continues_to_review
```

The new ARGOV-P18 governance integration test passed inside that failed full
suite run.

- Local-first rerun with those external-operation flags unset passed:

```bash
env -u FRONTIER_REAL_GITHUB_E2E -u FRONTIER_E2E_OWNER -u FRONTIER_E2E_DELETE_REPO -u FRONTIER_E2E_ARCHIVE_REPO -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_E2E_REPO_PREFIX -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE python tools/verify.py --all
```

Result:

```text
1350 passed in 23.33s
```

- `python -m pytest tests/unit/governance -q` - passed:

```text
503 passed in 2.98s
```

- `python -m pytest tests/integration/governance -q` - passed:

```text
7 passed in 5.74s
```

- `python tools/hooks/canary_runner.py` - passed:

```text
PASS governance_future_shift
PASS governance_permuted_labels
PASS governance_optimistic_fill
All Frontier canaries passed.
```

- `test -f docs/governance/END_TO_END_DRY_RUN.md` - passed with exit 0 and
  no output.

- `find artifacts -type f -size +1M -print` - passed with empty output.

- `git ls-files runs` - passed with empty output.

Supplementary validation:

- `python -m pytest tests/integration/governance/test_end_to_end_dry_run.py -q`
  - passed:

```text
1 passed in 2.03s
```

- `python -m ruff check tests/integration/governance/test_end_to_end_dry_run.py`
  - passed:

```text
All checks passed!
```

- `python -m json.tool tests/fixtures/governance/end_to_end/synthetic_lifecycle_fixture.json`
  - passed with exit 0.

Supplementary artifact audits:

- `find data -type f ! -name README.md ! -name ".gitkeep" -print` - passed
  with empty output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` -
  passed with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` -
  passed with empty output.
- `find . -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal"`
  - passed with empty output.

Skipped checks: none. Claude review, reviewer execution, `review.md`, and
`verdict.json` were not run or created by Codex because the executor prompt
reserves review and verdict handling for Ralph and the independent reviewer.

## Artifact Policy

`git ls-files runs` returned empty output. No run-local `handoff.md`,
`review.md`, `verdict.json`, `checks.json`, or repair artifact was created or
staged by Codex. No `runs/**` path is staged.

No raw data, canonical data, factor data, label data, cache data, SQLite/DB/WAL
file, Parquet, Arrow, Feather, log, generated report bundle, model binary,
credential, local environment file, or heavy artifact is staged.

The dry run writes temporary JSON files and a temporary SQLite registry only
under pytest's temp directory.

## Staging Discipline

Explicit staging only. `git add .`, `git add -A`, force push, PR creation,
merge, reviewer invocation, destructive cleanup, broker activity, live activity,
paper activity, order routing, production deployment, real-data ingestion, and
alpha search were not used.

Post-staging audit:

- `git diff --cached --name-only` - passed with exactly the staged set listed
  above.
- `git diff --cached --check` - passed with exit 0 and no output.
- `git diff --cached --name-only | rg '^runs/'` - passed with no matches.
- `git diff --cached --name-only | rg '(^data/(raw|canonical|factors|labels|cache)/|^metadata/|^artifacts/|\.(sqlite|sqlite3|db|db-journal|wal|parquet|arrow|feather|pkl|joblib|onnx|npy|npz|log)$|/cache/|/__pycache__/|/\.pytest_cache/)'`
  - passed with no matches.
- `git diff --name-only` - passed after explicit staging with empty output.
- `git status --short` - passed after explicit staging with only curated
  ARGOV-P18 paths:

```text
M  README.md
A  docs/governance/END_TO_END_DRY_RUN.md
M  docs/governance/README.md
A  handoffs/ALPHA_RESEARCH_GOVERNANCE_MVP/ARGOV-P18.md
A  tests/fixtures/governance/end_to_end/README.md
A  tests/fixtures/governance/end_to_end/synthetic_lifecycle_fixture.json
A  tests/integration/governance/test_end_to_end_dry_run.py
```

## Scope And Claims

No broker, live, paper, order-routing, production deployment, real-data
ingestion, alpha search, factor computation, label materialization, strategy
optimization, portfolio allocation, live approval, capital allocation, or
production status scope was introduced.

No alpha, profitability, tradability, or production-readiness claim was
introduced. The dry run validates governance gate composition and guard behavior
over synthetic fixtures only.
