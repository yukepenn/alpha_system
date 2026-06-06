# RT-P12 Handoff — Simple Signal Probe Runtime

Campaign: `ALPHA_RESEARCH_RUNTIME_MVP`  
Phase: `RT-P12` - Simple Signal Probe Runtime  
Executor: Codex  
Status: implementation complete; review not run by executor

## Scope Completed

- Added `alpha_system.runtime.probe` with lazy package exports.
- Added immutable `SignalProbeSpec` / `SignalProbeReport` contracts with
  explicit `fast_path`, `not_strategy_validation`, `not_a_candidate`, and
  `not_a_backtest` framing.
- Enforced bounded threshold neighborhoods, required `CostStressSpec` with
  `double_cost`, required resolved `RuntimeInputPack` binding, feature/label
  pack binding, `available_ts` / `label_available_ts` checks, and locked
  partition governance metadata checks.
- Added next-bar / explicit delayed fill logic that rejects same-bar fill
  policies and rejects fills before signal availability.
- Added `run_signal_probe`, which builds scalar position/trade/turnover,
  expectancy proxy, drawdown proxy, and threshold-neighborhood stability
  summaries while delegating cost stress only through
  `alpha_system.runtime.cost.build_cost_sensitivity_report`.
- Added focused unit tests and the dedicated no-lookahead fill test.
- Added `docs/research_runtime/SIGNAL_PROBE.md`, a synthetic-safe config
  template, tiny documented synthetic fixture rows, and the required README
  snapshot.

## Files For Ralph Staging

Codex staged no files. Per executor instructions, Ralph should stage only these
commit-eligible paths if accepting this phase:

- `src/alpha_system/runtime/probe/__init__.py`
- `src/alpha_system/runtime/probe/fills.py`
- `src/alpha_system/runtime/probe/report.py`
- `src/alpha_system/runtime/probe/runner.py`
- `src/alpha_system/runtime/probe/spec.py`
- `tests/unit/runtime/probe/test_signal_probe_runtime.py`
- `tests/no_lookahead/research_runtime/test_signal_probe_fills.py`
- `tests/fixtures/runtime/probe/README.md`
- `tests/fixtures/runtime/probe/synthetic_signal_probe_rows.json`
- `docs/research_runtime/SIGNAL_PROBE.md`
- `configs/runtime/probe/default_signal_probe.json`
- `README.md`
- `handoffs/ALPHA_RESEARCH_RUNTIME_MVP/RT-P12.md`

No `runs/` path is included. No
`reviews/ALPHA_RESEARCH_RUNTIME_MVP/RT-P12/**` files were created by Codex;
fresh review and verdict artifacts are owned by Ralph/reviewer.

## Git Visibility

- `git status --short`: not run. The executor prompt explicitly forbids Codex
  from running `git status`.
- `git diff` / `git diff --cached --name-only`: not run. The executor prompt
  explicitly forbids Codex from running `git diff`, and Codex staged no files.
- Codex did not run `git add`, `git commit`, `git push`, create a PR, merge,
  call Claude, run reviewer, create `review.md`, or create `verdict.json`.

## Validation

- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/STOP`
  - Result: exit 1; no run-level STOP marker found.
- `test -f runs/2026-06-06T031044Z_ALPHA_RESEARCH_RUNTIME_MVP/phases/RT-P12/STOP`
  - Result: exit 1; no phase-level STOP marker found.
- `python -m ruff format src/alpha_system/runtime/probe tests/unit/runtime/probe tests/no_lookahead/research_runtime/test_signal_probe_fills.py`
  - Result: exit 0. Initial run reformatted 3 files; final run reformatted 1
    file after a small patch.
- `python -m ruff check src/alpha_system/runtime/probe tests/unit/runtime/probe tests/no_lookahead/research_runtime/test_signal_probe_fills.py`
  - Result: initial exit 1 for import ordering and one long line; fixed.
    Final result: exit 0, `All checks passed!`.
- `python -c "import alpha_system.runtime.probe"`
  - Result: exit 1, `ModuleNotFoundError: No module named 'alpha_system'`.
  - Reason: this executor shell does not put `src` on `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.runtime.probe"`
  - Result: exit 0.
