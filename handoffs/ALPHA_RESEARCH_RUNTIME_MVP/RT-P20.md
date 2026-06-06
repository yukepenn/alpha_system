# ALPHA_RESEARCH_RUNTIME_MVP / RT-P20 Handoff

## Scope Summary

Implemented RT-P20 as tests, fixtures, and docs only. No runtime source,
consumed primitive package, CLI, broker/live/paper/order/account path,
`ACTIVE_CAMPAIGN.md`, review artifact, PR, merge, staging, commit, push, or
provider/reviewer call was created or run by Codex.

The run-local `runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P20/spec.md`
file was absent in this worktree, so the generated spec supplied in the
executor prompt was used as the active phase contract.

## Exact File List for Ralph Explicit Staging

Codex left these files unstaged, per executor instructions. Ralph should stage
only the curated paths below if it proceeds:

- `README.md`
- `docs/research_runtime/FIXTURES.md`
- `docs/research_runtime/TESTING.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P20.md`
- `tests/fixtures/runtime/fail_closed/README.md`
- `tests/fixtures/runtime/fail_closed/invalid_shortcuts.json`
- `tests/no_lookahead/research_runtime/test_rt_p20_fixture_no_lookahead.py`
- `tests/unit/runtime/fail_closed/test_runtime_fail_closed.py`

No `runs/` path is included. No review path is included.

## Git Status

`git status --short` was not run. The executor prompt explicitly forbade Codex
from running `git status`, `git diff`, `git add`, `git commit`, or `git push`.

No staging was performed by Codex. Because this executor did not stage files,
there is no Codex-created staged set containing forbidden paths. Ralph owns the
authoritative staging audit.

## Fixture Inventory

All runtime fixture files are tiny and synthetic. `find tests/fixtures/runtime
-type f -size +1M -print` returned empty output.

Per-file sizes from `find tests/fixtures/runtime -type f -printf '%p %s\n'`:

- `tests/fixtures/runtime/cost/README.md` - 173 bytes
- `tests/fixtures/runtime/cost/synthetic_fills_no_bbo.json` - 204 bytes
- `tests/fixtures/runtime/cost/synthetic_fills.json` - 330 bytes
- `tests/fixtures/runtime/fail_closed/README.md` - 612 bytes
- `tests/fixtures/runtime/fail_closed/invalid_shortcuts.json` - 5066 bytes
- `tests/fixtures/runtime/probe/README.md` - 408 bytes
- `tests/fixtures/runtime/probe/synthetic_signal_probe_rows.json` - 1761 bytes
- `tests/fixtures/runtime/diagnostics/cross_market/README.md` - 233 bytes
- `tests/fixtures/runtime/diagnostics/cross_market/synthetic_observations.json` - 2781 bytes
- `tests/fixtures/runtime/diagnostics/splits/README.md` - 202 bytes
- `tests/fixtures/runtime/diagnostics/splits/synthetic_observations.json` - 2072 bytes

Attestation: RT-P20 fixtures are hand-written synthetic metadata/scalar
fixtures only. They contain no real market data, provider responses, raw data,
canonical data, feature/label tables, runtime output values, alpha evidence, or
profitability/tradability evidence.

## Fail-Closed Scenario Coverage

- Missing `AlphaSpec` / `StudySpec` references:
  `evaluate_runtime_entry_request` returns `INPUTS_BLOCKED` with visible
  `missing_alpha_spec_ref` / `missing_study_spec_ref` reasons.
- Non-admissible `DatasetVersion` lifecycle:
  `resolve_runtime_input_pack` blocks `DRAFT`, calls the sanctioned
  DatasetVersion resolver, and does not produce an input pack; direct
  `RuntimeInputPack` construction with `DRAFT` also raises.
- Missing feature `available_ts` / label `label_available_ts`:
  `FeatureLabelPackResolver` plus `resolve_runtime_input_pack` returns
  `INPUTS_BLOCKED`; no-lookahead fixture tests also reject these shapes.
- Label value exposed as live feature:
  label-version-as-feature refs, live feature specs containing `label_value`,
  and live feature fixture inputs are blocked/rejected.
- Same-bar optimistic signal probe fill:
  `FillPolicy(delay_bars=0, allow_same_bar_fill=True)` raises, and
  `NoLookaheadRuntimeAudit` rejects same-bar report/fill metadata.
- Unbounded grid / `VariantBudget` exceeded:
  `validate_bounded_grid_request` returns a visible `BoundedGridRunRecord` with
  `GUARD_REJECTED`.
- Locked-test partition without metadata / locked-test selection:
  `resolve_runtime_input_pack` returns `INPUTS_INCONCLUSIVE` for missing
  contamination metadata and `INPUTS_BLOCKED` for locked-test selection;
  no-lookahead fixture tests reject the missing-metadata case.
- Cost stress omitted or missing `double_cost`:
  `SignalProbeSpec` rejects missing `CostStressSpec`, `CostStressSpec` rejects
  profiles without `double_cost`, and `CostSensitivityReport` exposes
  `slippage_labeled_proxy=True`.
- Hidden failed/inconclusive runs:
  `StudyRunRecord` rejects terminal failure states without visible reasons, and
  `RuntimeDecision` rejects terminal decisions without `RejectionReasonRecord`.
- Prohibited MVP states:
  `coerce_runtime_decision_state` rejects `ALPHA_VALIDATED`, `FACTOR_PROMOTED`,
  `STRATEGY_READY`, `PORTFOLIO_READY`, `LIVE_READY`, `PAPER_READY`,
  `PROFITABLE`, `TRADABLE`, and `PRODUCTION_READY`.
