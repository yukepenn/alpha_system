# IVL-P05 Handoff

## Scope Delivered

- Added `src/alpha_system/research_lane/memory_router.py`, a value-free verdict
  router that exercises `reject_exploratory_promotion_artifact` before memory
  routing and then maps:
  - REJECT -> `RejectedIdeaRecord` keyed by the minted AlphaSpec id.
  - DATA_GAP -> validated `RequeuedVerdictRecord` with no probe shot spent.
  - WATCH / CANDIDATE -> `PromotionDecision` only when caller supplies
    `reviewer_verdict_id`, `evidence_bundle_id`, and `trial_ledger_refs`.
- Added `alpha idea run <idea.yaml>` in `src/alpha_system/cli/idea.py`, composing
  validate -> testability -> fast probe when the gate passes -> report -> memory.
  DATA_GAP/FAIL pre-test gates short-circuit before `fast_probe`.
- Added focused router and CLI tests for the required memory actions, fail-closed
  cases, exploratory refusal, and fixture end-to-end DATA_GAP requeue.
- Updated `README.md` with a compact IVL-P05 snapshot and IVL-P06 dogfood pointer.

## Files Changed

- `src/alpha_system/research_lane/memory_router.py`
- `src/alpha_system/cli/idea.py`
- `tests/unit/research_lane/test_memory_router.py`
- `tests/unit/cli/test_idea_cli.py`
- `README.md`
- `handoffs/ALPHA_IDEA_TO_VERDICT_LOOP_V0/IVL-P05.md`

## Validation

- `python -m pytest tests/unit/research_lane/test_memory_router.py tests/unit/cli/test_idea_cli.py -q`
  - Result: exit 0; `20 passed`.
- `PYTHONPATH=src python -m alpha_system.cli.main idea run research/idea_to_verdict_loop_v0/fixtures/day_of_week.idea.yaml`
  - Result: exit 0. The fixture short-circuited at pre-test DATA_GAP, emitted a
    report, and routed to a `RequeuedVerdictRecord` with
    `promotion_eligible=false` and `probe_spent=false`.
  - Note: the existing `python -m` import-order `RuntimeWarning` appeared, as in
    IVL-P04; command still exited 0.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed, including
    `forbidden_exploratory_promotion`.
- `grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"`
  - Result: exit 0; `no forbidden research->sim imports`.
- `python -m pytest tests/unit/research/test_research_no_value_engine.py -q`
  - Result: exit 0; `3 passed`.
- `python -c "import importlib,sys; [sys.exit('numpy/pandas must NOT import') for m in ('numpy','pandas') if importlib.util.find_spec(m)]"`
  - Result: exit 0; numpy and pandas are not importable.
- `git show HEAD:src/alpha_system/governance/rejected_idea.py | cmp -s - src/alpha_system/governance/rejected_idea.py && echo rejected_idea.py unchanged`
  - Result: exit 0; `rejected_idea.py unchanged`.
- `git show HEAD:src/alpha_system/governance/requeue.py | cmp -s - src/alpha_system/governance/requeue.py && echo requeue.py unchanged`
  - Result: exit 0; `requeue.py unchanged`.
- `git show HEAD:src/alpha_system/governance/promotion.py | cmp -s - src/alpha_system/governance/promotion.py && echo promotion.py unchanged`
  - Result: exit 0; `promotion.py unchanged`.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `python tools/verify.py --artifacts`
  - Result: exit 0.
- `python tools/verify.py --boundaries`
  - Result: exit 0.
- `python -m compileall -q src/alpha_system/research_lane/memory_router.py src/alpha_system/cli/idea.py tests/unit/research_lane/test_memory_router.py tests/unit/cli/test_idea_cli.py`
  - Result: exit 0.

## Skipped Or Substituted Checks

- `git diff -- src/alpha_system/governance/rejected_idea.py src/alpha_system/governance/requeue.py src/alpha_system/governance/promotion.py` was not run because the executor prompt explicitly forbids `git diff`. I used the non-diff `git show ... | cmp -s` checks above instead.
- `git diff --cached --name-only` was not run because the executor prompt explicitly forbids `git diff`, and Codex is not authorized to stage in this phase. Ralph owns explicit-path staging validation.
- `python tools/verify.py --all` was not run. The spec says to broaden to `--all` only if shared governance behavior appears affected; this phase added the router/CLI path, left the memory factories byte-unchanged, and the requested scoped, smoke, canary, artifact, and boundary checks passed.
- No review artifact was created and no reviewer was called. The executor prompt explicitly reserves review, verdict parsing, PR, staging, commit, and merge work for Ralph.

## Explicit Confirmations

- REJECT writes a `RejectedIdeaRecord` keyed by `idea_draft.alpha_spec_id`; a missing AlphaSpec id fails closed before the graveyard factory is called.
- DATA_GAP writes a valid `RequeuedVerdictRecord` and reports `probe_spent=false`.
- WATCH/CANDIDATE require `reviewer_verdict_id`, `evidence_bundle_id`, and at least one `trial_ledger_ref`; the router does not mint reviewer verdicts and never auto-promotes.
- `reject_exploratory_promotion_artifact` refuses the EXPLORATORY readout before any memory action; the canary is green. FactorLibrary/AlphaBook are not imported or written.
- `promotion_eligible` remains `false` in fast readouts, router output, and CLI output.
- `src/alpha_system/governance/rejected_idea.py`, `src/alpha_system/governance/requeue.py`, and `src/alpha_system/governance/promotion.py` are byte-unchanged versus `HEAD`.
- No paid data was sourced; no materialize, scaleout-driver, broker, paper, live,
  order-routing, deployment, or forbidden-path operation was performed.
- The README snapshot is compact and factual, with no generated run details,
  local artifact paths, or alpha/profitability/tradability/production claims.
- `git ls-files runs` is empty. I did not run `git add`, `git commit`,
  `git push`, `git status`, or `git diff`; all changes are left unstaged for
  Ralph's explicit-path staging.
