# AGENT-P04 Handoff

## Scope Completed

Implemented the contracts-only Agent Factory permission model and static
role-to-permission matrix.

Added:

- immutable, value-free permission primitives:
  `ToolPermission`, `DataPermission`, `WritePermission`, `ReviewPermission`,
  `PromotionPermission`, `HumanApprovalRequired`, and `RedLaneRequired`;
- `RolePermissions` aggregate with an explicit `default_deny` constructor;
- static ten-role permission matrix with fail-closed lookup helpers;
- scoped unit tests for default-deny construction, fail-closed validation,
  matrix completeness, no raw data, no direct registry write, no promotion,
  review-role confinement, and human-approval / Red-lane markers;
- `docs/agent_factory/PERMISSIONS.md`;
- value-free config mirror at `configs/agent_factory/permissions/matrix.yaml`;
- compact README snapshot for AGENT-P04.

No concrete role module, tool implementation, separation enforcement, runtime
bridge, autonomous agent, continuous runner, alpha search, factor promotion,
data access, provider call, broker/paper/live/order/account surface, PR, merge,
review, `review.md`, or `verdict.json` was created by Codex.

## Staged Files

No files were staged by Codex, per executor instruction. Codex did not run
`git add`, `git commit`, `git push`, `git status`, or `git diff`.

Ralph should explicitly stage only these commit-eligible files for this phase:

- `src/alpha_system/agent_factory/permissions/__init__.py`
- `src/alpha_system/agent_factory/permissions/model.py`
- `src/alpha_system/agent_factory/permissions/matrix.py`
- `tests/unit/agent_factory/permissions/test_model.py`
- `tests/unit/agent_factory/permissions/test_matrix.py`
- `docs/agent_factory/PERMISSIONS.md`
- `configs/agent_factory/permissions/matrix.yaml`
- `README.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P04.md`

`tests/unit/agent_factory/permissions/__init__.py` already existed and was reused
unchanged.

## Git Status Output

`git status --short` was not run. The executor instruction explicitly prohibits
Codex from running `git status`; Ralph owns authoritative working-tree and
staged-set inspection after Codex finishes.

## Validation Commands

| Command | Result |
| --- | --- |
| `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP && test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P04/STOP` | PASS before implementation; no STOP file was present. |
| `git status --short` | SKIPPED; executor instructions explicitly prohibit Codex from running `git status`. |
| `python -c "import alpha_system.agent_factory.permissions.model, alpha_system.agent_factory.permissions.matrix"` | FAIL in this shell: `ModuleNotFoundError: No module named 'alpha_system'`. Reason: this source-layout environment does not put `src` on `PYTHONPATH` for bare `python -c`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -c "import alpha_system.agent_factory.permissions.model, alpha_system.agent_factory.permissions.matrix"` | PASS. |
| `PYTHONDONTWRITEBYTECODE=1 python tools/verify.py --smoke` | PASS; exit 0. |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python -m pytest tests/unit/agent_factory/permissions -q` | PASS; `39 passed in 0.04s`. |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python -m pytest tests/unit/agent_factory -q` | PASS; `78 passed in 0.08s`. |
| `test -f docs/agent_factory/PERMISSIONS.md` | PASS. |
| `test -f README.md` | PASS. |
| Matrix invariant snippet from the phase spec, run as `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'PY' ... PY` | PASS; output: `matrix OK: 10 roles; fail-closed on unknown role_id`. |
| `grep -REn "\.dbn\|\.zst\|read_parquet\|to_parquet\|pyarrow\|databento\|ib_insync\|ibapi\|\.feather\|\.arrow" src/alpha_system/agent_factory/permissions 2>/dev/null \|\| echo "no direct provider/file readers in permissions code"` | PASS; output: `no direct provider/file readers in permissions code`. |
| `git ls-files runs` | PASS; empty output. |
| `find . -maxdepth 4 -type d -name __pycache__ -print` | PASS; empty output. |
| `find . -maxdepth 3 -name .pytest_cache -type d -print` | PASS; empty output. |
| `find runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P04 -maxdepth 2 -type f -print 2>/dev/null` | PASS for local-artifact audit; exit 1 with empty output because the run-local AGENT-P04 phase directory is absent. |
| `find reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P04 -maxdepth 3 -type f -print 2>/dev/null` | PASS for review-artifact audit; exit 1 with empty output because no review artifact path exists. |
| `test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/STOP && test ! -f runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P04/STOP` | PASS after validation; no STOP file was present. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'PY' ... PY` public API sanity check importing `all_permissions`, `permission_for`, and `role_ids` | PASS; output: `10 10 librarian`. |

Additional local inspection:

- `awk` line-length check on new Python files: PASS; no line over 100 columns.
- A broad local `rg` query for repo type/lint context was over-wide and exited
  2 after producing unrelated repo-wide output; it was not a validation check.
  Codex replaced it with direct `sed -n '1,90p' pyproject.toml` inspection.

Skipped by instruction:

- `git status --short`: prohibited by executor instructions.
- `git diff --cached --name-only`: not run because executor instructions
  prohibit `git diff`, and Codex did not stage files.
- Claude review, reviewer, `review.md`, and `verdict.json`: prohibited for
  Codex in this executor turn; Ralph owns review routing.

## Artifact Audit

- `git ls-files runs` returned empty.
- Codex did not stage anything, so Codex staged no `runs/**` path and no
  forbidden data, heavy artifact, DB, cache, log, review, or verdict path.
- Authoritative staged-set audit is left to Ralph because executor instructions
  ban `git status` and `git diff`, and Ralph owns staging.
- No run-local AGENT-P04 file was created under
  `runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P04`.
- No `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P04/**`, `review.md`, or
  `verdict.json` artifact was created by Codex.
- No `.pytest_cache` or `__pycache__` directory was present after validation.
- No data, raw/canonical/feature/label/runtime/agent value, provider response,
  SQLite/DB/WAL, Parquet, Arrow, Feather, DBN, ZST, cache, log, or generated
  report bundle was created or edited.

## README Snapshot

`README.md` was updated with a compact AGENT-P04 snapshot:

- `ALPHA_AGENT_FACTORY_MVP` foundation gate has advanced through `AGENT-P04`;
- next phase is `AGENT-P05`;
- newly added durable modules/docs are listed:
  `alpha_system.agent_factory.permissions.model`,
  `alpha_system.agent_factory.permissions.matrix`, and
  `docs/agent_factory/PERMISSIONS.md`;
- safety boundaries remain contracts-only, default-deny/fail-closed, local-only,
  accepted-DatasetVersion-only, no autonomous agent, no raw-provider access, no
  external provider calls, and no broker/live/paper/order scope.

The README snapshot contains no run-local paths, local artifact paths,
alpha/tradability/profitability claims, broker/live/paper/deployment behavior,
or duplicated handoff content.

## Caveats and Follow-Ups

- Fresh Claude YELLOW review and verdict artifacts are still required by Ralph
  after Codex execution. Codex did not call Claude and did not create
  `review.md` or `verdict.json`.
