# AGENT-P22 Handoff - Agent Dry-Run Harness

## Scope Completed

Implemented the bounded, non-alpha Agent Factory dry-run harness for
`ALPHA_AGENT_FACTORY_MVP/AGENT-P22`.

Added:

- `alpha_system.agent_factory.dry_run.harness`
- focused dry-run unit tests
- `docs/agent_factory/DRY_RUN.md`
- compact `README.md` post-P22 snapshot

The harness routes exactly one synthetic `ResearchTask` once through Research
Director, Hypothesis Scout, AlphaSpec Critic, Data Contract Auditor, Feature
Engineer, Label Engineer, Diagnostics Runner, No-Lookahead Auditor,
Statistical Reviewer, and Librarian. It drives the existing role, permission,
queue, separation, record, memory, tool-result, tool-registry, and
`runtime_bridge` contracts. It does not instantiate an autonomous agent, start
a continuous loop, run alpha search, use real data, call providers, touch
broker/paper/live/order/account scope, create a PR, merge, or promote anything.

The default route reaches `REFERENCE_HANDOFF_RECORDED` as its most advanced
forward state and ends `REJECTED`. A missing synthetic DatasetVersion resolver
returns a structured `BLOCKED` report. No PASS-to-promotion path is exposed.

## Executor Staging

