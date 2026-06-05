# ASV1-P10 Handoff

## Phase

- Phase ID: `ASV1-P10`
- Phase name: Label Store MVP
- Campaign: `ALPHA_SYSTEM_V1`
- Lane: Yellow
- Branch: `auto/alpha_system_v1/asv1-p10-label-store-mvp`
- Worktree: `/home/yuke_zhang/projects/alpha_system`
- Base commit observed by Codex: `81b462c`
- Run directory: `runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/phases/ASV1-P10` (local-only)

## Scope Completed

Implemented the scoped label layer:

- exact nine-field `LabelSpec` label record contract;
- standard label type coverage for forward returns, MFE/MAE, target/stop ordering, future realized volatility, and future spread/liquidity;
- deterministic generation from canonical 1-minute bar records;
- path metrics with MFE/MAE metadata and conservative same-bar target/stop ordering;
- label validation and no-lookahead checks using `label_available_ts`;
- point-in-time research alignment keys and live factor/strategy input rejection;
- local-only JSONL label store defaulting to temp directories;
- temp-registry `label_versions` recording against the ASV1-P05 schema;
- documentation, tiny example config, and tiny deterministic synthetic label fixtures.

No factor computation, strategy logic, signal logic, backtest, portfolio,
execution, L2, broker, paper, live, order-routing, deployment, PR creation,
merge, reviewer call, `review.md`, `verdict.json`, or PASS marking was
introduced.

## Label Family Coverage

| Label family | Implementation | Tests |
| --- | --- | --- |
| `forward_return_1m` | `generate_forward_return_labels` | `test_forward_return_labels.py` |
| `forward_return_3m` | `generate_forward_return_labels` | `test_forward_return_labels.py`, no-lookahead tests |
| `forward_return_5m` | `generate_forward_return_labels` | `test_forward_return_labels.py`, session/half-day tests |
| `forward_return_10m` | `generate_forward_return_labels` | `test_forward_return_labels.py` |
| `forward_return_30m` | `generate_forward_return_labels` | `test_forward_return_labels.py` |
| MFE by horizon | `generate_mfe_mae_labels`, `compute_mfe_mae` | `test_mfe_mae_labels.py` |
| MAE by horizon | `generate_mfe_mae_labels`, `compute_mfe_mae` | `test_mfe_mae_labels.py` |
| target-before-stop | `generate_stop_target_ordering_labels` | `test_stop_target_ordering_labels.py` |
| stop-before-target | `generate_stop_target_ordering_labels` | `test_stop_target_ordering_labels.py` |
| future realized volatility | `generate_future_realized_volatility_labels` | `test_future_volatility_labels.py` |
| future spread/liquidity | `generate_future_spread_liquidity_labels` | `test_future_spread_liquidity_labels.py` |

## Schema And Alignment

`src/alpha_system/labels/spec.py` defines the exact required label record
fields:

```text
label_id
instrument_id
event_ts
horizon
label_type
value
path_metadata
data_version
label_available_ts
```

`src/alpha_system/labels/alignment.py` enforces the research alignment key:

```text
instrument_id
event_ts
session_id
horizon
data_version
label_version
```

`session_id` and `label_version` are required inside `path_metadata` so the
top-level label record remains exactly the required schema.

## No-Lookahead Confirmation

Generated labels set `label_available_ts` from the terminal future bar
`available_ts` when the horizon is complete. For incomplete horizons,
`value` is `None`, `insufficient_future` is true, and the label is clamped to
the observed session close. Validation rejects any label whose
`label_available_ts` is earlier than `path_metadata.horizon_end_ts`.

Labels are not usable as live inputs:

- `reject_labels_as_factor_inputs` rejects label records, label domains, and label fields.
- `reject_labels_as_strategy_inputs` rejects label records and label fields.
- `assert_research_join_purpose` rejects live-factor/live-strategy purposes.

## Session And Half-Day Handling

Generation groups bars by `instrument_id`, `data_version`, and `session_id`.
Horizons are resolved by same-session `bar_index`; they do not cross into the
next session. Session-boundary and half-day tests verify null/insufficient
labels rather than fabricated cross-session values.

## Registry And Store

`src/alpha_system/labels/store.py` records label versions into the existing
ASV1-P05 `label_versions` table with git commit/dirty state, code hash, config
hash, data version, parameters JSON, artifact paths JSON, decision status, and
status message. Tests use only `tmp_path` SQLite registries outside the repo.
No SQLite/DB file was committed.

`LocalLabelStore` defaults to a `/tmp`-backed temp directory and rejects
repository-local output roots such as `data/labels/generated`.

## Files Changed And Explicitly Staged

The following commit-eligible files were changed and staged explicitly by path:

