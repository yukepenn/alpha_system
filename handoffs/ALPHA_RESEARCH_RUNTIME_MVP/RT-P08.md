# ALPHA_RESEARCH_RUNTIME_MVP / RT-P08 Handoff

## Scope

Implemented the Label Diagnostics Runtime under
`alpha_system.runtime.diagnostics.label`. The runtime builds a descriptive
`LabelDiagnosticsReport` plus `DiagnosticsRunRecord` from a label-family
`DiagnosticsRunSpec`, resolved `RuntimeInputPack`, upstream feature/label
diagnostics reports, and scalar label diagnostic observations/profiles.

The implementation delegates to existing primitives:

- `alpha_system.research.feature_label_diagnostics.build_feature_label_diagnostics`
- `alpha_system.research.events.post_event_mfe_mae`
- `alpha_system.research.events.target_before_stop_probability`

It does not call providers, materialize labels, edit label packs, expose labels
as live features, create review artifacts, create PRs, merge, or push.

## Repair Summary

Claude review returned `REWORK` for B1: the root `README.md` edit was outside
RT-P08's authoritative `campaign.yaml` `allowed_paths` and introduced a
global-file race for a `parallel_safe` diagnostics-wave phase. This bounded
repair removed the `README.md` edit entirely and left `README.md` matching
`HEAD`. No review, verdict, PR, merge, broker, live, paper, or provider action
was performed.

## Staging

Initial executor pass staged no files, per the executor override.

Exact staged file list before repair validation: none.

Exact explicit file list staged for the repair commit:

- `src/alpha_system/runtime/diagnostics/label/__init__.py`
- `src/alpha_system/runtime/diagnostics/label/runtime.py`
- `tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py`
- `docs/research_runtime/diagnostics/label.md`
- `configs/runtime/diagnostics/label/README.md`
- `configs/runtime/diagnostics/label/default.yaml`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md`

`README.md` is intentionally excluded because RT-P08 is `parallel_safe` and the
authoritative campaign contract does not include `README.md` in this phase's
`allowed_paths`.

Do not stage ignored validation caches such as `__pycache__/` or
`.pytest_cache/`.

## README Snapshot

No `README.md` snapshot is included in this repair. The prior snapshot edit was
removed because the coordinator-owned global snapshot is not commit-eligible for
RT-P08 under the authoritative campaign contract.

## Validation

Skipped due executor override:

- `git status --short` was not run because the executor prompt explicitly
  prohibited `git status`.
- Staged-set inspection with `git diff --cached --name-only` was not run because
  the executor prompt explicitly prohibited `git diff`. Codex did not stage any
  files.

Commands run:

- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP; printf '%s\n' $?`
  - Result: exit 0, output `1`; no STOP file present.
- `python -c "import alpha_system.runtime.diagnostics.label"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not place `src` on `PYTHONPATH`; pytest config does.
- `PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.label"`
  - Result: exit 0.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/diagnostics/label -q`
  - Result: exit 0, `5 passed`.
- `python -m pytest tests/unit/runtime/diagnostics/label tests/unit/runtime/test_package_skeleton.py -q`
  - Result: exit 0, `8 passed`.
- `python -m ruff check src/alpha_system/runtime/diagnostics/label tests/unit/runtime/diagnostics/label`
  - Initial result: exit 1 for line length, `datetime.UTC`, and unused import
    findings in new files.
  - Final result after fixes: exit 0, `All checks passed!`.
- `test -f docs/research_runtime/diagnostics/label.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0, empty output.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0, all Frontier canaries passed.
- `python tools/verify.py --all`
  - Result: exit 1.
  - Final summary: `13 failed, 2243 passed in 38.01s`.
  - Remaining failures were outside RT-P08 label diagnostics:
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

Read-only discovery commands were also run with exit 0 unless noted: `sed` over
`AGENTS.md`, `frontier.yaml`, `ACTIVE_CAMPAIGN.md`, campaign docs, diagnostics
contracts, runtime contracts, input resolver, research diagnostics primitives,
label leakage audit primitives, README, and existing tests; `find` over
campaign/spec/runtime/config/doc/handoff paths; and `rg` over research, labels,
runtime, and tests for existing label diagnostics primitives.

## Repair Validation

Commands run during the B1 repair attempt:

- `sed -n '1,220p' .codex/skills/frontier-repair/SKILL.md`
  - Result: exit 0; repair workflow loaded.
- `git status --short --branch`
  - Result: exit 0; branch
    `auto/alpha_research_runtime_mvp/rt-p08-label-diagnostics-runtime`, with
    `README.md` modified before repair plus RT-P08 runtime/doc/config/test/handoff
    paths.
- `git diff -- README.md`
  - Initial result: exit 0; showed the out-of-contract RT-P08 README snapshot.
  - Final result after repair: exit 0, empty output.
- `git diff --cached --name-only`
  - Result before staging: exit 0, empty output.
- `find runs -name STOP -print`
  - Result: exit 1 because `runs/` is absent in this worktree; no active STOP
    file was found.
- `rg --files specs campaigns/ALPHA_RESEARCH_RUNTIME_MVP handoffs/ALPHA_RESEARCH_RUNTIME_MVP reviews/ALPHA_RESEARCH_RUNTIME_MVP 2>/dev/null | rg 'RT-P08|campaign.yaml|GOAL.md|review.md|verdict.json'`
  - Result: exit 0; found campaign contract and handoff, no local RT-P08 review
    or verdict files.
