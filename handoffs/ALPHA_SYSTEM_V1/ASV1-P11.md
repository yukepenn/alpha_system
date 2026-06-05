# ASV1-P11 Handoff

## Phase

- Phase ID: `ASV1-P11`
- Phase name: Factor Compute SDK MVP
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p11-factor-compute-sdk-mvp`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P11` (local-only)

## Scope Completed

Implemented the scoped Factor Compute SDK MVP:

- base factor compute abstractions and required factor-value schema;
- deterministic compute driver over canonical 1-minute bars;
- declared dependency resolution from `FactorSpec.input_fields`;
- rejection of undeclared/ad-hoc columns and label-like fields;
- warmup null/quality-flag behavior;
- session-reset history isolation;
- availability-lag application from input `available_ts`;
- point-in-time-safe normalization helpers;
- quality-flag normalization and source quality propagation;
- local-only JSONL factor-value I/O and small JSON manifests;
- lifecycle-gated materialization with draft blocked by default;
- optional temp/local SQLite registry entry for materialization runs;
- `alpha factor materialize` CLI registration while preserving `validate`;
- factor compute documentation, fixture-only example config, and placeholder factor library roots;
- required unit, no-lookahead, integration, fixture, and artifact-policy tests.

No labels, signals, strategies, backtests, portfolio logic, execution logic,
broker calls, paper/live trading, order routing, production deployment,
reviewer call, `review.md`, `verdict.json`, PR creation, merge, approval, or
promotion was introduced.

## Factor Value Schema Coverage

`src/alpha_system/factors/base.py` defines and enforces the required schema:

```text
factor_id
factor_version
instrument_id
event_ts
available_ts
session_id
bar_index
value
normalized_value
quality_flags
data_version
compute_version
```

`tests/unit/test_factor_value_schema.py` asserts field order and required
metadata. `data_version`, `compute_version`, `code_hash`, and `config_hash` are
recorded in materialization summaries and manifests.

## Dependency Validation

`src/alpha_system/factors/dependencies.py` validates compute dependencies
against `FactorSpec.input_fields` and the canonical 1-minute bar contract.
Only declared `bar` domain inputs are selected for factor implementations.
Missing declared inputs, undeclared implementation fields, non-canonical source
fields, ad-hoc columns, label domains, and label-like fields are rejected.

Labels remain research targets and cannot be factor inputs or strategy inputs.

## Materialization And Lifecycle Policy

`src/alpha_system/factors/materialize.py` supports `dry-run` and
`local-only-persist` output policies. Persistence is blocked unless lifecycle
policy permits it:

- draft materialization is blocked by default;
- candidate materialization is not long-term eligible by default;
- validated factors require reviewed validation evidence in a temp/local registry;
- approved factors additionally require review-backed promotion evidence;
- materialization never approves or promotes a factor.

Outputs are local-only JSONL factor values and JSON run manifests. Default
factor store roots resolve under `/tmp/alpha_system/factors`; explicit output
dirs, manifests, and registry paths must be local WSL paths outside the repo.

## No-Lookahead Timing

The compute driver emits null values with `insufficient_warmup` quality flags
until warmup is satisfied. With `session_reset=True`, history is isolated by
instrument, data version, and session. Availability is computed as input bar
`available_ts + FactorSpec.availability_lag`, preserving late input
availability instead of using future data. Normalization uses only prior values
plus the current value.

Coverage:

- `tests/unit/test_factor_warmup_behavior.py`
- `tests/unit/test_factor_session_reset.py`
- `tests/no_lookahead/test_factor_availability_lag.py`
- `tests/no_lookahead/test_factor_available_ts_propagation.py`
- `tests/no_lookahead/test_label_as_factor_input_rejected.py`

## Example Factor Scope

`configs/factors/examples/correctness_fixture_close_delta.json` is a tiny
synthetic deterministic correctness fixture. It is not a useful factor claim
and is not evidence of profitable, robust, tradable, or deployable behavior.

## Files Changed And Explicitly Staged

Commit-eligible files for explicit staging:

```text
configs/factors/examples/correctness_fixture_close_delta.json
docs/FACTOR_COMPUTE.md
factors/liquidity/.gitkeep
factors/microstructure/.gitkeep
factors/momentum/.gitkeep
factors/order_flow/.gitkeep
factors/price_action/.gitkeep
factors/researcher_sandbox/.gitkeep
factors/reversal/.gitkeep
factors/volatility/.gitkeep
handoffs/ASV1-P11.md
src/alpha_system/cli/factor.py
src/alpha_system/factors/base.py
src/alpha_system/factors/compute.py
src/alpha_system/factors/dependencies.py
src/alpha_system/factors/io.py
src/alpha_system/factors/materialize.py
src/alpha_system/factors/normalization.py
src/alpha_system/factors/quality.py
tests/fixtures/factors/README.md
tests/fixtures/factors/__init__.py
tests/fixtures/factors/synthetic.py
tests/integration/test_draft_materialization_blocked.py
tests/integration/test_factor_materialize_cli_help.py
tests/integration/test_factor_materialize_registry_tempdb.py
tests/integration/test_factor_materialize_tempdir.py
tests/integration/test_factor_no_output_artifacts.py
tests/no_lookahead/test_factor_availability_lag.py
tests/no_lookahead/test_factor_available_ts_propagation.py
tests/no_lookahead/test_label_as_factor_input_rejected.py
tests/unit/test_factor_compute_deterministic.py
tests/unit/test_factor_dependencies.py
tests/unit/test_factor_dependency_missing_input.py
tests/unit/test_factor_normalization.py
tests/unit/test_factor_quality_flags.py
tests/unit/test_factor_session_reset.py
tests/unit/test_factor_value_schema.py
tests/unit/test_factor_warmup_behavior.py
```

