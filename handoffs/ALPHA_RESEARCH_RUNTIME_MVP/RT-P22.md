# ALPHA_RESEARCH_RUNTIME_MVP / RT-P22 Handoff

## Curated file list for explicit staging by Ralph

- `README.md`
- `docs/research_runtime/TOOL_RESULTS.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P22.md`
- `src/alpha_system/runtime/tool_results.py`
- `tests/unit/runtime/test_tool_results.py`

No `configs/runtime/tool_results/**` file was needed. No review artifact is
included because Codex was explicitly forbidden from calling Claude, running a
reviewer, creating `review.md`, or creating `verdict.json`.

## Implementation summary

RT-P22 adds `alpha_system.runtime.tool_results` with immutable, serializable
`RuntimeToolResult` and `RuntimeRunSummary` contracts. The contracts carry only
status, run id, dataset/feature/label/code/config version ids, compact
diagnostics summaries, compact cost summaries with slippage labeled as a proxy,
visible `RejectionReasonRecord` payloads, artifact references, and the next
required gate.

The module consumes existing runtime contracts by import:
`StudyRunRecord`, `StudyRunManifest`, `RuntimeArtifactManifest`,
`RuntimeArtifactEntry`, `RuntimeArtifactRef`, `DiagnosticsReport`,
`DiagnosticsReportRef`, `CostSensitivityReport`, and `RejectionReasonRecord`.
It does not edit or redefine those primitives.

`RuntimeDecisionState` is used as the status surface, so prohibited MVP states
remain unrepresentable. Terminal `REJECTED`, `INCONCLUSIVE`, and `BLOCKED`
results require matching visible rejection reasons; forward states reject
rejection reasons.

The contract rejects raw/value/heavy fields in mapping inputs, including value
arrays, canonical bars/BBO payloads, provider payloads/rows, and heavy artifact
paths such as Parquet, Arrow, Feather, DBN, ZST, SQLite/DB/WAL, NumPy, pickle,
joblib, ONNX, and logs.

## Docs and README

- Added `docs/research_runtime/TOOL_RESULTS.md` documenting the contract shape,
  no-raw/heavy-data guarantee, no autonomous-agent framing, non-promotional
  interpretation, and fast-path-is-not-Reference-truth boundary.
- Updated `README.md` with the compact RT-P22 snapshot, module/doc pointers,
  active/next coordinator pointer, and unchanged safety boundaries.

## Git status

`git status --short` was not run. The executor prompt explicitly forbade Codex
from running `git status`, `git diff`, `git add`, `git commit`, or `git push`.
Ralph owns staging and authoritative git hygiene checks for this phase.

## Validation

- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP; echo $?`
  - Result: exit 0; output `1`, meaning no run-level STOP file was present.
- `find runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P22 -maxdepth 1 -type f -print`
  - Result: exit 1; phase run-artifact directory was absent in this worktree.
    No run-local handoff/review/verdict artifact was created by Codex.
- `python -m ruff format src/alpha_system/runtime/tool_results.py tests/unit/runtime/test_tool_results.py`
  - Initial result: exit 0; `2 files reformatted`.
  - Final result: exit 0; `2 files left unchanged`.
- `python -c "import alpha_system.runtime.tool_results"`
  - Result: exit 1; `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this source-layout executor shell does not add `src/` to
    `PYTHONPATH` for bare `python -c`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.tool_results"`
  - Result: exit 0.
- `python -m ruff check src/alpha_system/runtime/tool_results.py tests/unit/runtime/test_tool_results.py`
  - Initial result: exit 1; four E501 long error-message lines.
  - Final result: exit 0; `All checks passed!`.
- `python -m pytest tests/unit/runtime/test_tool_results.py -q`
  - Initial result: exit 0; `32 passed`.
  - Final result: exit 0; `33 passed`.
- `python -m pytest tests/unit/runtime -q`
  - Initial result: exit 0; `229 passed`.
  - Final result: exit 0; `230 passed`.
- `python tools/verify.py --smoke`
  - Result: exit 0 with no stdout.
- `test -f docs/research_runtime/TOOL_RESULTS.md`
  - Result: exit 0.
- `test -f README.md`
  - Result: exit 0.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0; all Frontier canaries passed.
- `git ls-files runs`
  - Result: exit 0 with empty output.

Skipped by instruction:

- `git status --short`: forbidden by executor prompt.
- `git diff --cached --name-only` and staged-path audits: forbidden because
  Codex was told not to run `git diff` and not to stage files.
- `git add`, `git commit`, `git push`: forbidden; Ralph owns staging/commit.
- `python tools/verify.py --all`: not run because the phase made a scoped
  additive runtime contract/test/doc change and the generated spec says broader
  Yellow-lane orchestration is Ralph-owned unless broader shared-behavior
  validation is required. Runtime unit tests, smoke, and canaries passed.

## Artifact audit

- `git ls-files runs` returned empty output.
- Codex did not stage any file.
- The curated file list for Ralph contains no `runs/**` path and no data/raw,
  data/canonical, data/factors, data/labels, data/cache, metadata DB, artifact
  bundle, parquet, arrow, feather, DBN, ZST, SQLite/DB/WAL, log, cache, broker,
  live, paper, order-routing, provider-call, or deployment path.
- Because staging was explicitly prohibited, Codex could not verify
  `git diff --cached --name-only`; Ralph must perform the authoritative staged
  artifact audit before commit.

## Safety confirmations

- No autonomous agent, agent loop, agent runner, or agent harness was created.
- No provider, broker, live, paper, order-routing, account, deployment, PR,
  merge, or reviewer operation was performed.
- Tool results carry compact summaries and references only; tests cover
  rejection of raw/value/heavy fields and prohibited MVP states.
- The change makes no alpha, tradability, profitability, strategy, portfolio,
  paper, live, broker, or production-readiness claim.

## Caveats and follow-ups

- The exact bare import command from the generated spec fails in this executor
  shell without `PYTHONPATH=src`; the source-layout import succeeds and pytest
  uses the repo test configuration.
- Fresh Yellow-lane Claude review and Ralph-owned staged artifact checks remain
  required before merge.
