# ASV1-P12 Handoff

## Phase

- Phase ID: `ASV1-P12`
- Phase name: Intraday Factor Diagnostics Engine
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p12-intraday-factor-diagnostics-engine`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P12` (local-only)

## Scope Completed

Implemented the scoped Tier 0 intraday factor diagnostics engine:

- research metric modules for IC, buckets, event triggers, regimes, execution filters, management features, stability, and factor correlation;
- study config and output models with compact JSON summary and manifest serialization;
- no-lookahead factor/label alignment over versioned factor values and labels;
- optional temp/local registry recording into `study_runs` and `factor_validation_runs`;
- `alpha study run` CLI wiring;
- fixture-only example study config;
- factor diagnostics documentation;
- required unit, no-lookahead, and integration tests.

No strategy backtest, execution engine, broker, paper/live trading, order routing, production deployment, candidate promotion, reviewer call, `review.md`, `verdict.json`, PR creation, merge, or PASS marking was performed.

Scope note: exposing the new CLI group through the existing command shell requires `src/alpha_system/cli/main.py`. The generated commit-eligible allowed-path list omitted that file while also requiring `alpha study run --help`. I made the minimal registration change so tests and `PYTHONPATH=src python -m alpha_system.cli study run --help` work, but this path omission is a scope contradiction that must be resolved before commit/staging.

## Diagnostic Coverage

| Category | Implemented diagnostics |
| --- | --- |
| Directional continuous | Pearson IC, Rank IC, IC by horizon, IC decay, IC by day/week/month, ICIR |
| Nonlinear buckets | bucket forward returns, bucket monotonicity, tail expectancy, U-shape profile, extreme bucket hit rate, MFE/MAE by bucket |
| Event triggers | event study, conditional forward returns, sample size, false breakout rate, target-before-stop probability, post-event MFE/MAE |
| Regime filters | with-filter vs without-filter uplift, coverage, false rejection rate, conditional improvement statistics |
| Execution filters | spread, liquidity, slippage, volume participation sensitivity, adverse selection proxy |
| Management features | target-before-stop, time-to-target, time-to-stop, breakeven usefulness, trailing stop usefulness |
| Stability/correlation | time-of-day, session-segment, monthly, regime stability, correlation to existing factors |

## CLI Behavior

`alpha study run` accepts a JSON study config plus scoped overrides for factor/label/data versions, factor/label JSONL paths, horizon, date/session/instrument selectors, output dir, registry path, manifest path, and minimum sample-size threshold.

Outputs are local diagnostic artifacts:

- `diagnostic_summary.json`
- `run_manifest.json`
- optional temp/local registry rows

The command records `decision_status = diagnostic_recorded`; this is diagnostics bookkeeping only and does not promote a candidate.

## Alignment And No-Lookahead

Diagnostics join factor values to labels only when these fields align:

- `factor_id`
- `factor_version`
- `label_id`
- `label_version`
- `data_version`
- `instrument_id`
- `event_ts`
- `session_id`
- optional `horizon_seconds`

The join rejects labels whose `label_available_ts` is before factor `available_ts`. The existing label validation layer also enforces `label_available_ts >= horizon_end_ts` and required path metadata. Tests cover label availability violations, label-version mismatch, session mismatch, and horizon mismatch.

## Warning Behavior

Diagnostics emit warnings for:

- insufficient sample size;
- missing label coverage;
- unstable horizon coverage;
- high missing-factor rate;
- invalid non-matching factor/data version references;
- unsupported diagnostic type.

Warnings are included in the diagnostic summary, manifest, and optional temp/local registry records.

## Registry Integration

When `registry_path` is configured, it must be a temp/local SQLite path outside the repository. The study runner initializes the existing ASV1-P05 registry schema and inserts one row into `study_runs` and one row into `factor_validation_runs`. Tests verify the temp DB writes and that no promotion decision is created.

## Validation Results

Commands run by Codex:

