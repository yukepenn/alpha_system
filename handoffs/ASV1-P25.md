# ASV1-P25 Handoff — L2 Readiness Schema and Design

## Scope Completed

Implemented design-only L2 readiness schemas, timestamp helpers, future-capability design metadata, in-memory synthetic validators, durable L2 docs, one tiny synthetic config example, required tests, and the README snapshot update.

No replay engine, order-book reconstruction engine, queue-position model, passive-fill simulation, live market data feed, broker scope, paper trading scope, persistence, registry migration, CLI command, executable L2 strategy validation, or second PnL truth was introduced.

## L2 Schema Coverage

Snapshot schema (`l2_snapshot_v1`):

| Field | Required | Nullable | Notes |
| --- | --- | --- | --- |
| `instrument_id` | yes | no | stable instrument id |
| `session_id` | yes | no | session assigned from `event_ts` |
| `event_ts` | yes | no | exchange/source event timestamp |
| `receive_ts` | yes | no | local/feed receive timestamp |
| `available_ts` | yes | no | earliest research-use timestamp |
| `book_level` | yes | no | one-based level, bounded `1..50` |
| `side` | yes | no | `bid` or `ask` |
| `price` | yes | no | positive `Decimal` |
| `size` | yes | no | nonnegative `Decimal` |
| `order_count` | yes | yes | present when source provides it |
| `data_version` | yes | no | nonblank version id |
| `quality_flags` | yes | no | `tuple[str, ...]`, empty when clean |

Event/delta schema (`l2_event_delta_v1`):

| Field | Required | Nullable | Notes |
| --- | --- | --- | --- |
| `instrument_id` | yes | no | stable instrument id |
| `session_id` | yes | no | session assigned from `event_ts` |
| `event_ts` | yes | no | exchange/source event timestamp |
| `receive_ts` | yes | no | local/feed receive timestamp |
| `available_ts` | yes | no | earliest research-use timestamp |
| `sequence_id` | yes | yes | monotonic when provided |
| `action` | yes | no | `add`, `update`, `delete`, or `clear` |
| `book_level` | yes | yes | required for level actions, nullable for `clear` |
| `side` | yes | no | `bid` or `ask` |
| `price` | yes | no | positive `Decimal` |
| `size` | yes | no | nonnegative `Decimal` |
| `order_count` | yes | yes | present when source provides it |
| `data_version` | yes | no | nonblank version id |
| `quality_flags` | yes | no | `tuple[str, ...]`, empty when clean |

## Timestamp Semantics

`event_ts` is the exchange/source event timestamp. `receive_ts` is the local or feed receive timestamp. `available_ts` is the earliest time the research system may use the information.

Validation enforces `event_ts <= receive_ts <= available_ts`. Session assignment uses `event_ts`; no-lookahead research ordering uses `available_ts` first, with `receive_ts`, `event_ts`, `sequence_id`, instrument, side, and book level as deterministic tie-breakers.

## Snapshot/Delta Consistency Contract

The consistency validator checks synthetic in-memory records only. It confirms snapshot and delta context matches on `instrument_id`, `session_id`, and `data_version`; deltas do not precede the snapshot on `event_ts` or `available_ts`; and provided `sequence_id` values increase across supplied deltas.

## Files Changed And Explicitly Staged

These commit-eligible paths were changed and are the intended explicit staged set:

- `README.md`
- `configs/data/l2_examples/synthetic_l2_readiness_example.json`
- `docs/FUTURE_L2_REPLAY.md`
- `docs/L2_READINESS.md`
- `docs/L2_SCOPE_BOUNDARIES.md`
- `handoffs/ASV1-P25.md`
- `src/alpha_system/l2/design.py`
- `src/alpha_system/l2/schemas.py`
- `src/alpha_system/l2/timestamps.py`
- `src/alpha_system/l2/validation.py`
- `tests/no_lookahead/test_l2_timestamp_ordering.py`
- `tests/unit/test_l2_artifact_policy.py`
- `tests/unit/test_l2_available_ts_required.py`
- `tests/unit/test_l2_book_level_validation.py`
- `tests/unit/test_l2_data_version_required.py`
- `tests/unit/test_l2_delta_required_fields.py`
- `tests/unit/test_l2_design_only_scope.py`
- `tests/unit/test_l2_quality_flags_required.py`
- `tests/unit/test_l2_receive_ts_semantics.py`
- `tests/unit/test_l2_side_enum.py`
- `tests/unit/test_l2_snapshot_delta_consistency_contract.py`
- `tests/unit/test_l2_snapshot_required_fields.py`
- `tests/unit/test_l2_update_action_enum.py`

