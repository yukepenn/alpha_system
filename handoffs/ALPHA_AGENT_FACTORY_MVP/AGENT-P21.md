# AGENT-P21 Handoff - Runtime Tool Integration Bridge

## Scope Completed

Implemented the scoped runtime-to-agent bridge for
`ALPHA_AGENT_FACTORY_MVP/AGENT-P21`.

Added:

- `alpha_system.agent_factory.runtime_bridge`, adapting
  `RuntimeToolResult` and `RuntimeRunSummary` into value-free
  `AgentToolResult` envelopes;
- runtime status mapping for forward outcomes plus `BLOCKED`, `REJECTED`, and
  `INCONCLUSIVE`;
- dataset resolution through `resolve_dataset_version`, with only `VERSIONED`
  and `READY_FOR_RESEARCH` accepted;
- fail-closed `BLOCKED` results for missing registry records, id mismatches,
  missing lifecycle state, and inadmissible lifecycle state;
- preservation of runtime run id, DatasetVersion id, FeaturePack/LabelPack
  refs, diagnostics summary refs/JSON summaries, cost summary, rejection
  reasons, blocking findings, artifact refs, limitations, and next gate;
- unit tests for mapping fidelity, `RuntimeRunSummary`, non-success outcomes,
  optional fields, value-free rejection, runtime import/static checks, and the
  resolver boundary;
- `docs/agent_factory/RUNTIME_BRIDGE.md`;
- compact `README.md` snapshot update for `AGENT-P21`.

No autonomous agent was instantiated. No diagnostics run was started. No raw
provider data, feature values, label values, runtime values, provider response,
heavy artifact, local DB, broker, paper, live, order, deployment, alpha,
tradability, profitability, candidate, promotion, or strategy-validation scope
was introduced.

## Staging

Codex staged no files. The executor instructions explicitly forbid `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes were left
unstaged for Ralph/the driver.

Exact staged file list from Codex actions: none.

Explicit file list for Ralph to stage:

- `src/alpha_system/agent_factory/runtime_bridge.py`
- `tests/unit/agent_factory/test_runtime_bridge.py`
- `docs/agent_factory/RUNTIME_BRIDGE.md`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P21.md`

No `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P21/**` files were created by Codex
because the executor prompt explicitly forbids calling Claude, running reviewer,
creating `review.md`, or creating `verdict.json`.

## Git Status Output

`git status --short` was not run. The executor instructions explicitly prohibit
Codex from running `git status`, so there is no `git status --short` output
from this executor turn. Ralph owns authoritative working-tree and staged-set
inspection after Codex finishes.

## Validation Commands

