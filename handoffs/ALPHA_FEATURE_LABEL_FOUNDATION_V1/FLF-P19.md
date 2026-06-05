# FLF-P19 Handoff — Path Labels: MFE / MAE / Triple Barrier

## Change Summary

Implemented the additive path label family under
`alpha_system.labels.families.path`.

The family adds:

- `mfe`
- `mae`
- `target_before_stop`
- `triple_barrier`

Each definition is built from a governed `LabelSpec` (`lspec_`) through the
FLF-P16 `LabelContractSpec.from_label_spec` contract adapter. The implementation
consumes `LabelHorizonSpec`, `LabelPathSpec`, `BarrierSpec`,
`target_stop_rules`, `path_rules`, and `availability_time` from the existing
contracts and governance `LabelSpec`.

Path calculations operate over FLF-P04 trade-truth bars only via
`alpha_system.features.semantics.is_real_trade_bar`. Synthetic no-trade rows are
excluded before excursion or barrier evaluation. Emitted values are in-memory
`LabelValueRecord` objects only, with `label_available_ts` derived from the
barrier or horizon resolution row and clamped to never precede
`LabelSpec.availability_time`.

No shared label core, governance module, feature module, other label family,
materialized label values, provider access, strategy/backtest wrapper, broker,
paper, live, order, PR, merge, review, or verdict artifact was added.

## Staging / Curated File List

Exact staged files by Codex: none. The executor prompt explicitly prohibited
`git add`, `git commit`, `git push`, `git status`, and `git diff`; all changes
are left unstaged for Ralph.

Curated files for Ralph to stage by explicit path:

- `src/alpha_system/labels/families/path/__init__.py`
- `src/alpha_system/labels/families/path/family.py`
- `tests/unit/labels/families/path/test_path_family.py`
- `docs/feature_label_foundation/labels/path.md`
- `configs/labels/families/path/README.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P19.md`

No review artifacts were created by Codex because the executor prompt forbade
calling Claude, running reviewer, and creating `review.md` or `verdict.json`.
YELLOW review remains Ralph-owned.

## Validation Results

STOP check:

```text
test -f runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/STOP
  result: STOP absent before execution
```

Requested repo state:

```text
git status --short
  skipped: executor prompt explicitly forbids running git status
```

Requested import:

```text
python -c "import alpha_system.labels.families.path"
  exit 1
  stderr: ModuleNotFoundError: No module named 'alpha_system'
  reason: bare python does not put this src-layout checkout's src/ directory on PYTHONPATH

PYTHONPATH=src python -c "import alpha_system.labels.families.path"
  exit 0
```

Requested validation:

```text
python tools/verify.py --smoke
  exit 0
  output: none

python -m pytest tests/unit/labels/families/path -q
  exit 0
  output: 6 passed in 0.07s

test -f docs/feature_label_foundation/labels/path.md
  exit 0

python tools/hooks/canary_runner.py
  exit 0
  output summary: All Frontier canaries passed.

git ls-files runs
  exit 0
  output: none
```

Supplemental local checks:

```text
python -m pytest tests/unit/labels -q
  exit 0
  output: 15 passed in 0.09s

python -m ruff check src/alpha_system/labels/families/path tests/unit/labels/families/path
  exit 0
  output: All checks passed!

python -m py_compile src/alpha_system/labels/families/path/__init__.py src/alpha_system/labels/families/path/family.py tests/unit/labels/families/path/test_path_family.py
  exit 0
  output: none

find . -path './.git' -prune -o \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' -o -name '*.wal' -o -name '*.journal' \) -print
  exit 0
  output: none

rg -n "ALPHA_VALIDATED|STRATEGY_READY|LIVE_READY|PROFITABLE|TRADABLE|PRODUCTION_READY" src/alpha_system/labels/families/path tests/unit/labels/families/path docs/feature_label_foundation/labels/path.md configs/labels/families/path/README.md
  exit 1
  output: none
  result: no prohibited MVP-state names in FLF-P19 files
```

Boundary scan over FLF-P19 paths found only negative-boundary prose/test
mentions of `live`, `broker`, `paper`, and `order`; no provider reader,
Databento, IBKR, parquet/arrow/feather, DBN/Zstd, broker API, paper/live/order
implementation, or import was added.

Run-local artifact note:

```text
find runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1 -maxdepth 3 -type f -print
  exit 1
  stderr: no such file or directory
```

The supplied run artifact directory was absent in this checkout. Codex did not
create `runs/**` artifacts.

## Artifact Policy Confirmation

- No staging or commit was performed by Codex.
- `git ls-files runs` returned empty.
- No `runs/**` path is in the curated file list.
- No run-local `handoff.md`, `review.md`, `verdict.json`, checks, or repair
  artifact was created by Codex.
- No raw/canonical market data, feature values, label values, provider
  responses, parquet, arrow, feather, DBN, Zstd, local DB, SQLite, WAL, journal,
  cache, log, model binary, or heavy artifact was created as a commit-eligible
  artifact.
- `git diff --cached --name-only` was not run because the executor prompt
  forbade `git diff`; Codex performed no staging, so there is no Codex-staged
  set to inspect.
- Ralph should stage only the curated paths above by explicit path and confirm
  the staged set contains no `runs/` path before commit.

## DAG / Scope Confirmation

- FLF-P19 is `parallel_safe: true`, `must_run_alone: false`, merge group
  `label_families`.
- The authored paths are disjoint from FLF-P17, FLF-P18, and FLF-P20 family
  paths.
- `ACTIVE_CAMPAIGN.md` was not edited.
- Shared label core was not edited:
  `src/alpha_system/labels/spec.py`, `contracts.py`, `generation.py`,
  `path_metrics.py`, `store.py`, `alignment.py`, `validation.py`,
  `version.py`, `engine.py`, `registry.py`, `leakage_audit.py`, `reports.py`,
  `__init__.py`, and `families/__init__.py`.
- Governance modules, feature modules, and other label families were not edited.
- No external provider call, raw provider data access, broker/live/paper/order
  routing/account behavior, PR creation, merge, deployment, destructive
  cleanup, reviewer invocation, review artifact, verdict artifact, or phase
  PASS marking was performed.
- No alpha, profitability, tradability, strategy, backtest, portfolio,
  production-readiness, or broker-readiness claim was introduced.

## Review Status

Fresh Claude Opus review is required for this YELLOW phase, but Codex did not
call Claude or create review artifacts because the executor prompt forbade
those actions. Ralph owns review, verdict parsing, staging, commit, PR, CI,
merge gate, and semantic done-check.
