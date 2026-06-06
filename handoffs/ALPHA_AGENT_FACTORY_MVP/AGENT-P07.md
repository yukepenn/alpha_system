# Handoff - AGENT-P07: Research Director Role Contract

## Scope Completed

- Added the contracts-only `research_director` role module.
- The role self-registers through the AGENT-P03 discovery registry on import.
- The role module checks its `callable_tools` against the AGENT-P04 permission
  matrix source of truth at import time.
- Added focused unit tests for registration, value-free population, matrix tool
  alignment, forbidden authority coverage, and shared role-file isolation.
- Added the Research Director role doc and reusable operating prompt template.
- Updated the root README snapshot for AGENT-P07 and next phase AGENT-P08.

No autonomous agent, runner, alpha search, diagnostics, implementation,
promotion, review, PR, merge, broker, paper, live, order, deployment, provider,
or raw-data operation was performed.

## Explicit File List For Ralph Staging

Codex did not stage files. Ralph should stage only these commit-eligible paths:

- `src/alpha_system/agent_factory/roles/research_director.py`
- `tests/unit/agent_factory/roles/test_research_director.py`
- `docs/agent_factory/roles/research_director.md`
- `templates/agent_factory/roles/research_director.md`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P07.md`

No review artifacts were created by Codex. `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P07/**`
remains reviewer-owned per executor instructions.

## Git Status

- `git status --short`: skipped. The executor prompt explicitly forbade running
  `git status`, `git diff`, `git add`, `git commit`, and `git push`.
- No staging or commit commands were run.

## Validation Commands

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP && test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P07/STOP` | Passed; no active STOP file was present. |
| `python -c "import alpha_system.agent_factory.roles.research_director"` | Failed before code import with `ModuleNotFoundError: No module named 'alpha_system'`; this shell does not put `src/` on `PYTHONPATH` for bare `python -c`. |
| `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.research_director"` | Passed. |
| `python -m pytest tests/unit/agent_factory/roles/test_research_director.py -q` | Passed: `6 passed in 0.02s`. |
| `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.research_director as _m; from alpha_system.agent_factory.roles import registry; from alpha_system.agent_factory.permissions.matrix import permission_for; p=permission_for('research_director'); r=registry.get('research_director'); assert set(r.callable_tools)==set(p.tool.tool_ids if hasattr(p.tool,'tool_ids') else p.tool.allowed_tool_ids); print('research_director OK:', r.role_id)"` | Passed; printed `research_director OK: research_director`. The concrete AGENT-P04 accessor is `allowed_tool_ids`. |
| `python tools/verify.py --smoke` | Passed. |
| `test -f docs/agent_factory/roles/research_director.md && test -f templates/agent_factory/roles/research_director.md` | Passed. |
| `git ls-files runs` | Passed; output was empty. |
| `find src/alpha_system/agent_factory/roles tests/unit/agent_factory/roles docs/agent_factory/roles templates/agent_factory/roles handoffs/ALPHA_AGENT_FACTORY_MVP -type f \\( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' -o -name '*.sqlite' -o -name '*.db' -o -name '*.wal' -o -name '*.log' \\) -print` | Passed; output was empty. |
| `test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P07/review.md && test ! -e reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P07/verdict.json` | Passed; Codex created no reviewer artifacts. |
| `! rg -n "research_director" src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py` | Passed; no shared role package or registry file contains a hard per-role import/name. |

## Artifact Audit

- `git ls-files runs` returned empty.
- No `runs/**` path is commit-eligible or listed for Ralph staging.
- The run-local handoff is under
  `runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P07/handoff.md`
  for local audit only.
- No heavy/db/log artifact was found under the edited phase-owned paths.
- No raw/canonical/factor/label/cache data path was created or edited.
- No `review.md` or `verdict.json` was created.

## Caveats

- The literal bare `python -c` import command cannot resolve the `src/` layout
  in this shell. The same import passed with `PYTHONPATH=src`, and the targeted
  pytest command passed.
- `git status --short` output is intentionally absent because the executor
  prompt forbade running `git status`.
