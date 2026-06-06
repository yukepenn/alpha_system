# RT-P02 Handoff - Runtime Package Skeleton and Naming

## Scope Completed

- Added importable Research Runtime package stubs for the later foundation,
  diagnostics, and cost phases:
  - `src/alpha_system/runtime/contracts/__init__.py`
  - `src/alpha_system/runtime/diagnostics/__init__.py`
  - `src/alpha_system/runtime/diagnostics/factor/__init__.py`
  - `src/alpha_system/runtime/diagnostics/label/__init__.py`
  - `src/alpha_system/runtime/diagnostics/splits/__init__.py`
  - `src/alpha_system/runtime/diagnostics/cross_market/__init__.py`
  - `src/alpha_system/runtime/cost/__init__.py`
- Added focused import/structure tests in
  `tests/unit/runtime/test_package_skeleton.py`.
- Added the authoritative runtime naming document:
  `docs/research_runtime/NAMING.md`.
- Established the committed runtime config placeholder:
  `configs/runtime/README.md`.
- Updated the root README snapshot for RT-P02 complete / `3 of 27`, with
  RT-P03 as the next phase.

This phase added no diagnostics, probe, grid, audit, evidence, handoff, CLI,
data access, provider access, trading, broker, live, paper, order, account,
strategy, backtest, portfolio, production, or runtime behavior.

## Explicit File List

Executor-staged files: none. The prompt explicitly forbids the executor from
running `git add`, `git status`, `git diff`, `git commit`, or `git push`; Ralph
owns authoritative explicit staging and commit.

Files created or edited for Ralph to stage explicitly:

- `src/alpha_system/runtime/contracts/__init__.py`
- `src/alpha_system/runtime/diagnostics/__init__.py`
- `src/alpha_system/runtime/diagnostics/factor/__init__.py`
- `src/alpha_system/runtime/diagnostics/label/__init__.py`
- `src/alpha_system/runtime/diagnostics/splits/__init__.py`
- `src/alpha_system/runtime/diagnostics/cross_market/__init__.py`
- `src/alpha_system/runtime/cost/__init__.py`
- `tests/unit/runtime/test_package_skeleton.py`
- `docs/research_runtime/NAMING.md`
- `configs/runtime/README.md`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P02.md`

No review artifact, `review.md`, `verdict.json`, run-local handoff, PR, merge,
or phase PASS marker was created by the executor.

## Validation

- `git status --short`: SKIPPED. The executor safety override explicitly
  forbids `git status`; Ralph owns worktree and staging inspection.
- `python -c "import alpha_system.runtime"`: FAIL in this shell with
  `ModuleNotFoundError: No module named 'alpha_system'`; the bare shell does
  not have the `src/` layout on `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.runtime"`: PASS.
- `python -c "import alpha_system.runtime.entry_contract"`: FAIL in this shell
  with `ModuleNotFoundError: No module named 'alpha_system'`; same bare-shell
  package-path issue.
- `PYTHONPATH=src python -c "import alpha_system.runtime.entry_contract"`:
  PASS.
- `python -m pytest tests/unit/runtime -q`: PASS, `14 passed in 0.03s`.
- `python tools/verify.py --smoke`: PASS, exit code 0.
- `test -f docs/research_runtime/NAMING.md`: PASS.
- `grep -q "RT-P02" README.md`: PASS after the final README formatting edit.
- `git ls-files runs`: PASS, empty output.
- `test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`: PASS.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`: exit
  code 1, confirming no STOP file exists.
- `sha256sum src/alpha_system/runtime/entry_contract.py`: PASS, unchanged
  before and after edits:
  `ed91f4b6c4c4263cf1783aac1601f8073d094a0a0536bef0204a228d1d3bbcb6`.

## Additional Commands Run

- `sed -n '1,220p' .codex/skills/frontier-execute/SKILL.md && test ! -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`:
  PASS; loaded the Frontier execute skill and found no STOP file.
- `sed -n '1,240p' frontier.yaml`: PASS.
- `sed -n '1,120p' ACTIVE_CAMPAIGN.md`: PASS.
- `rg --files campaigns specs handoffs reviews runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P02 | sort`:
  FAIL, exit code 2 because
  `runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P02` does not
  exist in this worktree; the command still listed available campaign, handoff,
  spec, and review files.
- `sed -n '1,220p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/GOAL.md`: PASS.
- `sed -n '1,260p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md`: PASS.
- `sed -n '1,260p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md`: PASS.
- `sed -n '1,260p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`: PASS.
- `rg -n "RT-P02|Runtime Package Skeleton|runtime_state_model|prohibited" campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md`:
  PASS.
- `rg --files src/alpha_system/runtime tests/unit docs/research_runtime configs handoffs/ALPHA_RESEARCH_RUNTIME_MVP | sort`:
  PASS.