No `runs/**` path is commit-eligible or staged. Run-local artifacts remain
local-only.

## Validation Results

Commands run by Codex:

```text
test -f runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - exit 1; no STOP file was active.

python -m pytest tests/unit tests/integration tests/no_lookahead
PASS - 234 passed.

python -m pytest tests/unit/test_factor_compute_deterministic.py tests/unit/test_factor_dependencies.py tests/unit/test_factor_warmup_behavior.py tests/unit/test_factor_session_reset.py
PASS - 9 passed.

python -m pytest tests/no_lookahead/test_factor_availability_lag.py tests/no_lookahead/test_factor_available_ts_propagation.py tests/no_lookahead/test_label_as_factor_input_rejected.py
PASS - 5 passed.

python -m alpha_system.cli factor validate --help
UNAVAILABLE - exit 1; package is not installed in this shell for the repo's src/ layout (`ModuleNotFoundError: No module named 'alpha_system'`).

python -m alpha_system.cli factor materialize --help
UNAVAILABLE - exit 1; same src-layout import reason.

PYTHONPATH=src python -m alpha_system.cli factor validate --help
PASS - help rendered and includes validate arguments.

PYTHONPATH=src python -m alpha_system.cli factor materialize --help
PASS - help rendered and includes materialize arguments.

python -m compileall src
PASS - exit 0.

git status --short
PASS - showed only ASV1-P11 allowed source/docs/config/tests/fixture/placeholders/handoff paths.

find data/factors -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find data/labels -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find metadata -type f ! -name README.md ! -name .gitkeep -print
PASS - returned empty.

find . -path './tests/fixtures/*' -prune -o -type f \( -name '*.parquet' -o -name '*.arrow' -o -name '*.feather' \) -print
PASS - returned empty.

find . -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' -o -name '*.db-journal' -o -name '*.wal' \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

alpha factor validate --help
UNAVAILABLE - exit 127; console script is not installed in this shell.

alpha factor materialize --help
UNAVAILABLE - exit 127; console script is not installed in this shell.

python -m ruff check src tests
UNAVAILABLE - exit 1; `ruff` is not installed.

python -m mypy src
UNAVAILABLE - exit 1; `mypy` is not installed.
```

## Artifact Policy Confirmation

Allowed-path and local-only separation is preserved. No factor outputs,
label outputs, raw/canonical data, local DBs, Parquet/Arrow/Feather files,
logs, caches, model artifacts, or run-local artifacts are staged or committed.
`runs/**` remains local-only; `git ls-files runs` returned empty.

No generated factor store, no `data/factors/**` payload, no `data/labels/**`
payload, no metadata DB, and no heavy artifact was staged or committed.

## Risk Coverage

- R-001/R-002 lookahead and timestamp ambiguity: mitigated with
  `available_ts` lag propagation and no-lookahead tests.
- R-003 session reset bugs: mitigated with reset and non-reset tests.
- R-005 factor/label leakage: mitigated with label input rejection tests.
- R-014 alpha/tradability overclaiming: docs/config/tests use fixture-only
  disclaimers and make no positive claims.
- R-015 unreviewed promotion: materialization records no approval or promotion.
- R-037/R-038/R-039 local output and DB artifact risk: temp-only integration
  tests and artifact audits passed.
- R-036 trivial fixture risk: tests include negative cases for missing inputs,
  ad-hoc columns, label fields, draft blocking, warmup, session boundaries, and
  late availability.

## Known Limitations

- The MVP includes only a correctness fixture factor builder, not a factor
  library or production factors.
- Local I/O supports JSONL/CSV bars and JSONL factor values for this phase; it
  does not claim a production factor store.
- The module help commands require either an editable install or
  `PYTHONPATH=src` in this shell because the project uses a `src/` layout.
- Fresh Claude review, verdict parsing, semantic done-check, PR, CI, and merge
  are Ralph-owned and were not performed by Codex.

## Review Focus

Reviewer should focus on dependency enforcement, label-input rejection,
`available_ts` propagation, warmup/session reset behavior, lifecycle gating,
draft materialization blocking, temp/local output policy, absence of promotion
paths, artifact-policy cleanliness, and absence of signal/strategy/backtest/
portfolio/execution or broker/live/paper scope.
