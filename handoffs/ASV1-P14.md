# ASV1-P14 Handoff — Signal Store and StrategySpec Layer

## Summary

Implemented the ASV1-P14 signal and strategy foundations:

- `SignalRecord` / `SignalSpec` schemas with timing and provenance metadata.
- Local-only signal JSONL serialization and `LocalSignalStore`.
- `StrategySpec` with declared factor dependencies, allowed signal-intent outputs, and forbidden responsibility enforcement.
- Deterministic single-factor threshold template strategy producing signal intent only.
- Strategy version registration using existing `strategy_registry` and `strategy_versions` tables in temp SQLite tests only.
- Docs, small config example, strategy authoring placeholders, and required tests.

## StrategySpec Boundaries

Allowed outputs are entry signal, exit signal, direction, optional confidence score, optional desired exposure, and required factor dependencies.

Explicitly excluded from StrategySpec and validated in tests: account equity, position sizing, fills, order lifecycle, slippage, commission, partial take-profit accounting, and portfolio aggregation.

No management, portfolio, execution, broker, live, paper, order-routing, fill, cost, or backtest implementation was introduced.

## Dependency And Leakage Validation

Strategies validate inputs against declared factor ids and factor versions. Missing dependencies, undeclared factor ids, and mismatched factor versions are rejected.

Labels are rejected as live strategy dependencies or input fields. Raw ad hoc columns outside the factor value schema are rejected.

## No-Lookahead Timing

Signal validation enforces:

- `signal.available_ts >= signal.event_ts`
- `signal.available_ts >= max(input_factor.available_ts)`
- declared signal factor versions match input factor value versions

## Registry Integration

`register_strategy_spec()` writes strategy identity/version rows only to caller-provided temp/local SQLite paths outside the repository. It uses the existing ASV1-P05 `strategy_registry` and `strategy_versions` tables and does not add migrations.

## Validation

Commands run:

- `python -m pytest tests/unit/test_signal_schema.py tests/unit/test_strategy_spec_fields.py tests/unit/test_strategy_forbidden_responsibilities.py` — PASS, 5 passed.
- `python -m pytest tests/no_lookahead/test_strategy_no_label_inputs.py tests/no_lookahead/test_strategy_no_raw_adhoc_inputs.py tests/no_lookahead/test_signal_available_ts.py` — PASS, 5 passed.
- `python -m pytest tests/unit tests/integration tests/no_lookahead` — initial run found one assertion wording mismatch in `tests/unit/test_signal_artifact_policy.py`; after fixing the assertion, PASS, 333 passed.
- `python -m compileall src` — PASS.
- `python -m ruff check src tests || true` — best-effort command could not run because `ruff` is not installed: `/usr/bin/python: No module named ruff`.
- `python -m mypy src || true` — best-effort command could not run because `mypy` is not installed: `/usr/bin/python: No module named mypy`.

Artifact audit commands:

- `git status --short` — showed only ASV1-P14 allowed-path untracked files before staging.
- `find data -path "*signals*" -type f -print || true` — no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — no output.
- `find . -path ./tests/fixtures -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print` — no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` — no output.
- `git ls-files runs` — no output.
- `git diff --cached --name-only` — no output at handoff-writing time.

No tests were skipped.

## Artifact Policy Confirmation

No generated signal store, SQLite DB, Parquet, Arrow, Feather, log, cache, raw data, canonical data, factor data, label data, metadata DB, or heavy artifact was committed.

Signal store and registry integration tests write only under pytest temp paths outside the repository. `runs/**` remains local-only and untracked; no run-local handoff, review, verdict, checks, or repair artifact was staged or committed.

## Staging Confirmation

No `git add .`, no `git add -A`, and no force push were used. At handoff-writing time no files were staged, and `git diff --cached --name-only` returned empty.

## Known Limitations

- Only the scoped deterministic single-factor threshold template is implemented.
- No backtest, execution, management, portfolio, order lifecycle, fill, slippage, or commission behavior is implemented by design.
- Static `ruff` and `mypy` checks could not run because those modules are not installed in this environment.
- Fresh Claude review, verdict parsing, done-check, PR, CI, and merge gates remain Ralph-owned and were not run by Codex.

## Review Focus

Review should focus on domain boundary enforcement, no-lookahead signal timing, label/raw-input rejection, temp-only registry/store behavior, artifact policy, and confirming that StrategySpec remains signal-intent only.