Codex staged no files. The executor prompt explicitly forbade `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes were left
unstaged for Ralph/the driver.

Exact staged file list from Codex actions: none.

Expected explicit commit-eligible file list for Ralph staging:

```text
src/alpha_system/agent_factory/dry_run/__init__.py
src/alpha_system/agent_factory/dry_run/harness.py
tests/unit/agent_factory/dry_run/test_harness.py
docs/agent_factory/DRY_RUN.md
README.md
handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P22.md
```

`tests/unit/agent_factory/dry_run/__init__.py` already existed and was not
edited. No `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P22/**` files were created by
Codex because the executor prompt forbade calling Claude, running reviewer,
creating `review.md`, and creating `verdict.json`.

## Git Status Output

`git status --short` was not run. The executor prompt explicitly prohibits
Codex from running `git status`, so there is no `git status --short` output
from this executor turn. Ralph owns authoritative working-tree and staged-set
inspection after Codex finishes.

## Validation Results

Required validation:

| Command | Result |
| --- | --- |
| `git status --short` | SKIPPED; executor instructions explicitly prohibit Codex from running `git status`. |
| `python -c "import alpha_system.agent_factory.dry_run.harness"` | FAIL, exit 1: `ModuleNotFoundError: No module named 'alpha_system'`. This source-layout shell does not put `src/` on `sys.path` for bare `python -c`; same caveat was seen in AGENT-P21. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -c "import alpha_system.agent_factory.dry_run.harness"` | PASS, exit 0. |
| `python tools/verify.py --smoke` | PASS, exit 0, no stdout. |
| `python -m pytest tests/unit/agent_factory/dry_run -q` | PASS, exit 0, `10 passed in 0.65s`. |
| `test -f docs/agent_factory/DRY_RUN.md` | PASS, exit 0. |
| `git ls-files runs` | PASS, exit 0 with empty output. |

Supplemental scoped checks:

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest tests/unit/agent_factory/dry_run -q` | PASS, exit 0, `10 passed in 0.61s`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m ruff check src/alpha_system/agent_factory/dry_run tests/unit/agent_factory/dry_run` | PASS, exit 0, `All checks passed!`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m ruff format --check src/alpha_system/agent_factory/dry_run tests/unit/agent_factory/dry_run` | Initially FAIL, exit 1: harness/test file needed formatting. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m ruff format src/alpha_system/agent_factory/dry_run tests/unit/agent_factory/dry_run` | PASS, exit 0, `2 files reformatted, 2 files left unchanged`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m ruff format --check src/alpha_system/agent_factory/dry_run tests/unit/agent_factory/dry_run` | PASS, exit 0, `4 files already formatted`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m ruff check src/alpha_system/agent_factory/dry_run/harness.py src/alpha_system/agent_factory/dry_run/__init__.py` | PASS after cleanup, exit 0, `All checks passed!`. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P22/review.md` | PASS, exit 0. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P22/verdict.json` | PASS, exit 0. |
| `test ! -e runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P22/review.md` | PASS, exit 0. |
| `test ! -e runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P22/verdict.json` | PASS, exit 0. |
| `test -f handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P22.md` | PASS, exit 0. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P22/review.md` | PASS, exit 0 on final post-handoff check. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P22/verdict.json` | PASS, exit 0 on final post-handoff check. |
| `test -f docs/agent_factory/DRY_RUN.md` | PASS, exit 0 on final post-handoff check. |

Harness execution probes:

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'PY' ... run_agent_dry_run() ... PY` | PASS, exit 0. Output confirmed `REJECTED`, `REFERENCE_HANDOFF_RECORDED`, `10` tool results, `7` registered tool invocations, `7` handoffs. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'PY' ... run_agent_dry_run(dataset_version_resolver=lambda _path, _id: None) ... PY` | PASS, exit 0. Output confirmed `BLOCKED`, `DIRECTOR_SCOPED`, Data Contract Auditor `BLOCKED`, rejected memory `BLOCKED`, research memory `BLOCKED`. |

Artifact audit:

| Command | Result |
| --- | --- |
| `git ls-files runs` | PASS, exit 0 with empty output. |
| `find data -type f ! -name README.md ! -name .gitkeep -print` | PASS, exit 0 with empty output. |
| `find artifacts -type f -size +1M -print` | PASS, exit 0 with empty output. |
| `git ls-files \| grep -E '\.(sqlite\|sqlite3\|db\|db-journal\|wal\|parquet\|arrow\|feather\|dbn\|zst\|pkl\|pickle\|joblib\|onnx\|npy\|npz\|log)$' \| grep -v '^tests/.*fixtures/' \|\| echo "no committed heavy/db/log artifacts"` | PASS, exit 0, output `no committed heavy/db/log artifacts`. |

Read-only/context commands run:

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md` - exit 0.
- `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P22/STOP` - exit 0.
- `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP` - exit 0.
- `sed -n '1,260p' AGENTS.md` - exit 0.
- `sed -n '1,260p' frontier.yaml` - exit 0.
- `sed -n '1,120p' ACTIVE_CAMPAIGN.md` - exit 0.
- `rg --files campaigns/ALPHA_AGENT_FACTORY_MVP specs handoffs reviews runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P22` - exit 2 because the run phase directory was absent; listed available campaign/handoff files.
- `sed -n '1,260p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` - exit 0.
- `sed -n '1,260p' campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md` - exit 0.
- `rg -n "AGENT-P22|Agent Dry-Run Harness|dry-run harness|dry_run" campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml campaigns/ALPHA_AGENT_FACTORY_MVP/ACCEPTANCE.md` - exit 0.
- `rg --files src/alpha_system/agent_factory tests/unit/agent_factory docs/agent_factory handoffs/ALPHA_AGENT_FACTORY_MVP reviews/ALPHA_AGENT_FACTORY_MVP` - exit 2 because `reviews/ALPHA_AGENT_FACTORY_MVP` was absent; listed available Agent Factory files.
- `sed -n '1,260p' handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P19.md` - exit 0.
- `sed -n '1,260p' handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P20.md` - exit 0.
- `sed -n '1,260p' handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P21.md` - exit 0.
- `sed -n '768,822p' campaigns/ALPHA_AGENT_FACTORY_MVP/PHASE_PLAN.md` - exit 0.
- `sed -n '1875,1918p' campaigns/ALPHA_AGENT_FACTORY_MVP/campaign.yaml` - exit 0.
- Multiple `sed` reads under `src/alpha_system/agent_factory/{roles,permissions,tools,queue,separation,records,memory}` and relevant unit tests - exit 0; used to map public contracts before editing.
- Multiple `sed` reads under `src/alpha_system/runtime/**` - exit 0; read only to understand existing runtime result constructors. No runtime source was edited, and harness imports runtime only through `runtime_bridge`.
- `rg -n "name = \"(queue|alphaspec|feature|label|review|ledger|memory)\." configs/agent_factory/tools/registry.toml` - exit 0; confirmed registered tool surfaces.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'PY' ... tool_names() ... PY` - exit 0; listed registered tool names.
- `sed -n '1,120p' src/alpha_system/agent_factory/dry_run/__init__.py` - exit 0.
- `sed -n '1,80p' tests/unit/agent_factory/dry_run/__init__.py` - exit 0.
- `test -f src/alpha_system/agent_factory/dry_run/harness.py` - exit 1 before creation.
- `test -f tests/unit/agent_factory/dry_run/test_harness.py` - exit 1 before creation.
- `test -f docs/agent_factory/DRY_RUN.md` - exit 1 before creation.
- `sed -n '1,260p' README.md` - exit 0.
- `sed -n '1,220p' docs/agent_factory/README.md` - exit 0.
- `sed -n '1,140p' docs/agent_factory/DRY_RUN.md` - exit 0 after creation.
- `sed -n '1,80p' README.md` - exit 0 after snapshot update.
- `rg --files src/alpha_system/agent_factory/dry_run tests/unit/agent_factory/dry_run docs/agent_factory README.md handoffs/ALPHA_AGENT_FACTORY_MVP | sort` - exit 0; listed relevant files and existing handoffs.

## Artifact Audit Confirmation

- `git ls-files runs` returned empty output.
- No file under `runs/**` was created or edited by this executor.
- No run-local handoff was written.
- No review artifact or verdict artifact was created.
- Codex staged nothing, so Codex introduced no staged `runs/**` path and no
  staged forbidden data, DB, cache, log, or heavy-artifact path.
- The expected Ralph staging list above contains no `runs/**`, data, DB,
  cache, log, or heavy artifact path.
- Ralph must perform the authoritative staged-set audit after explicit staging
  because the executor prompt forbade `git status`, `git diff`, and
  `git diff --cached --name-only`.

## README Snapshot Confirmation

`README.md` now has a compact post-P22 snapshot: `AGENT-P22` complete, Wave 4
closeout in progress, next `AGENT-P23`, new durable surfaces
`alpha_system.agent_factory.dry_run.harness` and
`docs/agent_factory/DRY_RUN.md`, and unchanged boundaries. It does not include
run-local paths, generated run details, alpha/profitability/tradability claims,
broker/live/paper/order/account behavior, or deployment behavior.

## Caveats

- The exact bare import command failed only because this source-layout executor
  shell lacks `src/` on `sys.path`; the `PYTHONPATH=src` import, smoke check,
  and exact scoped pytest command passed.
- The shared tool registry in this worktree does not contain queue or AlphaSpec
  tool entries, so the harness records early Director/Scout/Critic steps as
  structured `AgentToolResult` outputs plus the existing Scout handoff helper,
  and exercises registered `ToolInvocationRecord` contracts for registry,
  feature, label, runtime, review, and memory steps. No shared registry or role
  module was edited.
- Fresh YELLOW-lane Claude review and `verdict.json` remain required before
  merge. Codex did not call Claude, run reviewer, create `review.md`, create
  `verdict.json`, create a PR, merge, mark the phase PASS, stage, commit, or
  push.
