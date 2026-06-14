# Handoff - DIFFERENTIATED_KILLSHOT_V1 DK-P01

## Scope Delivered

DK-P01 added five zero-feed, known-ahead flags as additive members of the
existing `SESSION_CALENDAR_ROLL` family:

- `is_opex_day_flag`
- `is_quad_witch_day_flag`
- `is_month_end_session_flag`
- `is_quarter_end_session_flag`
- `in_roll_window_flag`

The reference family wires each flag through the enum, `_transform_id`,
`_INPUT_FIELDS_BY_FEATURE`, `CalendarFeatureSpec` wrapping, and `_feature_point`.
The fast path mirrors each flag in
`src/alpha_system/features/fast/session_calendar_roll.py`; `PACK_FEATURES`
remains auto-derived from `SessionFeatureName`.

The flags are `live=True`, CAUSAL, POINT_IN_TIME, and use current-row
`available_ts`. No flag uses `BARS_TO_ROLL` or `MINUTES_TO_ROLL`.

## Derivations And Non-Claims

- OPEX: session trade date equals analytic `third_friday(year, month)`.
- Quad witch: OPEX rule restricted to Mar/Jun/Sep/Dec.
- Month end: last weekday trading session in the committed calendar coverage
  years, excluding committed full-holiday records; absent outside coverage.
- Quarter end: month-end rule restricted to Mar/Jun/Sep/Dec; absent outside
  coverage.
- Roll window: `classify_roll_window` over the analytic CME equity-index
  quarterly roll calendar, default 2 days before / 1 day after, using the
  session-local timestamp and root symbol.

Non-claims are recorded in FeatureSpec metadata and the provenance note:
`not_exchange_official`, `not_holiday_complete`,
`fail_absent_outside_coverage`, and `approximate_roll`.

## FeatureRequest Gate

APPROVED FeatureRequest declarations were added under
`research/differentiated_substrate_v1/feature_requests/`:

- `is_opex_day_flag.json`
- `is_quad_witch_day_flag.json`
- `is_month_end_session_flag.json`
- `is_quarter_end_session_flag.json`
- `in_roll_window_flag.json`
- `SESSION_CALENDAR_ROLL_FLAGS_PROVENANCE.md`

Unit tests load these artifacts, validate them as `FeatureRequest` records, and
confirm they admit the new flags. Missing and PENDING requests still fail closed.
The existing duplicate-exposure gate re-checks requests and may bind a checked
`freq_` id into the resulting `FeatureSpec`; the original artifact request is
still present on the gate decision and must be APPROVED.

## Files Changed

