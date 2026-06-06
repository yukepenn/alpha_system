# AGENT-P10 Handoff - Data Contract Auditor Role Contract

## Scope Completed

Created the contracts-only Data Contract Auditor role declaration, phase-scoped
unit test, role documentation, and operating prompt template. The role
self-registers on import through
`alpha_system.agent_factory.roles.registry.register(...)` and does not edit
`roles/__init__.py`, `roles/registry.py`, sibling role modules, runtime,
governance, research, data, feature, label, broker, paper, live, or order
packages.

No autonomous agent was instantiated. No dataset was resolved. No data, registry,
provider, runtime, broker, paper, live, deployment, PR, merge, Claude call,
reviewer run, `review.md`, or `verdict.json` was created by the executor.

## Files For Ralph To Stage

- `src/alpha_system/agent_factory/roles/data_contract_auditor.py`
- `tests/unit/agent_factory/roles/test_data_contract_auditor.py`
- `docs/agent_factory/roles/data_contract_auditor.md`
- `templates/agent_factory/roles/data_contract_auditor.md`
- `handoffs/ALPHA_AGENT_FACTORY_MVP/AGENT-P10.md`

The spec also allows `reviews/ALPHA_AGENT_FACTORY_MVP/AGENT-P10/**`, but the
executor did not create review artifacts because the executor prompt explicitly
forbade calling Claude, running the reviewer, creating `review.md`, or creating
`verdict.json`.

`README.md` was not edited. AGENT-P10 is a parallel-safe role-wave phase, and
the generated spec assigns the README snapshot to the coordinator at serial
merge time.

## Git Visibility

- Exact staged file list: not inspected by Codex. The executor prompt forbade
  `git status` and `git diff`, and Codex performed no staging.
- `git status --short`: skipped because the executor prompt explicitly forbade
  running `git status`.
- `git diff --cached --name-only`: skipped because the executor prompt
  explicitly forbade running `git diff`.
- Staging: no `git add`, `git commit`, or `git push` was run by Codex.
- Ralph remains responsible for authoritative explicit staging and the staged
  artifact audit before commit.

## Validation Results

- STOP/run-dir check: `ls -la runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP/phases/AGENT-P10`
  failed with `No such file or directory`. The run-local phase directory named
  in the executor prompt was absent in this worktree.
- STOP/run-dir check: `ls -la runs` failed with `No such file or directory`.
  There was no `runs/` directory in this worktree.
- STOP check: `find runs/2026-06-06T193514Z_ALPHA_AGENT_FACTORY_MVP -maxdepth 1 -name STOP -print`
  failed with `No such file or directory`. No STOP file existed at the requested
  run path because the run directory itself was absent.
- `python -c "import alpha_system.agent_factory.roles.data_contract_auditor"`:
  failed with `ModuleNotFoundError: No module named 'alpha_system'`. This
  checkout uses a `src/` layout and the bare shell does not place `src/` on
  `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.data_contract_auditor"`:
  passed.
- `PYTHONPATH=src python -c "import alpha_system.agent_factory.roles.data_contract_auditor as m; from alpha_system.agent_factory.roles import registry; r = registry.get('data_contract_auditor'); print('registered:', r.role_id, registry.role_ids().count('data_contract_auditor'))"`:
  passed; output was `registered: data_contract_auditor 1`.
- `python tools/verify.py --smoke`: passed.
- `python -m pytest tests/unit/agent_factory/roles/test_data_contract_auditor.py -q`:
  passed after the final edit; output was `8 passed in 0.01s`.
- `python -m pytest tests/unit/agent_factory/roles -q`: passed after the final
  edit; output was `55 passed in 0.05s`.
- `test -f docs/agent_factory/roles/data_contract_auditor.md`: passed.
- `test -f templates/agent_factory/roles/data_contract_auditor.md`: passed.
- `python -m ruff check src/alpha_system/agent_factory/roles/data_contract_auditor.py tests/unit/agent_factory/roles/test_data_contract_auditor.py`:
  initially failed on one long source line. The declarative string was shortened
  without changing the role boundary, and the command then passed with
  `All checks passed!`.
- `rg -n "^(from|import) alpha_system\\.(data|runtime|governance|features|labels|research)|^(from|import) (databento|ib_insync|ibapi)" src/alpha_system/agent_factory/roles/data_contract_auditor.py`:
  passed with no matches, confirming the role module does not import forbidden
  consumed primitive, provider, or runtime surfaces.
- `rg -n "data_contract_auditor" src/alpha_system/agent_factory/roles/__init__.py src/alpha_system/agent_factory/roles/registry.py`:
  passed with no matches, confirming the shared role package and registry do not
  hard-import this concrete role.
- `find reviews/ALPHA_AGENT_FACTORY_MVP -maxdepth 2 -path '*AGENT-P10*' -print`:
  failed with `No such file or directory`; no review artifact directory was
  present or created by Codex.
- `rg -n "ALPHA_VALIDATED|FACTOR_PROMOTED|CANDIDATE_PROMOTED|read_parquet|to_parquet|pyarrow|databento|ib_insync|ibapi|\\.dbn|\\.zst|\\.feather|\\.arrow|\\.sqlite|\\.db" src/alpha_system/agent_factory/roles/data_contract_auditor.py tests/unit/agent_factory/roles/test_data_contract_auditor.py docs/agent_factory/roles/data_contract_auditor.md templates/agent_factory/roles/data_contract_auditor.md`:
  returned one expected boundary-test assertion line for `databento`; no reader,
  provider library, promotion-status, or heavy-artifact code reference was
  found in the role module.
- `git ls-files runs`: passed with empty output.

## Skipped Checks And Reasons

- `git status --short`: skipped because the executor prompt explicitly forbade
  `git status`.
- `git diff --cached --name-only`: skipped because the executor prompt
  explicitly forbade `git diff`.
- `python tools/verify.py --lint`, `python tools/verify.py --typecheck`,
  `python tools/verify.py --test`, and `python tools/hooks/canary_runner.py`:
  not run by Codex. The generated spec says YELLOW lane required checks are
  orchestrated by Ralph; Codex ran the phase-requested smoke, import, file
  existence, focused test, and role-suite checks.
- `python tools/verify.py --all`: not run. The generated spec requested
  broadening to the role unit-test slice if shared role-registry behavior
  appeared affected, and that slice passed. Ralph owns broader validation.
- Review generation: skipped because the executor prompt explicitly forbade
  calling Claude, running reviewer, creating `review.md`, or creating
  `verdict.json`.
- PR, CI wait, merge gate, and merge: skipped because the executor prompt
  explicitly reserves those actions for Ralph.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No files under `runs/**` were written by Codex.
- The run-local phase directory was absent in this worktree, and no run-local
  handoff was created.
- No review artifacts were created by Codex.
- No data, raw/canonical/factor/label/cache values, provider responses, local
  DBs, logs, caches, or heavy artifacts were created.
- No staging was performed by Codex; Ralph remains responsible for explicit
  staging and the authoritative no-forbidden-path staged audit.

## Caveats

- The bare `python -c` import command from the generated spec fails unless
  `PYTHONPATH=src` is supplied. This matches the source-layout behavior recorded
  in sibling role handoffs.
- The run artifact directory named in the executor prompt was not present in
  this worktree.
- The Data Contract Auditor role declares contracts only. It does not execute
  input resolution, read registry data, read provider data, call providers, write
  registries, implement features or labels, promote work, self-review, or make
  alpha, tradability, profitability, strategy, broker, paper, live, deployment,
  or production claims.
