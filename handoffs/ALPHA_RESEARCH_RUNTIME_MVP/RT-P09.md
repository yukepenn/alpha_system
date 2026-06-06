# RT-P09 Executor Handoff

Campaign: `ALPHA_RESEARCH_RUNTIME_MVP`  
Phase: `RT-P09` - Session / Regime / RTH / ETH Split Diagnostics  
Executor: Codex  
Status: implementation complete for Ralph validation/review routing; not self-approved

## Scope Completed

- Built `alpha_system.runtime.diagnostics.splits` with:
  - `SessionSplitReport`
  - `RegimeSplitReport`
  - `SplitDefinition`
  - scalar `SplitBucketSummary`
  - `build_session_split_report`
  - `build_regime_split_report`
  - `build_split_diagnostics_reports`
- Reports carry the RT-P06 `DiagnosticsReport` contract, `DiagnosticsFamily.SPLITS`,
  `DiagnosticsQualityGate`, limitations, lineage refs, coverage/quality summaries, and visible
  `RunRejectionReason` records for failed/low-sample paths.
- Regime and session split summaries orchestrate `alpha_system.research.regimes` directly:
  `regime_filter_coverage`, `regime_filter_uplift`, `false_rejection_rate`, and
  `conditional_strategy_improvement`.
- Conditioning uses `available_ts`; `label_available_ts` is an outcome guard only.
  Label/future outcome fields are rejected as conditioning fields.
- Added tiny synthetic fixtures, scoped tests, split docs, synthetic-safe configs, and README
  snapshot text.

## Staging

Codex did not stage files. The executor prompt explicitly required leaving all changes unstaged and
forbade `git add`, `git status`, and `git diff`.

Files for Ralph to stage explicitly, if accepted:

- `README.md`
- `configs/runtime/diagnostics/splits/README.md`
- `configs/runtime/diagnostics/splits/regime_buckets.synthetic.json`
- `configs/runtime/diagnostics/splits/session_windows.synthetic.json`
- `docs/research_runtime/diagnostics/splits.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P09.md`
- `src/alpha_system/runtime/diagnostics/splits/__init__.py`
- `src/alpha_system/runtime/diagnostics/splits/core.py`
- `tests/fixtures/runtime/diagnostics/splits/README.md`
- `tests/fixtures/runtime/diagnostics/splits/synthetic_observations.json`
- `tests/unit/runtime/diagnostics/splits/test_splits.py`

No `runs/**` path was staged by Codex.

## Git Status

`git status --short` was not run. The user executor prompt explicitly forbade `git status`.

## Commands Run

Context and STOP checks:

- `sed -n '1,220p' /home/yuke_zhang/projects/alpha_system-alpha_research_runtime_mvp-rt-p09/.codex/skills/frontier-execute/SKILL.md` - passed; skill instructions loaded.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && printf 'STOP present\n' || printf 'no STOP\n'` - passed; output `no STOP`.
- `sed -n '1,220p' AGENTS.md` - passed; project operating guide loaded.
- `sed -n '1,220p' frontier.yaml` - passed; control-plane context loaded.
- `rg --files campaigns specs src/alpha_system/runtime/diagnostics src/alpha_system/research tests/unit/runtime/diagnostics docs configs handoffs | sed -n '1,240p'` - passed; scoped files listed.
- `sed -n '1,220p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/GOAL.md` - passed; campaign goal loaded.
- `rg -n "RT-P09|split|R-012|R-013|diagnostics" campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md campaigns/ALPHA_RESEARCH_RUNTIME_MVP/campaign.yaml campaigns/ALPHA_RESEARCH_RUNTIME_MVP/ACCEPTANCE.md campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RISK_REGISTER.md campaigns/ALPHA_RESEARCH_RUNTIME_MVP/RUNBOOK.md` - passed; phase/risk context loaded.
- `sed -n '1,260p' src/alpha_system/runtime/diagnostics/contracts.py` - passed.
- `sed -n '1,320p' src/alpha_system/runtime/diagnostics/report.py` - passed.
- `sed -n '1,260p' src/alpha_system/research/regimes.py` - passed.
- `sed -n '1,220p' src/alpha_system/runtime/diagnostics/splits/__init__.py` - passed.
- `sed -n '260,620p' src/alpha_system/runtime/diagnostics/report.py` - passed.
- `sed -n '220,620p' src/alpha_system/runtime/diagnostics/contracts.py` - passed.
- `sed -n '1,260p' src/alpha_system/runtime/contracts/run_record.py` - passed.
- `sed -n '1,260p' tests/unit/runtime/diagnostics/test_report.py` - passed.
- `sed -n '1,260p' tests/unit/runtime/diagnostics/test_contracts.py` - passed.
- `for f in src/alpha_system/runtime/diagnostics/factor/__init__.py src/alpha_system/runtime/diagnostics/label/__init__.py src/alpha_system/runtime/diagnostics/cross_market/__init__.py; do sed -n '1,220p' "$f"; done` - passed.
- `rg -n "RuntimeInputPack|available_ts|label_available_ts|session" src/alpha_system/runtime src/alpha_system/governance src/alpha_system/features src/alpha_system/labels tests | sed -n '1,260p'` - passed.
- `rg -n "class .*Input|InputPack|available_ts|label_available_ts" src/alpha_system/runtime -g '*.py'` - passed.
- `rg --files src/alpha_system/runtime | sed -n '1,220p'` - passed.
- `find configs/runtime -maxdepth 4 -type f -print | sed -n '1,220p'` - passed.
- `sed -n '1,180p' README.md` - passed.
- `sed -n '77,320p' src/alpha_system/runtime/input_resolver.py` - passed.
- `sed -n '580,780p' src/alpha_system/runtime/input_resolver.py` - passed.
- `sed -n '1,220p' configs/runtime/README.md` - passed.
- `find docs/research_runtime -maxdepth 2 -type f -print | sort | sed -n '1,160p'` - passed.
- `sed -n '1,220p' docs/research_runtime/DIAGNOSTICS_CONTRACTS.md` - passed.
- `sed -n '925,1005p' campaigns/ALPHA_RESEARCH_RUNTIME_MVP/PHASE_PLAN.md` - passed.
- `sed -n '1,220p' pyproject.toml` - passed.
- `find tests/fixtures -maxdepth 4 -type f -print | sed -n '1,200p'` - passed.
- `sed -n '1,220p' src/alpha_system/runtime/__init__.py && sed -n '1,220p' src/alpha_system/runtime/diagnostics/__init__.py` - passed.
- `rg -n "RunRejectionReason\(|low_sample|weak_diagnostics|data_unavailable" src tests | sed -n '1,220p'` - passed.
- `rg -n "ACCEPTED_DATASET_VERSION_LIFECYCLE_STATES|READY_FOR_RESEARCH|VERSIONED" src/alpha_system/runtime/input_resolver.py src/alpha_system/runtime/entry_contract.py` - passed.
- `mkdir -p tests/unit/runtime/diagnostics/splits tests/fixtures/runtime/diagnostics/splits docs/research_runtime/diagnostics configs/runtime/diagnostics/splits handoffs/ALPHA_RESEARCH_RUNTIME_MVP` - passed.