```text
configs/labels/examples/standard_label_set.json
docs/LABEL_STORE.md
handoffs/ASV1-P10.md
src/alpha_system/labels/alignment.py
src/alpha_system/labels/generation.py
src/alpha_system/labels/path_metrics.py
src/alpha_system/labels/spec.py
src/alpha_system/labels/store.py
src/alpha_system/labels/validation.py
tests/fixtures/labels/README.md
tests/fixtures/labels/__init__.py
tests/fixtures/labels/synthetic_bars.py
tests/integration/test_label_no_output_artifacts.py
tests/integration/test_label_registry_tempdb.py
tests/no_lookahead/test_label_available_ts.py
tests/no_lookahead/test_labels_not_factor_inputs.py
tests/no_lookahead/test_labels_not_strategy_inputs.py
tests/unit/test_forward_return_labels.py
tests/unit/test_future_spread_liquidity_labels.py
tests/unit/test_future_volatility_labels.py
tests/unit/test_label_half_day_behavior.py
tests/unit/test_label_session_boundaries.py
tests/unit/test_label_spec_fields.py
tests/unit/test_mfe_mae_labels.py
tests/unit/test_stop_target_ordering_labels.py
```

No `runs/**` path is commit-eligible or staged. Run-local artifacts remain
local-only.

## Validation Results

Commands run by Codex:

```text
test -f runs/2026-06-02T012007Z_ALPHA_SYSTEM_V1/STOP
PASS - exit 1; no STOP file was active.

python -m pytest tests/unit tests/integration tests/no_lookahead
PASS - 206 passed.

python -m pytest tests/unit/test_label_spec_fields.py tests/unit/test_forward_return_labels.py tests/unit/test_mfe_mae_labels.py tests/unit/test_stop_target_ordering_labels.py
PASS - 25 passed.

python -m pytest tests/no_lookahead/test_label_available_ts.py tests/no_lookahead/test_labels_not_factor_inputs.py tests/no_lookahead/test_labels_not_strategy_inputs.py
PASS - 6 passed.

python -m compileall src
PASS - exit 0.

git status --short
PASS - showed only ASV1-P10 source/docs/config/tests/fixture/handoff paths before staging.

find data/labels -type f ! -name ".gitkeep" -print
BASELINE OUTPUT - exit 0; printed data/labels/README.md. This is an existing tracked placeholder from the baseline, not generated label data. The path is forbidden for this phase, so Codex did not edit or remove it.

find metadata -type f ! -name README.md ! -name ".gitkeep" -print
PASS - returned empty.

find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print
PASS - returned empty.

find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print
PASS - returned empty.

git ls-files runs
PASS - returned empty.

python -m ruff check src tests || true
UNAVAILABLE - exit 0 due to `|| true`; /usr/bin/python: No module named ruff.

python -m mypy src || true
UNAVAILABLE - exit 0 due to `|| true`; /usr/bin/python: No module named mypy.

git diff --check
PASS - exit 0.
```

No hidden failed runs are known.

## Artifact Policy

No raw data, canonical data, generated label stores, local label
Parquet/Arrow/Feather files, local SQLite/DB/journal/WAL files, heavy artifacts,
logs, caches, or `runs/**` files were staged. The only fixture additions are
tiny deterministic correctness fixtures under `tests/fixtures/labels/**`.

Staging was explicit by path. `git add .`, `git add -A`, force push, PR
creation, merge, reviewer execution, `review.md`, and `verdict.json` were not
used.

## Risk Dispositions

| Risk | Disposition |
| --- | --- |
| R-001 Lookahead leakage | Mitigated by `label_available_ts` generation from terminal `available_ts`, validation against `horizon_end_ts`, and no-lookahead tests. |
| R-002 `event_ts`/`available_ts` ambiguity | Mitigated by separate schema fields and docs distinguishing `event_ts` from `label_available_ts`. |
| R-003 Session reset bugs | Mitigated by same-session grouping and `bar_index` horizon resolution; session-boundary and half-day tests cover insufficient future cases. |
| R-005 Factor/label misalignment | Mitigated by required alignment key fields and research-only join policy. |
| R-018 SQLite schema drift | Mitigated by reusing ASV1-P05 `label_versions`; no migration/schema change added. |
| R-036 Fixture tests too trivial | Mitigated with deterministic fixtures covering complete horizons, insufficient future, session boundary, half-day, MFE/MAE, same-bar ambiguity, and no-lookahead guards. |
| R-037 CLI/library writes to local-only repo paths | Mitigated by temp default store, repo-path rejection, and no-output-artifact tests. |
| R-039 Generated Parquet committed | Mitigated by no Parquet/Arrow/Feather generation and clean artifact audit. |

## Known Limitations And Review Focus

- There is no label CLI in this phase; the label store is library-level only.
- Future realized volatility uses population standard deviation over future
  close-to-close returns for the deterministic fixture path.
- The exact `find data/labels -type f ! -name ".gitkeep" -print` command
  prints the baseline `data/labels/README.md`; reviewer/Ralph should treat this
  as a baseline placeholder mismatch, not generated label output.
- Fresh Claude review is required by the Yellow lane but was not run by Codex,
  per executor instructions.

No alpha, profitability, robustness, or tradability claims were introduced.