- Raw/heavy/tool-result-like payload shapes:
  `classify_runtime_artifact` marks raw/heavy/runtime-value descriptors
  local-only and only admits curated row-free summaries.

`RuntimeToolResult` / `RuntimeRunSummary` contracts are not present on this
worktree (`alpha_system.runtime.tool_results` / `alpha_system.runtime.reports`
are RT-P22 surfaces). Their raw/heavy-data checks are therefore recorded as an
RT-P22 dependency rather than faked in RT-P20.

## Validation

- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`
  - Result: exit 0.
- `python -m ruff format tests/unit/runtime/fail_closed/test_runtime_fail_closed.py tests/no_lookahead/research_runtime/test_rt_p20_fixture_no_lookahead.py`
  - Result: exit 0; `2 files reformatted`.
- `python -m pytest tests/unit/runtime/fail_closed tests/no_lookahead/research_runtime -q`
  - Result: exit 0; `29 passed in 0.38s`.
- `python tools/verify.py --smoke`
  - Result: exit 0 with empty output.
- `test -f docs/research_runtime/FIXTURES.md`
  - Result: exit 0.
- `test -f docs/research_runtime/TESTING.md`
  - Result: exit 0.
- `find tests/fixtures/runtime -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed.
- `python tools/verify.py --typecheck`
  - Result: exit 0; compileall completed.
- `python -m ruff check tests/unit/runtime/fail_closed/test_runtime_fail_closed.py tests/no_lookahead/research_runtime/test_rt_p20_fixture_no_lookahead.py`
  - Result: exit 0; `All checks passed!`.
- `python -m ruff format --check tests/unit/runtime/fail_closed/test_runtime_fail_closed.py tests/no_lookahead/research_runtime/test_rt_p20_fixture_no_lookahead.py`
  - Result: exit 0; `2 files already formatted`.
- `python tools/verify.py --lint`
  - Result: exit 1.
  - Summary: broad existing repo lint/format debt; output started with
    `289 files would be reformatted, 589 files already formatted` and
    `Found 1361 errors`. The new RT-P20 Python files pass scoped Ruff check and
    format check.
- `python tools/verify.py --test`
  - Result: exit 1; `13 failed, 2381 passed in 40.94s`.
  - Failures:
    - `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network`
    - `tests/test_ralph_driver.py::test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase`
    - `tests/test_ralph_driver.py::test_provider_mock_commit_updates_active_campaign_and_leaves_git_clean`
    - `tests/test_ralph_driver.py::test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase`
    - `tests/test_ralph_driver.py::test_mock_review_rework_then_repair_passes`
    - `tests/test_ralph_driver.py::test_resume_from_spec_ready_continues_without_regenerating_spec`
    - `tests/test_ralph_driver.py::test_resume_from_executed_continues_to_review`
    - `tests/test_ralph_driver.py::test_fresh_provider_run_prepares_phase_branch_before_executor_and_preserves_main`
    - `tests/test_ralph_driver.py::test_resume_from_push_block_retries_gates_without_provider_or_new_commit`
    - `tests/test_ralph_driver.py::test_resume_from_push_block_missing_local_commit_stays_push_blocked_without_provider_replay`
    - `tests/test_ralph_driver.py::test_provider_usage_limit_writes_waiting_handoff_not_blocked`
    - `tests/test_ralph_driver.py::test_dag_wave_sequential_completes_with_dependencies`
    - `tests/test_ralph_driver.py::test_dag_wave_parallel_runs_wave_in_mock`
  - These are outside RT-P20 allowed paths and match the pre-existing broad
    Frontier/GitHub/Ralph-driver failures recorded in RT-P19.
- `find docs/research_runtime/FIXTURES.md docs/research_runtime/TESTING.md README.md tests/unit/runtime/fail_closed tests/no_lookahead/research_runtime/test_rt_p20_fixture_no_lookahead.py tests/fixtures/runtime/fail_closed -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P20/review.md`
  - Result: exit 0.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P20/verdict.json`
  - Result: exit 0.

`python tools/verify.py --all` was not run. `--lint` and `--test`, which are
included in `--all`, already fail for unrelated existing repo issues; rerunning
`--all` would not add a narrower RT-P20 signal.

## Artifact Audit

- `git ls-files runs` returned empty output.
- Codex did not create or edit `runs/**`.
- Codex did not create `review.md` or `verdict.json`.
- Codex did not stage files; no `git add`, `git commit`, `git push`,
  `git status`, or `git diff` was run.
- The Ralph staging list above contains no `runs/` path and no raw/canonical,
  feature, label, cache, metadata DB, artifact bundle, parquet, Arrow, Feather,
  DBN, ZST, SQLite, DB, WAL, log, broker, live, paper, order-routing, provider,
  or deployment path.

## Runtime Defects / Findings

No RT-P20 runtime defect was discovered in the exercised fail-closed surfaces.
The targeted fail-closed and no-lookahead suites pass against the current
runtime without modifying `src/alpha_system/runtime/**`.

Broad validation caveats are existing, out-of-scope failures:

- Repo-wide lint/format debt causes `python tools/verify.py --lint` to fail.
- Existing Frontier/GitHub/Ralph-driver tests cause `python tools/verify.py
  --test` to fail with 13 failures.

## Caveats / Deferrals

- Yellow-lane independent review remains required, but Codex was explicitly
  forbidden from calling Claude, running reviewer, creating `review.md`, or
  creating `verdict.json`.
- `RuntimeToolResult` / `RuntimeRunSummary` raw/heavy-data contract checks are
  deferred to RT-P22 because those contract modules are not present on this
  worktree.
- `git status --short` output is intentionally absent due the executor safety
  override forbidding `git status`.
