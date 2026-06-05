# FLF-P17 Handoff — Fixed-Horizon and Midprice Forward Labels

## Change Summary

Implemented the additive FLF-P17 fixed-horizon label family under
`alpha_system.labels.families.fixed_horizon`.

The phase adds:

- governed label definitions for `fwd_ret_1m`, `fwd_ret_3m`, `fwd_ret_5m`,
  `fwd_ret_10m`, `fwd_ret_30m`, `mid_fwd_ret_1m`, `mid_fwd_ret_3m`,
  `mid_fwd_ret_5m`, `mid_fwd_ret_10m`, and `mid_fwd_ret_30m`;
- `LabelContractSpec` / `LabelInputSpec` / future offline `WindowSpec`
  construction from an existing governance `LabelSpec` with an `lspec_` id;
- deterministic `LabelVersion` derivation for every definition;
- in-memory `LabelValueRecord` calculation with `label_available_ts` derived
  from the horizon terminal row availability and the governed
  `LabelSpec.availability_time`;
- trade-close forward returns that treat `no_trade` rows as gaps;
- midprice forward returns that flag `missing_bbo`, `bbo_quarantined`, and BBO
  invariant gaps without forward fill or interpolation;
- row-free family config metadata and durable family documentation;
- scoped synthetic unit tests for supported labels and fail-closed paths.

No materialized label values, raw/canonical data files, provider calls, registry
writes, feature exposure, broker/live/paper/order/account behavior, PR, merge,
review, verdict, or research claim was added.

## Staging / Curated File List

Staged by Codex: none. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

Curated files for Ralph to stage by explicit path:

- `src/alpha_system/labels/families/fixed_horizon/__init__.py`
- `src/alpha_system/labels/families/fixed_horizon/family.py`
- `tests/unit/labels/families/fixed_horizon/test_fixed_horizon_family.py`
- `configs/labels/families/fixed_horizon/README.md`
- `configs/labels/families/fixed_horizon/horizons.yaml`
- `docs/feature_label_foundation/labels/fixed_horizon.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P17.md`

`README.md` was intentionally not edited by Codex during this parallel build.
Per the phase spec, the README snapshot is a serialized merge-checkpoint update
owned by Ralph after this phase is rebased onto current `main`.

No review artifacts were created by Codex because the executor prompt
explicitly forbade calling Claude, running reviewer, creating `review.md`,
creating `verdict.json`, creating a PR, or marking the phase PASS.

## Validation Results

- STOP check:
  `test -f runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/STOP ...`:
  passed; output `no STOP`.
- `git status --short`: not run; explicitly forbidden by executor prompt.
- `git ls-files runs`: passed; output empty.
- `python -c "import alpha_system.labels.families.fixed_horizon"`: failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because bare `python -c`
  does not put `src/` on `PYTHONPATH` in this checkout.
- `PYTHONPATH=src python -c "import alpha_system.labels.families.fixed_horizon"`:
  passed.
- `python -m pytest tests/unit/labels/families/fixed_horizon -q`: passed,
  7 tests.
- `PYTHONPATH=src python -m pytest tests/unit/labels/families/fixed_horizon -q`:
  passed, 7 tests.
- `PYTHONPATH=src python -m ruff check src/alpha_system/labels/families/fixed_horizon tests/unit/labels/families/fixed_horizon`:
  passed.
- `python -m pytest tests/no_lookahead/feature_label -q`: passed, 5 tests.
- `python tools/verify.py --smoke`: passed; command exited 0.
- `python tools/hooks/canary_runner.py`: passed; all Frontier canaries passed.
- `test -f docs/feature_label_foundation/labels/fixed_horizon.md`: passed.
- Boundary heuristic:
  `grep -REn "\.dbn|\.zst|read_parquet|pyarrow|databento|ib_insync|\.feather" src/alpha_system/labels ...`:
  passed; output `no direct provider/file readers found in label code`.
- Local forbidden artifact suffix scan for SQLite/DB/WAL/journal/parquet/arrow/
  feather/DBN/Zstd/numpy files: passed; output empty.
- Prohibited lifecycle-state scan over the FLF-P17 source/test/doc/config paths:
  passed; no matches.

One attempted `rm -rf` cleanup of generated `__pycache__` directories was
blocked by sandbox policy. The generated `.pyc` files were then removed with
targeted `find -delete`, and the empty cache directories were removed with
`rmdir`. A final scoped file scan showed only the curated source, test, doc,
and config files listed above.

## Artifact Policy Confirmation

- Codex staged nothing and committed nothing.
- `git ls-files runs` returned empty.
- No `runs/**` files were created by Codex.
- No run-local `handoff.md`, `review.md`, `verdict.json`, checks, or repair
  attempt artifacts were created by Codex.
- No raw/canonical market data, provider responses, materialized feature values,
  materialized label values, heavy artifacts, local DB/registry files, caches,
  logs, report bundles, `.dbn`, `.zst`, parquet, arrow, feather, `.npy`, or
  `.npz` files are in the curated file list.
- `git diff --cached --name-only` was not run because the executor prompt
  forbade `git diff`; Codex performed no staging, so there is no Codex-staged
  set to inspect.
- Explicit staging remains Ralph-owned; Ralph should stage only the curated
  paths above by explicit path.

## DAG / Scope Confirmation

- FLF-P17 is parallel-safe and writes only the disjoint fixed-horizon label
  family source, tests, docs, configs, and this handoff during the parallel
  build.
- `ACTIVE_CAMPAIGN.md` was not edited.
- `README.md` was not edited during the parallel build; the serialized README
  snapshot remains a Ralph-owned merge-checkpoint action per spec.
- Shared label core was consumed and not edited:
  `labels/spec.py`, `labels/contracts.py`, `labels/generation.py`,
  `labels/path_metrics.py`, `labels/store.py`, `labels/alignment.py`,
  `labels/validation.py`, `labels/version.py`, `labels/engine.py`,
  `labels/registry.py`, `labels/leakage_audit.py`, `labels/reports.py`,
  `labels/__init__.py`, and `labels/families/__init__.py` were not changed.
- Governance modules were consumed and not edited. The family requires a
  governed `LabelSpec` and delegates label-as-feature checks through the
  FLF-P16 `LabelContractSpec` / governance leakage-guard path.
- Feature modules were consumed and not edited. The family consumes canonical
  input views and FLF-P04 semantics only.
- No other label family directory was edited.
- No external Databento/IBKR provider call, raw provider file read, broker,
  live, paper, order routing, account, strategy, backtest, portfolio,
  production deployment, PR creation, merge, or destructive cleanup was
  performed.
- No alpha, profitability, tradability, promotion, broker, live, paper,
  deployment, or production-readiness claim was introduced.

## Review Status

Fresh Claude Opus review is required for this YELLOW phase, but Codex did not
call Claude or create review artifacts because the executor prompt forbade
those actions. Ralph owns review, verdict parsing, staging, commit, PR, CI,
merge gate, semantic done-check, and the serialized README snapshot.