- `sed -n '1260,1310p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`
  - Result: exit 0; confirmed RT-P08 `allowed_paths` exclude `README.md`.
- `sed -n '3040,3190p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`
  - Result: exit 0; confirmed the parallel-safe/global-file stop condition.
- `sed -n '1,260p' handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md`
  - Result: exit 0; read the existing handoff before repair.
- `find reviews/ALPHA_RESEARCH_RUNTIME_MVP -maxdepth 3 -type f -path '*RT-P08*' -print 2>/dev/null`
  - Result: exit 1 with empty output; no local RT-P08 review artifacts found.
- `sed -n '1,60p' README.md`
  - Result: exit 0; inspected the invalid README snapshot before repair.
- `git show HEAD:README.md | sed -n '1,60p'`
  - Result: exit 0; inspected the baseline README snapshot.
- `find src/alpha_system/runtime/diagnostics/label tests/unit/runtime/diagnostics/label docs/research_runtime/diagnostics configs/runtime/diagnostics/label -type f -print | sort`
  - Result: exit 0; confirmed RT-P08 files and ignored Python caches.
- `git diff -- src/alpha_system/runtime/diagnostics/label/__init__.py`
  - Result: exit 0; inspected the only modified pre-existing in-scope runtime
    file.
- `git status --short`
  - Result after README repair: exit 0 with no `README.md` entry:
    - ` M src/alpha_system/runtime/diagnostics/label/__init__.py`
    - `?? configs/runtime/diagnostics/`
    - `?? docs/research_runtime/diagnostics/`
    - `?? handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md`
    - `?? src/alpha_system/runtime/diagnostics/label/runtime.py`
    - `?? tests/unit/runtime/diagnostics/label/`
- `git ls-files runs`
  - Result: exit 0, empty output.
- `PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.label"`
  - Result: exit 0.
- `test -f docs/research_runtime/diagnostics/label.md`
  - Result: exit 0.
- `python -c "import alpha_system.runtime.diagnostics.label"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this shell does not place `src` on `PYTHONPATH`; the project pytest
    configuration does.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/diagnostics/label -q`
  - Result: exit 0, `5 passed in 0.13s`.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0, all Frontier canaries passed.
- `python tools/verify.py --all`
  - Result: exit 1, `13 failed, 2243 passed in 34.59s`.
  - Failures remain the same out-of-scope Workflow 2/GitHub harness tests:
    `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` and
    twelve `tests/test_ralph_driver.py` cases covering provider-wired mock,
    resume, push-block, usage-limit, and DAG-wave behavior.
- `just frontier-doctor`
  - Result: exit 0, Frontier doctor passed.
- `python -m ruff check src/alpha_system/runtime/diagnostics/label tests/unit/runtime/diagnostics/label`
  - Result: exit 0, `All checks passed!`.
- `git add src/alpha_system/runtime/diagnostics/label/__init__.py src/alpha_system/runtime/diagnostics/label/runtime.py tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py docs/research_runtime/diagnostics/label.md configs/runtime/diagnostics/label/README.md configs/runtime/diagnostics/label/default.yaml handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md`
  - Result: exit 0; explicit staging only.
- `git diff --cached --name-only`
  - Result after explicit staging: exit 0, exact staged set:
    - `configs/runtime/diagnostics/label/README.md`
    - `configs/runtime/diagnostics/label/default.yaml`
    - `docs/research_runtime/diagnostics/label.md`
    - `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md`
    - `src/alpha_system/runtime/diagnostics/label/__init__.py`
    - `src/alpha_system/runtime/diagnostics/label/runtime.py`
    - `tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py`
- `git diff --cached --name-only | rg '^runs/'`
  - Result: exit 1, empty output; no `runs/` path staged.
- `git status --short`
  - Result after explicit staging:
    - `A  configs/runtime/diagnostics/label/README.md`
    - `A  configs/runtime/diagnostics/label/default.yaml`
    - `A  docs/research_runtime/diagnostics/label.md`
    - `A  handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P08.md`
    - `M  src/alpha_system/runtime/diagnostics/label/__init__.py`
    - `A  src/alpha_system/runtime/diagnostics/label/runtime.py`
    - `A  tests/unit/runtime/diagnostics/label/test_label_diagnostics_runtime.py`
- `git diff --cached --check`
  - Result: exit 0.

## Artifact Audit

- `git ls-files runs` returned empty.
- Codex did not create or stage any `runs/**` artifact.
- Codex did not create `review.md` or `verdict.json`.
- Codex did not create a PR, merge, push, or run forbidden staging commands.
- The repair staging list excludes `README.md` and contains only RT-P08
  `campaign.yaml` `allowed_paths`.
- No raw/canonical/feature/label/runtime value artifact, local DB, parquet,
  arrow, feather, DBN, ZST, log, cache bundle, model binary, broker, live, paper,
  or order-routing file is in the repair staged list.
- Ignored Python cache files were created by local validation under
  `__pycache__/` and `.pytest_cache/`; they are not commit-eligible.

## Caveats

- The exact spec import command fails in this shell unless `PYTHONPATH=src` is
  set. The project pytest configuration sets `pythonpath = ["src"]`, and the
  `PYTHONPATH=src` import passed.
- `python tools/verify.py --all` still fails in out-of-scope Workflow 2/GitHub
  harness tests listed above. The RT-P08 scoped tests, smoke check, lint check,
  docs presence check, canary runner, and `runs` artifact audit passed.