Implementation checks:

- `python -c "import alpha_system.runtime.diagnostics.splits"` - failed before validation with `ModuleNotFoundError: No module named 'alpha_system'`; this shell does not have the package installed and no `PYTHONPATH` is set.
- `python -m pytest tests/unit/runtime/diagnostics/splits -q` - passed; `5 passed`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.diagnostics.splits"` - passed.
- `python -m pytest tests/unit/runtime/diagnostics/splits -q` - passed; `5 passed`.
- `test -f docs/research_runtime/diagnostics/splits.md` - passed.

Spec validation and artifact audit:

- `python -c "import alpha_system.runtime.diagnostics.splits"` - failed with `ModuleNotFoundError: No module named 'alpha_system'`; same environment/PYTHONPATH caveat as above.
- `python tools/verify.py --smoke` - passed.
- `git ls-files runs` - passed; output empty.
- `find data -type f ! -name README.md ! -name .gitkeep -print` - passed; output empty.
- `find artifacts -type f -size +1M -print` - passed; output empty.
- `find . -name "*.parquet" -not -path "./tests/fixtures/*" -print` - passed; output empty.
- `git ls-files | grep -E '\.(sqlite|sqlite3|db|wal|parquet|arrow|feather|dbn|zst|pkl|npy|npz|log)$' | grep -v '^tests/fixtures/' || echo "no committed heavy/db/log artifacts"` - passed; output `no committed heavy/db/log artifacts`.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP && printf 'STOP present\n' || printf 'no STOP\n'` - passed; output `no STOP`.
- `find tests/fixtures/runtime/diagnostics/splits -type f -size +1M -print` - passed; output empty.
- `wc -c tests/fixtures/runtime/diagnostics/splits/synthetic_observations.json` - passed; output `2072 tests/fixtures/runtime/diagnostics/splits/synthetic_observations.json`.

## Skipped Checks

- `git status --short` - skipped because the executor prompt explicitly forbade `git status`.
- Reviewer execution, `review.md`, and `verdict.json` - skipped because the executor prompt
  explicitly forbade calling Claude, running reviewer, creating review artifacts, or creating a
  verdict.
- PR creation, merge, staging, commit, and push - skipped because the executor prompt explicitly
  made these Ralph-owned and forbade Codex from doing them.

## Artifact Audit Confirmation

- `git ls-files runs` returned empty.
- No files were found under `data/` beyond allowed placeholders by the requested audit command.
- No `artifacts/` file larger than 1 MB was found.
- No non-fixture Parquet files were found.
- No committed heavy/db/log artifacts were found by the requested `git ls-files | grep` audit.
- Split fixture file is 2,072 bytes; no split fixture file exceeds 1 MB.
- No run-local handoff, review, verdict, or repair-attempt artifact was created.

## README Snapshot Confirmation

`README.md` was updated compactly to mention the RT-P09 split diagnostics module,
synthetic-safe config templates, and `docs/research_runtime/diagnostics/splits.md`. It does not
claim PASS, review completion, PR creation, merge completion, alpha validation, tradability,
profitability, broker/live/paper behavior, deployment behavior, or strategy readiness.

## Caveats

- The exact import command from the generated spec fails in this shell without `PYTHONPATH=src`.
  The package imports successfully with `PYTHONPATH=src`, and pytest uses the repo's configured
  `pythonpath = ["src"]`.
- Codex did not create `reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P09/**`, `review.md`, or
  `verdict.json`; review is Ralph/Claude-owned after this executor step.
- Codex did not mark the phase PASS.
