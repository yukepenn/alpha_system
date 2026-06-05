# FLF-P10 Handoff - Session / Calendar / Roll Feature Families

## Summary

Implemented the additive Session / Calendar / Roll feature family under
`src/alpha_system/features/families/session/`. The family builds FLF-P06
`FeatureSpec` / `FeatureVersion` definitions only after the FLF-P05 governed
FeatureRequest gate admits an approved `freq_` request and consumes the
governance duplicate-exposure guard. Computation returns in-memory
`FeatureValueRecord` tuples only; no values are materialized or persisted.

Covered features:

- `session_id`
- `minutes_from_rth_open`
- `minutes_to_rth_close`
- `rth_segment_flag`
- `eth_segment_flag`
- `day_of_week`
- `bars_to_roll`
- `minutes_to_roll`
- `minutes_to_expiration`
- `halt_status_flag`

Expiration and status metadata are optional and fail closed to `None` with
`expiration_metadata_absent` / `status_metadata_absent` flags when absent. Dense
synthetic no-trade rows keep session/calendar values but retain `no_trade` and
add `synthetic_no_trade_position_only`, so they are not treated as real trade
bars.

## Files For Ralph To Stage

Codex staged no files per executor override. Recommended commit-eligible files
for Ralph's explicit staging:

- `src/alpha_system/features/families/session/__init__.py`
- `src/alpha_system/features/families/session/family.py`
- `tests/unit/features/families/session/test_session_family.py`
- `docs/feature_label_foundation/features/session.md`
- `configs/features/families/session/README.md`
- `handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P10.md`
- `README.md`

No `runs/` path is included in this list.

## Validation Results

- `test -f runs/2026-06-05T131433Z_ALPHA_FEATURE_LABEL_FOUNDATION_V1/STOP` -
  exit 1; STOP file absent, so execution proceeded.
- `git status --short` - skipped because the user override explicitly forbids
  Codex from running `git status`.
- `python -c "import alpha_system.features.families.session"` - failed in this
  shell with `ModuleNotFoundError: No module named 'alpha_system'` because the
  package is not installed and the bare command does not set `PYTHONPATH`.
- `PYTHONPATH=src python -c "import alpha_system.features.families.session"` -
  passed.
- `python -m pytest tests/unit/features/families/session -q` - passed,
  `7 passed in 0.08s`.
- `python -m ruff check src/alpha_system/features/families/session tests/unit/features/families/session`
  - passed, `All checks passed!`.
- `python tools/verify.py --smoke` - passed, exit 0.
- `python tools/hooks/canary_runner.py` - passed; all Frontier canaries passed.
- `test -f docs/feature_label_foundation/features/session.md` - passed.
- `test -f handoffs/ALPHA_FEATURE_LABEL_FOUNDATION_V1/FLF-P10.md` - passed
  after this handoff was written.
- `git ls-files runs` - passed with empty output.

## Artifact Policy

No raw provider files, canonical data files, feature values, label values,
provider responses, SQLite/DB/WAL files, logs, caches, parquet/arrow/feather,
model binaries, or heavy artifacts were created. No run-local `handoff.md`,
`review.md`, or `verdict.json` was created. `git ls-files runs` returned empty.

## Explicit Staging Confirmation

Codex did not run `git add`, `git commit`, `git push`, `git diff`, or
`git status`. No files were staged by Codex. Ralph owns authoritative staging,
commit, validation ledger, review, verdict, PR, CI, and merge handling.

## DAG Metadata Confirmation

The implementation stayed within the FLF-P10 additive family paths plus the
required family doc, config placeholder, handoff, and concise README snapshot.
No shared feature/label core, sibling feature family, `labels/**`,
`governance/**`, or `ACTIVE_CAMPAIGN.md` file was edited. The session family
paths are disjoint from sibling Wave 1 family paths; `README.md` remains the
shared serial-merge snapshot file called out by the spec.

## Forbidden Scope Confirmation

No live trading, paper trading, broker operation, order routing, account scope,
strategy/backtest/portfolio code, production deployment, external Databento or
IBKR provider call, raw-provider access, alpha search, or alpha/profitability/
tradability claim was added. The implementation consumes canonical in-memory
rows and optional accepted-DatasetVersion metadata only.
