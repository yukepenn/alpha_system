# ALPHA_RESEARCH_RUNTIME_MVP / RT-P17 Handoff

## Curated file list for Ralph staging

Codex staged no files. Per the executor override, Ralph should stage only these
commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/handoff/__init__.py`
- `src/alpha_system/runtime/handoff/reference.py`
- `tests/unit/runtime/handoff/test_reference_candidate_handoff.py`
- `docs/research_runtime/REFERENCE_HANDOFF.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17.md`

No `runs/` path is included. No review artifacts, `review.md`, or
`verdict.json` were created by Codex.

## Implementation summary

RT-P17 adds `alpha_system.runtime.handoff` with:

- immutable `ReferenceCandidateHandoff`, `RuntimeObjectRef`,
  `VersionLineageSnapshot`, `CostProfileRef`, and `ReferenceRequirement`
  contracts;
- `build_reference_candidate_handoff`, which consumes an upstream
  `EvidenceDraft`, `StudyRunManifest`, `RuntimeArtifactManifest`,
  `CostSensitivityReport`, `CostModelVersion`, cost profile summaries, and
  `NoLookaheadAuditResult`;
- forward state capped at `REFERENCE_HANDOFF_READY`;
- `strategy_not_validated=True` and `next_required_gate =
  REFERENCE_VALIDATION_REQUIRED`;
- fail-closed terminal outcomes with visible `RejectionReasonRecord` values for
  missing cost stress, missing required cost profiles, missing/no-passing
  no-lookahead audit, or upstream terminal evidence;
- reference-only payloads carrying ids, hashes, scalar profile metadata,
  limitations, and refs only.

The handoff does not run Reference validation, execute a Reference backtest,
promote a factor, create a strategy candidate, or make alpha, tradability,
profitability, portfolio, paper, live, broker, order, account, deployment, or
production claims.

## Governance and primitive boundary

The handoff package consumes existing runtime and governance-adjacent contracts
by import and does not edit or duplicate them:

- `alpha_system.runtime.evidence.EvidenceDraft`
- `alpha_system.runtime.contracts.StudyRunManifest`
- `alpha_system.runtime.contracts.RuntimeArtifactManifest`
- `alpha_system.runtime.cost.CostSensitivityReport` and `CostModelVersion`
- `alpha_system.runtime.audit.NoLookaheadAuditResult`
- `alpha_system.runtime.decisions.RuntimeDecision` and
  `RejectionReasonRecord`

No files under governance, research, experiments, backtest, feature, label,
data, broker, live, paper, order-routing, provider, or deployment packages were
modified.

## Tests and docs

Added synthetic unit tests for:

- ready handoff assembly with evidence, manifest, artifact manifest,
  diagnostics refs, cost model, `base`, `double_cost`, and passed audit refs;
- missing cost stress blocking the handoff with a visible reason;
- missing `base` profile blocking the handoff fail-closed;
- rejected no-lookahead audit blocking the handoff;
- upstream terminal `EvidenceDraft` decisions staying terminal;
- scope-honest, value-free, non-promotional payload fields.

Added `docs/research_runtime/REFERENCE_HANDOFF.md`. `README.md` now records
RT-P17 as complete in the `runtime_integration` gate, sets active/next to
RT-P17 / RT-P18, lists `alpha_system.runtime.handoff`, lists the new
Reference handoff doc, and keeps the unchanged local-only,
accepted-DatasetVersion-only, no-provider-call, no-broker/live/paper/order,
descriptive, non-promotional safety boundaries. It also states that a
`ReferenceCandidateHandoff` is not Reference validation.

## Validation

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md && test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P17/STOP`
  - Result: exit 0; Frontier execute skill loaded and initial STOP checks clear.
- Read-only context inspection via `sed`, `find`, and `rg --files` over
  `AGENTS.md`, `frontier.yaml`, `ACTIVE_CAMPAIGN.md`,
  `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/**`, RT-P16 handoff, and existing
  runtime source/test/docs files.
  - Result: exit 0 except the specified RT-P17 run phase directory was absent
    before Codex created it for local audit output.
- `mkdir -p src/alpha_system/runtime/handoff tests/unit/runtime/handoff docs/research_runtime handoffs/ALPHA_RESEARCH_RUNTIME_MVP runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P17`
  - Result: exit 0.
- `PYTHONPATH=src python -m pytest tests/unit/runtime/handoff -q`
  - Result: exit 1 initially; 1 failure in
    `test_missing_base_profile_blocks_handoff_fail_closed` due a `KeyError`
    when materializing a missing `base` profile ref after correctly detecting
    the precondition failure.
  - Fix: `_cost_profile_refs` now emits refs only for present profiles when the
    handoff is terminal; the blocked reason remains visible.
- `PYTHONPATH=src python -m pytest tests/unit/runtime/handoff -q`
  - Result after fix: exit 0; `6 passed in 0.15s`.
- `python -m ruff format src/alpha_system/runtime/handoff tests/unit/runtime/handoff && python -m ruff check src/alpha_system/runtime/handoff tests/unit/runtime/handoff`
  - Result: exit 1 initially after formatting; unused `pytest` import in the
    new test file.
  - Fix: removed the unused import and an unnecessary local test artifact.