- `python tools/verify.py --smoke`
  - Result: exit 0.
- `python -m pytest tests/unit/runtime/probe tests/no_lookahead/research_runtime -q`
  - Result: exit 0, `13 passed in 0.14s` on the final run.
- `test -f docs/research_runtime/SIGNAL_PROBE.md`
  - Result: exit 0.
- `git ls-files runs`
  - Result: exit 0, empty output.
- `find tests/fixtures/runtime/probe -type f -size +1M`
  - Result: exit 0, empty output.
- `python -m pytest tests/unit/runtime -q`
  - Result: exit 0, `146 passed in 0.38s`.
- `python tools/hooks/canary_runner.py`
  - Result: exit 0, all Frontier canaries passed.

Skipped:

- `git status --short`
  - Reason: explicitly forbidden by the executor safety override.
- Staged-set inspection with `git diff --cached --name-only`
  - Reason: explicitly forbidden by the executor safety override, and Codex did
    not stage any files.
- `python tools/verify.py --all`
  - Reason: no shared runtime contract or primitive package was edited; narrow
    probe/no-lookahead checks, broader `tests/unit/runtime`, smoke, scoped
    lint, and canaries passed. Ralph owns broader merge-gate validation.
- Claude review, `review.md`, and `verdict.json`
  - Reason: explicitly forbidden by the executor safety override; Ralph owns
    reviewer orchestration and verdict parsing.

## Artifact Audit

- `git ls-files runs` returned empty output.
- No `runs/**` artifact was created or edited by Codex.
- No review artifacts were created by Codex.
- No files were staged by Codex; therefore this executor introduced no staged
  `runs/` path and no staged forbidden heavy/data/cache/log/DB artifact.
- The only fixture files added under `tests/fixtures/runtime/probe/` are tiny
  documented synthetic rows and a README. The `find ... -size +1M` check
  returned empty.
- No raw/canonical/feature/label/runtime value artifact, local DB, parquet,
  arrow, feather, DBN, ZST, log, cache bundle, model binary, broker, live,
  paper, or order-routing file is in the Ralph staging list above.

## Scope Confirmation

- The probe consumes `runtime.cost` by import and delegates cost stress through
  `build_cost_sensitivity_report`; it does not import `backtest.*` directly.
- The probe consumes runtime contracts, input resolver handles, diagnostics
  references, and cost reports by import. No consumed primitive package was
  edited.
- No files under `src/alpha_system/governance/**`, `experiments/**`,
  `backtest/**`, `research/**`, `features/**`, `labels/**`, `data/**`,
  `signals/**`, `strategies/**`, `portfolio/**`, `management/**`, broker,
  live, paper, order-routing, raw/canonical data, metadata DB, or artifacts
  paths were edited by Codex.
- The report is descriptive and non-promotional. It carries explicit
  limitations and states that the probe is not strategy validation, not a
  candidate, not a backtest, and not a promotion basis.
- No alpha, tradability, profitability, strategy, paper, live, broker,
  production, portfolio, order, or account claim was introduced.

## README Snapshot

`README.md` now records that `ALPHA_RESEARCH_RUNTIME_MVP` has entered Wave 2
sequential `integration` after the merged Wave 1 diagnostics fan-out; active
phase `RT-P12`; next phase `RT-P13`; new durable module
`alpha_system.runtime.probe`; new doc
`docs/research_runtime/SIGNAL_PROBE.md`; synthetic-safe config under
`configs/runtime/probe/`; and unchanged local-first, accepted-DatasetVersion,
availability, no-provider, no-broker/live/paper/order/account, local-only
artifact, and non-promotional boundaries. No CLI surface was added.

## Caveats

- The exact import command in the generated spec fails in this executor shell
  unless `PYTHONPATH=src` is supplied. The same import passes with
  `PYTHONPATH=src`, and pytest uses the project `pythonpath = ["src"]`
  configuration.
- Formal `RejectionReasonRecord`, unified runtime decision states, and the
  `NoLookaheadRuntimeAudit` object remain later-phase scope (`RT-P15` and
  `RT-P14` respectively). This phase emits probe-local reasons only.
