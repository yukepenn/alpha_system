# ALPHA_RESEARCH_RUNTIME_MVP / RT-P16 Handoff

## Curated file list for Ralph staging

Codex staged no files. Per the executor override, Ralph should stage only these
commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/evidence/__init__.py`
- `src/alpha_system/runtime/evidence/draft.py`
- `tests/unit/runtime/evidence/test_evidence_draft.py`
- `docs/research_runtime/EVIDENCE_DRAFT.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16.md`

No `runs/` path is included. No review artifacts, `review.md`, or
`verdict.json` were created by Codex.

## Implementation summary

RT-P16 adds `alpha_system.runtime.evidence` with:

- immutable, hashable `EvidenceDraft` and `EvidenceSectionSummary` contracts;
- `build_evidence_draft`, which assembles diagnostics, cost sensitivity,
  signal probe, bounded-grid, no-lookahead audit, manifest, study-run record,
  trial, limitation, artifact, and decision-state metadata;
- clean-run coupling to `EVIDENCE_DRAFT_READY`;
- terminal `REJECTED` / `INCONCLUSIVE` / `BLOCKED` visibility through
  `RejectionReasonRecord`;
- explicit non-promotional flags: descriptive only, not a candidate, not
  Reference truth, not a finalized `EvidenceBundle`, and not a promotion basis;
- summary-only safeguards that reject value-bearing summary keys.

The builder requires cost discipline for forward drafts: `base` and
`double_cost` cost profiles, slippage labeled as a proxy, and no cost profile as
a promotion basis. A referenced `SignalProbeReport` must point to the supplied
`CostSensitivityReport`.

## Governance and primitive boundary

The evidence package consumes these primitives by import and does not edit or
duplicate them:

- `alpha_system.governance.evidence_bundle.create_evidence_bundle`
- `alpha_system.governance.evidence_bundle.EvidenceBundle`
- `alpha_system.governance.trial_ledger.TrialLedgerRecord`
- existing runtime diagnostics, cost, probe, bounded-grid, no-lookahead audit,
  manifest, study-run record, and RT-P15 decision-state contracts

No files under governance, research, experiments, backtest, feature, label, data,
broker, live, paper, order-routing, provider, or deployment packages were
modified.

## Tests and docs

Added synthetic unit tests for:

- governance `EvidenceBundle` acceptance through the real governance surface;
- failed/inconclusive visibility via `RejectionReasonRecord`;
- rejection of value-bearing summaries;
- non-candidate / non-promotion / not-finalized-bundle flags;
- cost discipline requiring `base` + `double_cost` when building a forward
  draft.

Added `docs/research_runtime/EVIDENCE_DRAFT.md`. `README.md` now records RT-P16
as complete in the integration track, sets active/next to RT-P16 / RT-P17,
lists `alpha_system.runtime.evidence`, and keeps the local-only,
orchestration-only, accepted-DatasetVersion-only, no-provider-call,
no-broker/live/paper/deployment, and non-promotional safety boundaries.

## Validation

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md`
  - Result: exit 0; Frontier execute skill loaded.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP ...`
  - Result: exit 0; `NO_STOP`.
- Read-only context inspection via `sed` / `rg --files` over `AGENTS.md`,
  `frontier.yaml`, `ACTIVE_CAMPAIGN.md`,
  `campaigns/ALPHA_RESEARCH_RUNTIME_MVP/**`, relevant prior handoffs, and
  existing runtime/governance source files.
  - Result: exit 0 except
    `rg --files specs/ALPHA_RESEARCH_RUNTIME_MVP ... reviews/ALPHA_RESEARCH_RUNTIME_MVP`,
    which returned exit 2 because those directories are absent in this checkout.
    Prior commit-eligible handoffs were present.
- `git status --short`
  - Result: skipped.
  - Reason: explicitly forbidden by the executor safety override.
- `git ls-files runs`
  - Result: exit 0 with empty output. Ran twice; both empty.
- `python -c "import alpha_system.runtime.evidence"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: bare Python in this executor shell does not include `src/` on
    `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.evidence"`
  - Result: exit 0.
- `python -c "import alpha_system.governance.evidence_bundle"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: same bare-import `PYTHONPATH` issue.
- `PYTHONPATH=src python -c "import alpha_system.governance.evidence_bundle"`
  - Result: exit 0.
- `python -m ruff check --fix src/alpha_system/runtime/evidence`
  - Result: exit 1 initially after fixing import order; remaining issues were
    long lines in the new file.
- `python -m ruff format src/alpha_system/runtime/evidence`
  - Result: exit 0; `1 file reformatted, 1 file left unchanged`.
- `python -m ruff check src/alpha_system/runtime/evidence`
  - Result: exit 0; all checks passed.
- `python -m ruff format src/alpha_system/runtime/evidence tests/unit/runtime/evidence`
  - Result: exit 0; `3 files left unchanged`.
- `python -m ruff check src/alpha_system/runtime/evidence tests/unit/runtime/evidence`
  - Result: exit 0; all checks passed. Re-run after test cleanup also passed.
- `python -m pytest tests/unit/runtime/evidence -q`
  - Result: exit 0; `5 passed`. Ran before and after the prohibited-token test
    cleanup; final run was `5 passed in 0.17s`.
- `python tools/verify.py --smoke`
  - Result: exit 0 with no stdout.
- `test -f docs/research_runtime/EVIDENCE_DRAFT.md`
  - Result: exit 0.
- `test -f README.md`
  - Result: exit 0.
- `grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" src/alpha_system/runtime/evidence 2>/dev/null | grep -v "from_mapping\|resolve_dataset_version" || echo "no direct provider/file readers found in runtime/evidence"`
  - Result: exit 0; `no direct provider/file readers found in runtime/evidence`.
- `find data -type f ! -name README.md ! -name .gitkeep -print`
  - Result: exit 0 with empty output.
- `find artifacts -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print`
  - Result: exit 0 with empty output.
- `python tools/verify.py --all`
  - Result: exit 1; `13 failed, 2306 passed in 40.29s`.
  - Failures were outside RT-P16 evidence scope:
    `tests/test_github_utils.py::test_dry_run_pr_does_not_call_network` and
    12 `tests/test_ralph_driver.py` Workflow 2 / Ralph state-machine tests
    (`test_provider_wired_env_max_phases_one_runs_exactly_one_mock_phase`,
    `test_provider_mock_commit_updates_active_campaign_and_leaves_git_clean`,
    `test_provider_wired_default_mock_campaign_is_not_hard_coded_to_one_phase`,
    `test_mock_review_rework_then_repair_passes`,
    `test_resume_from_spec_ready_continues_without_regenerating_spec`,
    `test_resume_from_executed_continues_to_review`,
    `test_fresh_provider_run_prepares_phase_branch_before_executor_and_preserves_main`,
    `test_resume_from_push_block_retries_gates_without_provider_or_new_commit`,
    `test_resume_from_push_block_missing_local_commit_stays_push_blocked_without_provider_replay`,
    `test_provider_usage_limit_writes_waiting_handoff_not_blocked`,
    `test_dag_wave_sequential_completes_with_dependencies`,
    `test_dag_wave_parallel_runs_wave_in_mock`).
  - Codex did not modify these out-of-scope files.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0; `165 passed in 0.30s`.
- `find src/alpha_system/runtime/evidence tests/unit/runtime/evidence docs/research_runtime/EVIDENCE_DRAFT.md README.md -type f -size +1M -print`
  - Result: exit 0 with empty output.
- `rg -n "ALPHA_VALIDATED|FACTOR_PROMOTED|STRATEGY_READY|PORTFOLIO_READY|LIVE_READY|PAPER_READY|PROFITABLE|TRADABLE|PRODUCTION_READY" src/alpha_system/runtime/evidence tests/unit/runtime/evidence docs/research_runtime/EVIDENCE_DRAFT.md README.md`
  - Result: exit 1 with empty output; no prohibited MVP state token matched.
- `test -f handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16.md`
  - Result: exit 0.
- `find src/alpha_system/runtime/evidence tests/unit/runtime/evidence docs/research_runtime/EVIDENCE_DRAFT.md README.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P16.md -type f -size +1M -print`
  - Result: exit 0 with empty output.
- Final `git ls-files runs`
  - Result: exit 0 with empty output.

Skipped:

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
- No `runs/**` artifact was created or edited by Codex.
- No files were staged by Codex; therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- The scoped touched-file size check returned empty output.
- The runtime/evidence provider/file-reader heuristic returned
  `no direct provider/file readers found in runtime/evidence`.
- `find data ...`, `find artifacts ... -size +1M`, and non-fixture parquet scans
  returned empty output.
- No raw/canonical/feature/label/runtime value artifact, provider response,
  local DB, parquet, arrow, feather, DBN, ZST, log, cache bundle, model binary,
  broker, live, paper, order-routing, provider-call, or deployment file is in
  the Ralph staging list above.
- No `git add`, `git commit`, `git push`, `git status`, `git diff`, force push,
  PR, merge, broker, live, paper, order, deployment, Claude review, `review.md`,
  or `verdict.json` action was performed.

## Caveats and review needs

- The exact bare import commands in the generated spec fail in this executor
  shell unless `PYTHONPATH=src` is supplied. The explicit `PYTHONPATH=src`
  imports pass, and pytest uses the repo `pythonpath` setting.
- `python tools/verify.py --all` is not clean because of out-of-scope
  Workflow 2/GitHub/Ralph failures already present in the broader suite during
  this run. Focused RT-P16 evidence tests, runtime unit tests, smoke, canaries,
  docs checks, and artifact checks passed.
- Yellow-lane independent review artifacts are still required before merge, but
  Codex was explicitly forbidden from calling Claude, running reviewer, or
  creating `review.md` / `verdict.json`.
