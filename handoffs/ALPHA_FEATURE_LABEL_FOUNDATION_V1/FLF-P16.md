# FLF-P16 Handoff — LabelSpec and LabelVersion Contracts

## Change Summary

Implemented the FLF-P16 label-layer contract surface.

The phase adds:

- `alpha_system.labels.version`, a contract-only module with frozen/hashable
  `LabelContractSpec`, `LabelVersion`, `LabelInputSpec`, `LabelHorizonSpec`,
  `LabelPathSpec`, `BarrierSpec`, `CostAdjustmentSpec`,
  `LabelAvailabilityPolicy`, `LabelLineageRecord`, `LabelFamily`, and
  `LabelValueRecord`.
- Deterministic `LabelVersion` ids as `lver_<64-hex-content-hash>` over the
  canonical label contract payload.
- A required governance `LabelSpec` (`lspec_`) binding for `LabelContractSpec`.
  The contract adapts governed horizon, path rules, cost model,
  target/stop rules, availability time, forbidden feature overlap, and leakage
  checks.
- `LabelValueRecord` validation requiring `label_available_ts` and rejecting
  value rows whose availability precedes event time, horizon-end time, or the
  governed `LabelSpec.availability_time`.
- Label-as-feature and lookahead feature-reference rejection through the
  existing `alpha_system.governance.label_leakage_guard.check_label_leakage`
  guard.
- Additive wiring through `alpha_system.labels.families`.
- Scoped unit tests and durable docs at
  `docs/feature_label_foundation/LABEL_CONTRACTS.md`.
- A compact README snapshot update marking FLF-P16 complete after merge and
  FLF-P17 as next.

No concrete label family, label materialization, label store, label registry,
label values, raw/canonical data reads, provider calls, or research claims were
added.

## Staging / Curated File List

Staged by Codex: none. The executor prompt explicitly prohibited `git add`,
`git commit`, `git push`, `git status`, and `git diff`; all changes are left
unstaged for Ralph.

Curated files for Ralph to stage by explicit path:

- `src/alpha_system/labels/version.py`
- `src/alpha_system/labels/families/__init__.py`
- `tests/unit/labels/test_label_contracts.py`
- `docs/feature_label_foundation/LABEL_CONTRACTS.md`
- `README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P16.md`

No review artifacts were created by Codex because the executor prompt
explicitly forbade calling Claude, running reviewer, and creating `review.md` or
`verdict.json`. YELLOW review remains Ralph-owned.

## Validation Results

- `git status --short`: not run; explicitly forbidden by executor prompt.
- `python -c "import alpha_system.labels.version"`: failed with
  `ModuleNotFoundError: No module named 'alpha_system'` because bare
  `python -c` does not put `src/` on `PYTHONPATH` in this checkout.
- `python -c "import alpha_system.labels.families"`: failed with
  `ModuleNotFoundError: No module named 'alpha_system'` for the same bare
  `python -c` environment reason.
- `PYTHONPATH=src python -c "import alpha_system.labels.version"`: passed.
- `PYTHONPATH=src python -c "import alpha_system.labels.families"`: passed.
- `PYTHONPATH=src python -c "import alpha_system.labels.version; import alpha_system.labels.families"`:
  passed after the final import-format cleanup.
- `python tools/verify.py --smoke`: passed.
- `PYTHONPATH=src python -m pytest tests/unit/labels/test_label_contracts.py -q`:
  passed, 8 tests.
- `python -m pytest tests/unit/labels -q`: passed, 9 tests.
- `test -f docs/feature_label_foundation/LABEL_CONTRACTS.md`: passed.
- `python tools/hooks/canary_runner.py`: passed; all Frontier canaries passed.
- `git ls-files runs`: passed; output empty.
- `PYTHONPATH=src python -m ruff check src/alpha_system/labels/version.py src/alpha_system/labels/families/__init__.py tests/unit/labels/test_label_contracts.py`:
  passed after import ordering cleanup.
- `find . -path './.git' -prune -o \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' -o -name '*.dbn' -o -name '*.zst' -o -name '*.wal' -o -name '*.journal' \) -print`:
  passed; output empty.
- `rg -n "ALPHA_VALIDATED|STRATEGY_READY|LIVE_READY|PROFITABLE|TRADABLE|PRODUCTION_READY" src/alpha_system/labels/version.py src/alpha_system/labels/families/__init__.py tests/unit/labels/test_label_contracts.py docs/feature_label_foundation/LABEL_CONTRACTS.md README.md`:
  passed; no prohibited lifecycle-state terms found.

One local rerun attempt of `git ls-files runs` used a mistyped worktree path and
failed before executing in the repository; the command was rerun in the correct
repository and passed with empty output.

## Artifact Policy Confirmation

- No `runs/**` files were created, staged, or committed by Codex.
- The run-local `runs/<run_id>/phases/FLF-P16/handoff.md`, `review.md`,
  `verdict.json`, checks, and repair artifacts were not created by Codex.
- `git ls-files runs` returned empty.
- No DB, SQLite, WAL, journal, parquet, arrow, feather, `.dbn`, `.zst`, raw,
  canonical, cache, log, provider-response, feature-value, label-value, report
  bundle, or heavy artifact path is in the curated file list.
- Local artifact scan for common forbidden data/DB/heavy suffixes returned
  empty.
- `git diff --cached --name-only` was not run because the executor prompt
  forbade `git diff`; Codex performed no staging, so there is no Codex-staged
  set to inspect.
- Explicit staging only is confirmed for the Ralph driver: the curated file
  list above contains no `runs/` path.

## DAG / Scope Confirmation

- FLF-P16 is `parallel_safe=false`, `must_run_alone=true`, merge group
  `label_families`; this phase was treated as run-alone.
- `ACTIVE_CAMPAIGN.md` was not edited.
- Existing core label modules were not edited:
  `src/alpha_system/labels/spec.py`, `contracts.py`, `generation.py`,
  `store.py`, `path_metrics.py`, `alignment.py`, `validation.py`, `engine.py`,
  `registry.py`, `leakage_audit.py`, `reports.py`, and `__init__.py`.
- Governance modules were not edited.
- Governance was consumed, not duplicated: `LabelContractSpec` requires a
  validated `alpha_system.governance.label_spec.LabelSpec` and delegates
  live-feature leakage checks to
  `alpha_system.governance.label_leakage_guard.check_label_leakage`.
- The README snapshot was updated compactly with FLF-P16 progress, FLF-P17 as
  next, the new label contract module/doc, and unchanged safety boundaries.
- No external provider call, raw provider data access, broker/live/paper/order
  routing/account behavior, PR creation, merge, deployment, destructive cleanup,
  or reviewer invocation was performed.
- No alpha, profitability, tradability, IC, strategy, backtest, portfolio,
  broker, live, paper, deployment, or production-readiness claim was
  introduced.

## Review Status

Fresh Claude Opus review is required for this YELLOW phase, but Codex did not
call Claude or create review artifacts because the executor prompt forbade
those actions. Ralph owns review, verdict parsing, staging, commit, PR, CI,
merge gate, and semantic done-check.