| Command | Result |
| --- | --- |
| `find runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP -maxdepth 3 -name STOP -print` | FAIL, exit 1: the requested run directory was not present in this worktree. |
| `test ! -e runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP` | PASS. |
| `test ! -e runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P21/STOP` | PASS. |
| `git status --short` | SKIPPED; executor instructions explicitly prohibit Codex from running `git status`. |
| `python -c "import alpha_system.agent_factory.runtime_bridge"` | FAIL, exit 1: `ModuleNotFoundError: No module named 'alpha_system'`. This source-layout shell does not put `src/` on `sys.path` for bare `python -c`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -c "import alpha_system.agent_factory.runtime_bridge"` | PASS. |
| `python -m pytest tests/unit/agent_factory/test_runtime_bridge.py -q` | PASS; final run `10 passed in 0.17s`. |
| `python tools/verify.py --smoke` | PASS; no output. |
| `test -f docs/agent_factory/RUNTIME_BRIDGE.md` | PASS. |
| `git ls-files runs` | PASS, exit 0 with empty output. |
| `git diff --name-only origin/main...HEAD \| grep -E '^src/alpha_system/runtime/' && echo "BLOCKER: runtime package edited" \|\| echo "ok: runtime not edited"` | SKIPPED; executor instructions explicitly prohibit Codex from running `git diff`. |
| `grep -REn "\.dbn\|\.zst\|read_parquet\|to_parquet\|pyarrow\|databento\|ib_insync\|ibapi\|\.feather\|\.arrow" src/alpha_system/agent_factory 2>/dev/null \| grep -v "resolve_dataset_version" \|\| echo "ok: no direct provider/file readers in agent_factory"` | RAN; output was existing guard constants in `tools/results.py`, `tools/contracts.py`, `entry_contract.py`, and `roles/contracts.py`. No direct provider/file reader call was introduced in `runtime_bridge.py`. |
| `python -m ruff check src/alpha_system/agent_factory/runtime_bridge.py tests/unit/agent_factory/test_runtime_bridge.py` | PASS; `All checks passed!`. Supplemental scoped lint check. |
| `python -m ruff format --check src/alpha_system/agent_factory/runtime_bridge.py tests/unit/agent_factory/test_runtime_bridge.py` | PASS; `2 files already formatted`. Supplemental scoped format check. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P21/review.md` | PASS. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P21/verdict.json` | PASS. |
| `find reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P21 -maxdepth 2 -type f -print` | FAIL, exit 1: review directory absent because reviewer artifacts are explicitly forbidden for Codex in this executor prompt. |

## Artifact Audit

- `git ls-files runs` returned empty output.
- Codex did not stage anything, so Codex introduced no staged `runs/**` path and
  no staged forbidden data, DB, cache, log, or heavy-artifact path.
- No file under `runs/**` was created or modified by this executor.
- No runtime source file under `src/alpha_system/runtime/**` was edited by this
  executor.
- No data-foundation source file under `src/alpha_system/data/**` was edited by
  this executor.
- No `ACTIVE_CAMPAIGN.md` write was performed.
- No review artifact, verdict JSON, PR, merge, staging, commit, broker/live/
  paper/order/account operation, provider call, runtime execution, alpha search,
  promotion, or deployment was performed by Codex.
- Python validation may create or touch local `__pycache__/` files; those are
  cache artifacts and must remain unstaged.

## Boundary Confirmation

- `runtime_bridge.py` imports and consumes `RuntimeToolResult` and
  `RuntimeRunSummary`; it does not redefine them.
- `runtime_bridge.py` imports and uses `resolve_dataset_version` as the default
  dataset resolver boundary. Tests use in-process resolver stubs only and do
  not touch real registries.
- The bridge creates only `AgentToolResult` outputs and relies on the AGENT-P05
  value-free validation to reject raw/heavy markers, bytes, dataframe or array
  objects, duplicate refs, and heavy artifact suffixes.
- The bridge handles `BLOCKED`, `REJECTED`, and `INCONCLUSIVE` without raising
  when runtime-visible reasons are present, and it maps `cost_summary=None` to
  `AgentToolResult.cost_summary=None`.
- The bridge does not duplicate diagnostics, cost stress, overfit, signal probe,
  no-lookahead, runtime input resolution, or registry behavior.
- The README snapshot is compact and contains no run-local paths, alpha/
  profitability/tradability claims, broker/live/paper/deployment behavior, or
  duplicated phase-handoff content.

## Caveats

- A pre-existing Agent Factory role contract,
  `src/alpha_system/agent_factory/roles/diagnostics_runner.py`, already imports
  `alpha_system.runtime.tool_results` by reference. `AGENT-P21` allowed paths do
  not permit editing that module, so Codex did not change it. This phase added
  the single runtime-to-agent adapter module requested by the spec and did not
  broaden edits outside the allowed file list.
- The exact bare import command failed only because this source-layout executor
  shell lacks `src/` on `sys.path`; the `PYTHONPATH=src` import, scoped bridge
  tests, scoped Ruff checks, and smoke check passed.
- Fresh YELLOW-lane Claude review and verdict artifacts remain required before
  merge. Codex did not call Claude, run reviewer, create `review.md`, create
  `verdict.json`, create a PR, merge, mark the phase PASS, stage, commit, or
  push.

## Review Request Focus

Ralph/the reviewer should verify that:

- `runtime_bridge.py` is the only new runtime-output adapter introduced by this
  phase;
- all runtime outcomes map defensively into value-free `AgentToolResult`
  statuses and fields;
- dataset resolution remains bound to `resolve_dataset_version` and the
  `VERSIONED` / `READY_FOR_RESEARCH` admissibility set;
- no raw/heavy payload, provider/file reader, autonomous runner, broker/live/
  paper/order/account, alpha, profitability, tradability, candidate, promotion,
  or strategy-validation scope was introduced;
- no forbidden path, `runs/**`, cache, DB, log, or heavy artifact is staged; and
- the pre-existing `diagnostics_runner.py` runtime type import is either
  accepted as a prior contract reference or routed to a later allowed-path
  repair.

## Next Step

Ralph should explicitly stage only the commit-eligible paths listed above, run
its lane-required checks and artifact guards, then route the required fresh
Claude review. This executor does not mark the phase PASS.