- `src/alpha_system/features/families/session/family.py`
- `src/alpha_system/features/fast/session_calendar_roll.py`
- `tests/fixtures/feature_compute_fast_path/session_calendar_roll.py`
- `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py`
- `tests/unit/features/families/session/test_session_family.py`
- `research/differentiated_substrate_v1/feature_requests/is_opex_day_flag.json`
- `research/differentiated_substrate_v1/feature_requests/is_quad_witch_day_flag.json`
- `research/differentiated_substrate_v1/feature_requests/is_month_end_session_flag.json`
- `research/differentiated_substrate_v1/feature_requests/is_quarter_end_session_flag.json`
- `research/differentiated_substrate_v1/feature_requests/in_roll_window_flag.json`
- `research/differentiated_substrate_v1/feature_requests/SESSION_CALENDAR_ROLL_FLAGS_PROVENANCE.md`
- `README.md`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P01.md`

No `reviews/**`, `review.md`, `verdict.json`, PR, merge, staging, commit, push,
broker, paper, live, order-routing, deployment, or destructive operation was
performed.

## Validation Commands And Results

- `test -e runs/2026-06-14T034219Z_DIFFERENTIATED_KILLSHOT_V1/STOP && printf 'STOP_PRESENT\n' || printf 'NO_STOP\n'`
  - PASS: `NO_STOP`.
- `PYTHONPATH=src python -m ruff check src/alpha_system/features/families/session/family.py src/alpha_system/features/fast/session_calendar_roll.py tests/unit/features/families/session/test_session_family.py tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py tests/fixtures/feature_compute_fast_path/session_calendar_roll.py`
  - PASS.
- `PYTHONPATH=src python -m pytest tests/unit/features/families/session/test_session_family.py tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py -q`
  - PASS: `10 passed, 1 skipped`.
- `PYTHONPATH=src python -m pytest tests -k "session or calendar or roll or parity or feature_request or no_lookahead" -q`
  - PASS: `358 passed, 26 skipped, 3191 deselected`.
- `PYTHONPATH=src python tools/verify.py --smoke`
  - PASS.
- `PYTHONPATH=src python tools/hooks/canary_runner.py`
  - PASS: all Frontier canaries passed.
- `python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"`
  - PASS: no output.
- `grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" --include=*.py research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"`
  - PASS: `no forbidden research->sim imports`.
- `git ls-files runs`
  - PASS: no output.
- `env -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python tools/verify.py --all`
  - FAIL: known environment issue because `ALPHA_DATA_ROOT` was inherited;
    `tests/unit/runtime/test_cache_policy.py::test_run_artifact_cache_root_is_explicit_local_only`
    failed, matching the repository lesson. Test body otherwise reached
    `3494 passed, 80 skipped`.
- `env -u ALPHA_DATA_ROOT -u FRONTIER_CREATE_PR -u FRONTIER_ALLOW_AUTOMERGE -u FRONTIER_MERGE_DRY_RUN -u FRONTIER_PARALLEL -u FRONTIER_MAX_PARALLEL_PHASES PYTHONPATH=src python tools/verify.py --all`
  - PASS: `3495 passed, 80 skipped`. `status_doctor` reported WARN only because
    no run-local `state.json` exists in this checkout.

Skipped by explicit executor instruction:

- `git diff --name-only -- src/alpha_system/strategies/templates.py src/alpha_system/core/value_store.py`
  - SKIPPED: user explicitly forbade `git diff`. I did not edit either path.

Materialization attempt:

- `PYTHONPATH=src python -m alpha_system.cli feature materialize --family session_calendar_roll --feature is_opex_day_flag,is_quad_witch_day_flag,is_month_end_session_flag,is_quarter_end_session_flag,in_roll_window_flag --instrument ES,NQ,RTY --execute`
  - NOT MATERIALIZED: command exited 2 at argument parsing. Current CLI supports
    registered `--feature-set-id/--feature-set-version` planning and
    `--seed-config` execution; it does not expose the spec's illustrative
    `--family/--feature/--instrument` interface. No Parquet, registry, or other
    materialized output was created by this attempt.

## Explicit Confirmations

- All five flags are wired through both the reference family and the fast path.
- New tests cover value truth, no-lookahead/`available_ts`, FeatureRequest
  admission, and fail-closed missing/PENDING requests.
- Polars parity tests remain present and auto-enumerate the new enum members;
  they skip in this environment because `polars` is intentionally unimportable.
- The flags are live-compatible, CAUSAL, POINT_IN_TIME, and do not use the
  offline roll-countdown features.
- The zero-feed derivations and non-claims are recorded in contracts and
  research provenance.
- No real-data metric, IC, return, diagnostic, alpha, profitability,
  tradability, or promotion evidence was inspected or produced.
- `day_of_week_effect` and `open_close_auction_flow` were not given new feature
  members; they continue to reuse existing substrate.
- `src/alpha_system/strategies/templates.py` and
  `src/alpha_system/core/value_store.py` were not edited.
- `research/` imports no reference-sim module per the grep guard.
- `numpy`, `pandas`, and `polars` remain unimportable.
- No `runs/**`, Parquet, registry DB, raw/canonical/factor/label data, cache,
  log, secret, review, or verdict artifact was created for commit.
- README snapshot was updated within policy.

## Residual Notes

The only unmet operational item is local ES/NQ/RTY materialization. The current
CLI surface cannot express the requested flags through the illustrative command,
and adding CLI/seed-pack support would be outside DK-P01 allowed paths. Ralph or
a follow-up phase should either provide a registered FeatureSetSpec materializer
path for `SESSION_CALENDAR_ROLL` packs or authorize a scoped CLI extension.
