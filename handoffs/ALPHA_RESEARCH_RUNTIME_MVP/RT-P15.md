# ALPHA_RESEARCH_RUNTIME_MVP / RT-P15 Handoff

## Curated file list for Ralph staging

Codex staged no files. Per the executor override, Ralph should stage only these
commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/decisions/__init__.py`
- `src/alpha_system/runtime/decisions/models.py`
- `src/alpha_system/runtime/decisions/records.py`
- `src/alpha_system/runtime/decisions/states.py`
- `tests/unit/runtime/decisions/test_decision_states.py`
- `docs/research_runtime/DECISION_STATES.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15.md`

No `runs/` path is included. No
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15/**` files were created by Codex;
fresh review and verdict artifacts are owned by Ralph/reviewer.

## Implementation summary

RT-P15 adds `alpha_system.runtime.decisions` with:

- `RejectionReasonRecord`, `RejectionReasonCode`, and the closed nine-code
  category set;
- `RuntimeDecisionState` and `RuntimeDecision`, which require visible reasons
  for terminal `REJECTED`, `INCONCLUSIVE`, and `BLOCKED` states and reject
  reasons on forward states;
- adapters for `RunRejectionReason`, `RuntimeEntryReason`,
  `NoLookaheadAuditReason`, and bounded-grid rejection records;
- `RuntimeStopCondition`, a runtime decision object that maps to `BLOCKED` and
  is distinct from the Workflow 2 operator `runs/<run_id>/STOP` file.

The adapters preserve upstream reason codes as `source_code` and map canonical
`code` to the closed RT-P15 category set. Reason payloads stay value-free and do
not copy expected/actual values, rows, raw data paths, provider payloads, or
heavy artifacts.

## Scope and primitive boundary

The implementation consumed existing reason-emitting modules and did not edit
them:

- `alpha_system.runtime.contracts.run_record`
- `alpha_system.runtime.contracts.run_spec`
- `alpha_system.runtime.entry_contract`
- `alpha_system.runtime.audit.no_lookahead`
- `alpha_system.runtime.grid.contracts`

No research, experiments, governance, backtest, feature, label, data, broker,
live, paper, order-routing, provider, or deployment code was edited. No IC,
cost, bounded-grid, no-lookahead, governance, backtest, feature, label, or data
logic was duplicated.

## README snapshot

`README.md` now records the RT-P15 runtime decision-state snapshot, notes
16/27 phases through RT-P15 in the Wave 2 integration track, sets active/next to
`RT-P16` - EvidenceBundle Draft Builder, lists
`alpha_system.runtime.decisions` and
`docs/research_runtime/DECISION_STATES.md`, and keeps the unchanged local-first,
accepted-DatasetVersion-only, no raw-provider, no external provider-call, no
broker/live/paper/order/account, structured-visible-failure, and
non-promotional safety boundaries.

## Validation

- `git status --short`
  - Result: skipped.
  - Reason: explicitly forbidden by the executor safety override in this
    prompt.
- `git ls-files runs`
  - Result: exit 0 with empty output.
- `python -c "import alpha_system.runtime.decisions"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this executor shell does not put the repository `src/` layout on
    `PYTHONPATH` for bare Python commands.
- `PYTHONPATH=src python -c "import alpha_system.runtime.decisions"`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/decisions -q`
  - Result: exit 0; `5 passed in 0.31s`.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0; `160 passed in 0.43s`.
- `python tools/verify.py --smoke`
  - Result: exit 0 with no stdout.
- `test -f docs/research_runtime/DECISION_STATES.md`
  - Result: exit 0.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed.
- `find src/alpha_system/runtime/decisions tests/unit/runtime/decisions docs/research_runtime/DECISION_STATES.md README.md handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P15.md -type f -size +1M -print`
  - Result: exit 0 with empty output.

Skipped:

- `git diff --cached --name-only` and any staged-set inspection using `git diff`
  - Reason: explicitly forbidden by the executor safety override, and Codex
    staged no files.
- Claude review, `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    reviewer orchestration and verdict parsing.

## Artifact audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created or edited by Codex.
- No files were staged by Codex; therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- The touched source/test/doc/handoff paths contain no file larger than 1 MB by the
  scoped `find ... -size +1M` check.
- No raw/canonical/feature/label/runtime value artifact, provider response,
  local DB, parquet, arrow, feather, DBN, ZST, log, cache bundle, model binary,
  broker, live, paper, order-routing, provider-call, or deployment file is in
  the Ralph staging list above.

## Caveats and review needs

- The exact bare import command from the generated spec fails in this executor
  shell unless `PYTHONPATH=src` is supplied. The supplemental import with
  `PYTHONPATH=src`, narrow decision tests, broader runtime unit tests, smoke,
  docs presence, and canaries passed.
- Yellow-lane review artifacts are still required before merge, but Codex was
  explicitly forbidden from calling Claude, running reviewer, or creating
  `review.md` / `verdict.json`.
- No reconciliation required out-of-scope edits to upstream reason producers.