- `sed -n '1,220p' src/alpha_system/runtime/__init__.py`: PASS.
- `sed -n '1,260p' src/alpha_system/runtime/entry_contract.py`: PASS.
- `sed -n '1,220p' README.md`: PASS.
- `sed -n '254,286p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`:
  PASS.
- `sed -n '815,890p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml`:
  PASS.
- `sed -n '311,395p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md`:
  PASS.
- `sed -n '1,260p' tests/unit/runtime/test_entry_contract.py`: PASS.
- `sed -n '1,220p' docs/research_runtime/README.md`: PASS.
- `sed -n '1,220p' handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P01.md`: PASS.
- `rg -n "requires-python|python_version|target-version" pyproject.toml setup.cfg tox.ini .ruff.toml ruff.toml`:
  FAIL, exit code 2 because some optional config files are absent; it confirmed
  `pyproject.toml` targets Python 3.12.
- `find src/alpha_system/features src/alpha_system/labels -maxdepth 3 -name __init__.py -print | sort | head -40`:
  PASS.
- `find src/alpha_system/features src/alpha_system/labels -maxdepth 3 -name __init__.py -print | sort | head -8 | xargs -r sed -n '1,60p'`:
  PASS.
- `sed -n '1,80p' src/alpha_system/features/families/__init__.py`: PASS.
- `sed -n '1,80p' src/alpha_system/features/families/bbo/__init__.py`: PASS.
- `sed -n '1,80p' tests/unit/features/test_feature_package_skeleton.py`: PASS.
- `sed -n '1,80p' tests/unit/labels/families/test_label_family_package_skeleton.py`:
  PASS.
- `mkdir -p src/alpha_system/runtime/contracts src/alpha_system/runtime/diagnostics/factor src/alpha_system/runtime/diagnostics/label src/alpha_system/runtime/diagnostics/splits src/alpha_system/runtime/diagnostics/cross_market src/alpha_system/runtime/cost tests/unit/runtime configs/runtime docs/research_runtime handoffs/ALPHA_RESEARCH_RUNTIME_MVP`:
  PASS.
- `find src/alpha_system/runtime tests/unit/runtime docs/research_runtime configs/runtime handoffs/ALPHA_RESEARCH_RUNTIME_MVP -maxdepth 5 -type f | sort`:
  PASS; showed the expected files plus local test-generated `__pycache__`
  files.
- `sed -n '1,180p' docs/research_runtime/NAMING.md`: PASS.
- `sed -n '1,160p' tests/unit/runtime/test_package_skeleton.py`: PASS.
- `sed -n '1,45p' README.md`: PASS.
- `sed -n '1,120p' configs/runtime/README.md`: PASS.

## Artifact Audit

- `git ls-files runs` returned empty.
- No staging was performed by the executor.
- `git diff --cached --name-only` was not run because the prompt explicitly
  forbids `git diff`; Ralph must perform the authoritative staged-set audit.
- No `runs/`, data, DB, cache, log, parquet, arrow, feather, DBN, Zstd, model,
  raw provider, canonical, feature, label, or runtime value artifact was staged
  by the executor.
- Test execution generated local `__pycache__` files under runtime test/source
  directories. They are local-only byproducts and must not be staged.

## Entry Contract Confirmation

`src/alpha_system/runtime/entry_contract.py` was not edited. Its checksum was
identical before and after this execution:

```text
ed91f4b6c4c4263cf1783aac1601f8073d094a0a0536bef0204a228d1d3bbcb6
```

The RT-P01 package surface remains importable under `PYTHONPATH=src`, and the
new `tests/unit/runtime/test_package_skeleton.py` test asserts the RT-P01
symbols remain re-exported from `alpha_system.runtime`.

## README Snapshot

`README.md` now records RT-P02 complete / `3 of 27`, names RT-P03 as the next
phase, references the importable runtime package skeleton,
`docs/research_runtime/NAMING.md`, and `configs/runtime/`, and confirms no
`alpha runtime` CLI was added. The snapshot keeps the unchanged local-first,
accepted-DatasetVersion-only, no-provider, no-broker/live/paper/order/account,
and no-claim safety boundaries.

## Caveats

- The prompt-provided run phase directory was not present in this worktree, so
  no run-local handoff was written. The commit-eligible handoff is this file.
- The exact bare `python -c` import commands fail unless the repo is installed
  or `PYTHONPATH=src` is set. The package imports pass with `PYTHONPATH=src`,
  and both scoped runtime tests and `python tools/verify.py --smoke` pass.
- Claude review, verdict parsing, PR creation, staging, commit, push, and merge
  remain Ralph-owned and were not performed by the executor.