No `runs/**` path is included. No review artifact, run-local handoff, `review.md`, or `verdict.json` was created by Codex.

## Validation

Passed:

- `python -m pytest tests/unit tests/no_lookahead` — 525 passed.
- `python -m pytest tests/unit/test_l2_snapshot_required_fields.py tests/unit/test_l2_delta_required_fields.py tests/no_lookahead/test_l2_timestamp_ordering.py` — 9 passed.
- `python -m pytest tests/unit/test_l2_snapshot_required_fields.py tests/unit/test_l2_delta_required_fields.py tests/no_lookahead/test_l2_timestamp_ordering.py tests/unit/test_l2_available_ts_required.py tests/unit/test_l2_receive_ts_semantics.py tests/unit/test_l2_side_enum.py tests/unit/test_l2_update_action_enum.py tests/unit/test_l2_book_level_validation.py tests/unit/test_l2_data_version_required.py tests/unit/test_l2_quality_flags_required.py tests/unit/test_l2_snapshot_delta_consistency_contract.py tests/unit/test_l2_design_only_scope.py tests/unit/test_l2_artifact_policy.py` — 40 passed.
- `python -m compileall src` — passed.
- `git status --short` — listed only allowed changed paths before handoff/staging.
- `find data -path "*l2*" -type f -print || true` — no output.
- `find artifacts -type f ! -name README.md ! -name ".gitkeep" -print 2>/dev/null || true` — no output.
- `find metadata -type f ! -name README.md ! -name ".gitkeep" -print` — no output.
- `find . -path "./tests/fixtures/*" -prune -o -type f \( -name "*.parquet" -o -name "*.arrow" -o -name "*.feather" \) -print` — no output.
- `find . -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-journal" -o -name "*.wal" \) -print` — no output.
- `git ls-files runs` — no output.

`ruff` and `mypy` were not run because they are not configured in `pyproject.toml` and are not declared in the repo dev dependencies for this phase.

## Artifact Policy And Staging

The only example under `configs/data/l2_examples/` is tiny, deterministic, synthetic, correctness-only, and explicitly marked as not real market data. No real L2 data, order-book data, replay output, generated store, local DB, heavy artifact, Parquet, Arrow, Feather, log, or cache was added.

Staging must remain explicit by path. `git add .`, `git add -A`, force push, PR creation, merge, reviewer execution, PASS marking, and Claude calls were not performed.

## Durable Boundaries

The Tier 1 reference 1-minute bar engine remains the single PnL truth. L2 remains design/schema-only. No alpha, profitability, robustness, tradability, production-execution, broker, live, paper, deployment, or executable L2 strategy-validation claim was introduced.

Allowed commit-eligible paths are separated from local-only `runs/**` artifacts. `runs/**` remains local-only and untracked for this campaign baseline.

## Deferred Future Work

- Source-specific L2 sequencing, gap, reset, and recovery policy.
- Reviewed future L2 replay design and implementation.
- Future L2-derived feature skeleton in ASV1-P26.
- Future queue-position, latency, and passive-fill research only after reviewed replay assumptions exist.
- Any future live data, broker, paper, or execution work would require separate authorization and is not part of this campaign phase.

## Known Limitations

- Validation is schema-level only and operates on mapping records in memory.
- No persistence, registry integration, data loader, CLI, replay, feature materialization, queue model, passive-fill simulation, or execution component exists.
- Nullable source-dependent fields are represented as required columns with null values when unavailable.

## Review Focus

Reviewer should focus on required field completeness, enum coverage, timestamp ordering and no-lookahead semantics, snapshot/delta consistency, design-only scope control, absence of forbidden runtime modules, artifact policy compliance, README boundary wording, and staged-path hygiene.
