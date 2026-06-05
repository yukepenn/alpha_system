# FLF-P18 Handoff - Cost-Adjusted / Spread-Adjusted Labels

## Change Summary

Implemented the FLF-P18 additive label family under
`alpha_system.labels.families.cost_adjusted`.

The phase adds:

- `cost_adjusted_fwd_ret`, a BBO mid-to-mid forward-return label adjusted by a
  governed `CostAdjustmentSpec` spread model plus explicit `fixed_cost_bps`.
- `spread_adjusted_fwd_ret`, a BBO mid-to-mid forward-return label adjusted by
  the governed spread model only.
- `CostAdjustedLabelDefinition` and family-specific spec wrappers around the
  FLF-P16 `LabelContractSpec`; governance `LabelSpec` records are consumed via
  `LabelContractSpec.from_label_spec(...)` and are not duplicated.
- In-memory compute functions that return `LabelValueRecord` tuples only. Every
  value record carries `label_available_ts`.
- Fail-closed BBO handling through FLF-P04 quote semantics: missing,
  quarantined, invariant-broken, and missing exact-horizon terminal BBO rows
  return `None` with quality flags and are not forward-filled.
- Synthetic dense-grid no-trade anchor handling via FLF-P04 semantics:
  canonical no-trade rows are flagged as `synthetic_no_trade` / `no_trade` and
  are not treated as trade bars.
- Scoped synthetic unit tests, family docs, a config placeholder, and a compact
  README snapshot update.

No label values were materialized, registered, persisted, or exposed as live
features.

## Staging / Curated File List

Staged by Codex: none. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

Curated files for Ralph to stage by explicit path:

- `src/alpha_system/labels/families/cost_adjusted/__init__.py`
- `src/alpha_system/labels/families/cost_adjusted/family.py`
- `tests/unit/labels/families/cost_adjusted/test_cost_adjusted_family.py`
- `docs/feature_label_foundation/labels/cost_adjusted.md`
- `configs/labels/families/cost_adjusted/README.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P18.md`

No review artifacts were created by Codex because the executor prompt
explicitly forbade calling Claude, running reviewer, and creating `review.md`
or `verdict.json`. YELLOW review remains Ralph-owned.

## Validation Results

- `git status --short`: not run; explicitly forbidden by executor prompt.
- `python -c "import alpha_system.labels.families.cost_adjusted"`: failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because bare
  `python -c` does not put `src/` on `PYTHONPATH` in this checkout.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -c "import alpha_system.labels.families.cost_adjusted"`:
  passed.
- `python tools/verify.py --smoke`: passed.
- `python -m pytest tests/unit/labels/families/cost_adjusted -q`: passed, 6
  tests.
- `test -f docs/feature_label_foundation/labels/cost_adjusted.md`: passed.
- `git ls-files runs`: passed; output empty.
- Optional `python -m pytest tests/no_lookahead/feature_label -q`: passed, 5
  tests.
- Optional `python tools/hooks/canary_runner.py`: not run; left to Ralph because
  the executor prompt requested narrow, spec-scoped validation and Ralph owns
  broader validation orchestration.

Read-only cleanup/inspection notes:

- Phase-owned Python `__pycache__` directories created by import/pytest runs
  were removed from the new source/test directories before handoff.
- A read-only scan of the new Python files found no overlong lines after final
  wrapping.
- A read-only scan for prohibited lifecycle-state tokens in the curated phase
  paths and README returned no matches.

## Artifact Policy Confirmation

- No `runs/**` files were created, edited, staged, or committed by Codex.
- The run-local `runs/<run_id>/phases/FLF-P18/handoff.md`, `review.md`,
  `verdict.json`, checks, and repair artifacts were not created by Codex.
- `git ls-files runs` returned empty.
- No DB, SQLite, WAL, journal, parquet, arrow, feather, `.dbn`, `.zst`, raw,
  canonical, cache, log, provider-response, feature-value, label-value, report
  bundle, or heavy artifact path is in the curated file list.
- `git diff --cached --name-only` was not run because the executor prompt
  forbade `git diff`; Codex performed no staging, so there is no Codex-staged
  set to inspect.
- Explicit staging only is confirmed for the Ralph driver: the curated file
  list above contains no `runs/` path.

## DAG / Scope Confirmation

- FLF-P18 is `parallel_safe=true`, `must_run_alone=false`, merge group
  `label_families`; the implementation stayed within the phase-owned
  `cost_adjusted` family paths plus the spec-authorized README snapshot and
  handoff.
- `ACTIVE_CAMPAIGN.md` was not edited.
- No shared label core file was edited: `src/alpha_system/labels/spec.py`,
  `contracts.py`, `generation.py`, `path_metrics.py`, `store.py`,
  `alignment.py`, `validation.py`, `version.py`, `engine.py`, `registry.py`,
  `leakage_audit.py`, `reports.py`, `__init__.py`, and
  `labels/families/__init__.py` were not changed.
- No feature module, governance module, other label family, broker/live/paper
  path, provider path, or data path was edited.
- Governance was consumed, not duplicated: definitions require a governed
  `alpha_system.governance.label_spec.LabelSpec` and build the family contract
  through `alpha_system.labels.version.LabelContractSpec.from_label_spec(...)`.
- `CostAdjustmentSpec` is consumed from the FLF-P16 label contract and its
  governed `cost_model` is the only cost/spread parameter source.
- Every computed `LabelValueRecord` carries `label_available_ts`; labels are not
  exposed as live features.
- The README snapshot was updated compactly with FLF-P18 progress, the new
  `cost_adjusted` label family, the new label-family doc, and unchanged safety
  boundaries.

## Forbidden Scope / Claims Confirmation

- No live trading, paper trading, broker operation, order routing, account
  access, production deployment, PR creation, merge, or reviewer invocation was
  performed.
- No external Databento, IBKR, or other provider API was called; no raw
  provider file or provider response was read.
- No raw/canonical/factor/feature/label value, local registry DB, report bundle,
  cache, model, or heavy artifact was added.
- No strategy, backtest, portfolio, fill, execution, alpha-search, tradability,
  profitability, or production-readiness behavior or claim was introduced.

## Review Status

Fresh Claude Opus review is required for this YELLOW phase, but Codex did not
call Claude or create review artifacts because the executor prompt forbade
those actions. Ralph owns review, verdict parsing, staging, commit, PR, CI,
merge gate, and semantic done-check.