```text
test -f runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - no STOP file was active.

python -m pytest tests/unit tests/integration tests/no_lookahead
PASS - 266 passed.

python -m pytest tests/unit/test_pearson_ic.py tests/unit/test_rank_ic.py tests/unit/test_ic_decay.py tests/unit/test_icir.py
PASS - 7 passed.

python -m pytest tests/unit/test_bucket_monotonicity.py tests/unit/test_bucket_tail_expectancy.py tests/unit/test_event_study_counts.py
PASS - 4 passed.

python -m pytest tests/no_lookahead/test_diagnostics_label_availability.py tests/no_lookahead/test_diagnostics_factor_label_alignment.py
PASS - 4 passed.

python -m alpha_system.cli study run --help
FAIL - exit 1; ModuleNotFoundError: No module named 'alpha_system'. This shell has the repo source uninstalled and no PYTHONPATH set. This is the same src-layout import condition observed in ASV1-P11, but the generated spec marks missing study help as blocking.

PYTHONPATH=src python -m alpha_system.cli study run --help
PASS - help rendered with study run arguments.

python -m compileall src
PASS - exit 0.

git status --short
EXCEPTION - showed ASV1-P12 source/docs/config/tests/handoff paths plus `src/alpha_system/cli/main.py`, which is required for CLI registration but omitted from the generated allowed-path list.

find artifacts/factor_studies -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true
PASS - returned empty.

find metadata -type f ! -name README.md ! -name ".gitkeep" -print
PASS - returned empty.

find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print
PASS - returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

alpha study run --help || true
UNAVAILABLE - console script is not installed in this shell (`alpha: command not found`).

python -m ruff check src tests || true
UNAVAILABLE - `ruff` is not installed.

python -m mypy src || true
UNAVAILABLE - `mypy` is not installed.
```

## Artifact Policy

No full study outputs, generated factor-study directories, local DB files, raw/canonical data, factor/label stores, Parquet/Arrow/Feather files, logs, caches, model files, or run-local artifacts were committed.

`runs/**` remains local-only. `git ls-files runs` returned empty. The run-local handoff was not written or staged. The commit-eligible handoff is this file, `handoffs/ASV1-P12.md`.

No files have been staged or committed by Codex for this phase because of the allowed-path contradiction above and the bare module-help failure. `git diff --cached --name-only` returned empty before handoff completion.

Allowed-path and local-only separation is preserved for local-only artifacts: generated study outputs under `artifacts/factor_studies/**` and `runs/**` are not staged or committed. Commit eligibility needs Ralph or human resolution for the omitted CLI registration path.

## Statistical Limitations

The diagnostics are descriptive statistics over aligned factor/label rows. They do not account for multiple testing, costs, fills, capital, portfolio constraints, execution state, later strategy rules, or review outcomes. Small samples, sparse events, missing path labels, and unstable horizon coverage must be interpreted as warnings, not evidence for deployment.

## Claim Discipline

Outputs and docs state that diagnostics are Tier 0 research evidence only, not strategy PnL truth, not a backtest, not candidate approval, and not tradability evidence. A dedicated test checks the diagnostic summary and docs for unsupported positive claim phrases.

## Risks

- R-001/R-002 lookahead and timestamp ambiguity: mitigated with label availability and horizon-end validation plus no-lookahead tests.
- R-005 factor/label misalignment: mitigated with version, instrument, session, event timestamp, data version, label version, and optional horizon alignment tests.
- R-014/R-034 overclaiming and promotion confusion: mitigated with docs/output language and claim tests.
- R-024/R-036 fixture adequacy: tests use deterministic synthetic rows with positive, negative, missing, and boundary cases.
- R-037 CLI artifact writes: mitigated with tempdir integration and artifact-policy test.
- R-038/R-039 DB/heavy artifacts: artifact scans returned empty.
- R-009 execution truth ambiguity: management and execution-filter modules are diagnostic only and introduce no execution accounting.

Open risk: the exact bare module help command failed in this uninstalled `src`-layout shell. The CLI implementation works with `PYTHONPATH=src`, and subprocess tests verify the command help through that path. Ralph should decide whether to install the package in the validation environment or route repair outside this phase's allowed paths.

Open scope contradiction: `src/alpha_system/cli/main.py` is required for the command to be reachable but is absent from the generated allowed-path list.

## Known Limitations

- Inputs are JSONL factor values and JSONL labels; no new data-layer storage or registry migration was introduced.
- Execution-filter metrics use available diagnostic fields and proxies only; they are not execution simulation.
- Registry writes are temp/local and use existing experiment-style tables.
- The console script `alpha` is unavailable unless the package is installed.
- The command registration change is in `src/alpha_system/cli/main.py`; that file needs allowed-path authorization before staging/commit.

## Review Focus

Please review:

- no-lookahead alignment semantics, especially `available_ts` vs `label_available_ts`;
- whether the bare module help failure should be treated as environment-only or blocking;
- whether `src/alpha_system/cli/main.py` should be admitted as a commit-eligible command registration path;
- diagnostic completeness across required categories;
- output language and claim discipline;
- registry rows and artifact-path policy;
- absence of broker/paper/live/backtest/execution scope creep.