- `python -m ruff format src/alpha_system/runtime/handoff tests/unit/runtime/handoff && python -m ruff check src/alpha_system/runtime/handoff tests/unit/runtime/handoff`
  - Result: exit 0; all checks passed.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P17/STOP`
  - Result: exit 0; STOP checks clear before validation.
- `python -c "import alpha_system.runtime.handoff"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: bare Python in this executor shell does not include `src/` on
    `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.handoff"`
  - Result: exit 0.
- `python tools/verify.py --smoke`
  - Result: exit 0 with no stdout. Re-run after final guard cleanup also exit 0.
- `PYTHONPATH=src python -m pytest tests/unit/runtime/handoff -q`
  - Result: exit 0; final focused run `6 passed in 0.18s`.
- `test -f docs/research_runtime/REFERENCE_HANDOFF.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `PYTHONPATH=src python -m pytest tests/unit/runtime -q`
  - Result: exit 0; final run `171 passed in 0.34s`.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed. Re-run after final guard
    cleanup also exit 0.
- `python tools/verify.py --all`
  - Result: exit 1; final run `13 failed, 2312 passed in 38.73s`.
  - Failures are outside RT-P17 handoff scope and reproduce the same
    Workflow 2/GitHub/Ralph class of failures recorded in RT-P16:
    `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` and
    12 `tests/test_ralph_driver.py` provider-wired / resume / DAG-wave tests:
    `test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase`,
    `test_provider_mock_commit_updates_active_campaign_and_leaves_git_clean`,
    `test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase`,
    `test_mock_review_rework_then_repair_passes`,
    `test_resume_from_spec_ready_continues_without_regenerating_spec`,
    `test_resume_from_executed_continues_to_review`,
    `test_fresh_provider_run_prepares_phase_branch_before_executor_and_preserves_main`,
    `test_resume_from_push_block_retries_gates_without_provider_or_new_commit`,
    `test_resume_from_push_block_missing_local_commit_stays_push_blocked_without_provider_replay`,
    `test_provider_usage_limit_writes_waiting_handoff_not_blocked`,
    `test_dag_wave_sequential_completes_with_dependencies`, and
    `test_dag_wave_parallel_runs_wave_in_mock`.
- `python -m ruff format src/alpha_system/runtime/handoff tests/unit/runtime/handoff`
  - Result after final guard cleanup: exit 0; `3 files left unchanged`.
- `python -m ruff check src/alpha_system/runtime/handoff tests/unit/runtime/handoff`
  - Result after final guard cleanup: exit 0; all checks passed.
- `git ls-files runs`
  - Result after handoff write: exit 0 with empty output.
- `find src/alpha_system/runtime/handoff tests/unit/runtime/handoff docs/research_runtime/REFERENCE_HANDOFF.md README.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P17.md -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `rg -n "\\.dbn|\\.zst|read_parquet|pyarrow|ib_insync|\\.feather" src/alpha_system/runtime/handoff tests/unit/runtime/handoff 2>/dev/null || true`
  - Result: exit 0 with empty output.
- `find data -type f ! -name README.md ! -name .gitkeep -print`
  - Result: exit 0 with empty output.
- `find artifacts -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`
  - Result: exit 0 with empty output.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P17/STOP`
  - Result: exit 0; final STOP checks clear.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- `git diff --cached --name-only`
  - Reason: the executor safety override forbids `git diff`; Codex staged no
    files.
- `git add`, `git commit`, `git push`, PR creation, merge, Claude review,
  `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    staging, commit, validation orchestration, review, verdict parsing, PR, CI,
    and merge gates.

## Artifact audit

- `git ls-files runs` returned empty output.
- Final scoped size, provider/heavy-reader, non-fixture parquet, `data/`, and
  `artifacts/` scans returned empty output.
- No files were staged by Codex; therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- The Ralph staging list above contains no `runs/` path and no forbidden
  data/raw, data/canonical, data/factors, data/labels, data/cache, metadata DB,
  artifact bundle, parquet, arrow, feather, DBN, ZST, broker, live, paper,
  order-routing, provider-call, or deployment path.
- No `git add`, `git commit`, `git push`, `git status`, `git diff`, force push,
  PR, merge, broker, live, paper, order, deployment, Claude review,
  `review.md`, or `verdict.json` action was performed.

## Caveats and review needs

- The exact bare import command in the generated spec fails in this executor
  shell unless `PYTHONPATH=src` is supplied. The explicit `PYTHONPATH=src`
  import passes, and pytest uses the repo `pythonpath` setting.
- `python tools/verify.py --all` is not clean because of out-of-scope
  Workflow 2/GitHub/Ralph failures. Focused RT-P17 handoff tests, runtime unit
  tests, smoke, canaries, lint, docs check, and artifact checks passed.
- Yellow-lane independent review artifacts are still required before merge, but
  Codex was explicitly forbidden from calling Claude, running reviewer, or
  creating `review.md` / `verdict.json`.
