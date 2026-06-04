# DATA-P12 Handoff - Session Templates and Trading Calendar

## Scope Completed

Implemented DATA-P12 session/calendar records in
`src/alpha_system/data/foundation/sessions.py`.

`SessionTemplate` is now a frozen, fail-closed record with the campaign-required
fields:

- `template_id`
- `timezone`
- `rth_start`
- `rth_end`
- `eth_start`
- `eth_end`
- `maintenance_breaks`
- `source`

Validation requires an explicit valid IANA timezone, rejects implicit-local and
abbreviation-style timezones, validates non-empty ETH windows including
overnight ETH, requires RTH to fall within ETH after overnight normalization,
requires well-formed maintenance breaks with `start < end`, and rejects sources
that claim holiday completeness, exchange-final authority, or production
certification.

`TradingCalendarRecord` is now a frozen, fail-closed record with the
campaign-required fields:

- `calendar_id`
- `instrument_root`
- `date`
- `session_type`
- `open_ts`
- `close_ts`
- `breaks`
- `is_holiday`
- `is_early_close`
- `source`

Validation requires `instrument_root` to exist in the DATA-P05 futures
instrument master, requires timezone-aware `open_ts`/`close_ts` for open
sessions, rejects naive timestamps, requires `close_ts > open_ts`, requires
dated break windows to be aware and inside the open session, requires
`HOLIDAY` and `EARLY_CLOSE` flag/session-type consistency, and allows holidays
only as no-session records or explicitly closed zero-duration records.

## Session Template Linkage

Added the synthetic declarative config
`configs/data/session_templates_and_calendar.json` with the
`session_cme_index_futures_eth` template ID already referenced by
`InstrumentMasterRecord.session_template_id` in DATA-P05.

Added `resolve_session_template_for_instrument()` and
`resolve_session_templates_for_instrument_master()` to resolve the DATA-P05
linkage and fail closed if a template ID is missing or the template timezone
does not match the instrument-master timezone.

## DST, Early Close, Holiday, and Fixtures

Added `tests/fixtures/data/synthetic_session_calendar.json`, a tiny
hand-authored fixture with:

- one synthetic session template;
- one normal full ETH session;
- one DST-transition session with visible offset change (`-06:00` to `-05:00`);
- one early-close session with `is_early_close = true` and shortened
  `close_ts`;
- one holiday session with no tradable timestamps.

The tests verify explicit timezone enforcement, malformed RTH/ETH/break
rejection, normal full-session duration, DST offset transition visibility,
early-close duration, holiday representation, required field exposure, and
DATA-P05 session-template linkage resolution.

## Documentation and README Snapshot

Added `docs/data_foundation/SESSIONS_AND_CALENDAR.md` describing the field
contracts, fail-closed validation, explicit timezone/DST handling, early-close
and holiday representation, synthetic fixtures, and non-claims.

Updated `docs/data_foundation/README.md` to index the DATA-P12 session/calendar
doc and updated `tests/fixtures/data/README.md` to document the synthetic
fixture.

Updated the repository `README.md` snapshot for DATA-P12: the snapshot records
the new `SessionTemplate` and `TradingCalendarRecord` objects, the synthetic
template config, the `SESSIONS_AND_CALENDAR.md` doc, and the next phase
(`DATA-P13` - Roll Policy and Roll Calendar). The safety boundaries remain
unchanged: IBKR read-only historical only; clientId `101`/`102` hard-blocked;
no broker/order/account/paper/live/real-time scope; real data local-only; and
explicit staging only.

## Validation Results

No checks were skipped.

```text
python -m pytest tests/unit/data/test_sessions_calendar.py -q
```

Result:

```text
26 passed in 0.06s
```

```text
python -m pytest tests/unit/data -q
```

Result:

```text
240 passed in 0.17s
```

```text
git status --short
```

Result before handoff/staging:

```text
 M README.md
 M docs/data_foundation/README.md
 M src/alpha_system/data/foundation/sessions.py
 M tests/fixtures/data/README.md
?? configs/data/session_templates_and_calendar.json
?? docs/data_foundation/SESSIONS_AND_CALENDAR.md
?? tests/fixtures/data/synthetic_session_calendar.json
?? tests/unit/data/test_sessions_calendar.py
```

```text
python tools/verify.py --smoke
```

Result: passed with exit code 0 and no output.

```text
test -f docs/data_foundation/SESSIONS_AND_CALENDAR.md
```

Result: passed with exit code 0 and no output.

```text
grep -q "DATA-P12" README.md
```

Result: passed with exit code 0 and no output.

```text
python tools/hooks/canary_runner.py
```

Result:

```text
PASS forbidden_git_add_dot
PASS policy_doc_mentions_forbidden_command
PASS forbidden_test_tamper
PASS forbidden_secret
PASS forbidden_large_binary
PASS forbidden_destructive_op
PASS forbidden_boundary_import
PASS forbidden_raw_data_commit
PASS forbidden_cache_data_commit
PASS forbidden_local_artifacts
PASS forbidden_scope_drift
PASS generated_scaffold_allowed
PASS governance_future_shift
PASS governance_permuted_labels
PASS governance_optimistic_fill
All Frontier canaries passed.
```

```text
git ls-files runs
```

Result: passed with empty output.

```text
find data -type f ! -name README.md ! -name ".gitkeep" -print
```

Result: passed with empty output.

```text
find metadata -type f ! -name README.md ! -name ".gitkeep" -print
```

Result: passed with empty output.

```text
find . -name "*.parquet" -not -path "./tests/fixtures/*" -print
```

Result: passed with empty output.

Additional local source sanity run while editing:

```text
python -m py_compile src/alpha_system/data/foundation/sessions.py
```

Result: passed with exit code 0 and no output.

## Explicit Staging Set

Curated commit-eligible paths for explicit staging:

```text
README.md
configs/data/session_templates_and_calendar.json
docs/data_foundation/README.md
docs/data_foundation/SESSIONS_AND_CALENDAR.md
handoffs/ALPHA_DATA_FOUNDATION_V1/DATA-P12.md
src/alpha_system/data/foundation/sessions.py
tests/fixtures/data/README.md
tests/fixtures/data/synthetic_session_calendar.json
tests/unit/data/test_sessions_calendar.py
```

No `runs/**` path is included. `git add .` and `git add -A` were not used.
No run-local `handoff.md`, `review.md`, or `verdict.json` was created or
staged.

## Artifact and Scope Confirmation

- `git ls-files runs` returned empty.
- No `runs/**` path is in the curated staging set.
- No raw data, canonical data, factor data, label data, cache data, provider
  response, account artifact, SQLite/DB/WAL file, log, Parquet, Arrow, Feather,
  model artifact, secret, credential, or heavy artifact was created or staged.
- Only tiny synthetic deterministic fixtures under `tests/fixtures/data/**`
  were added.
- No external call, provider pull, IBKR connection, broker operation, order
  routing, account access, position access, paper trading, live trading,
  real-time behavior, production deployment, PR creation, merge, reviewer call,
  review artifact, `verdict.json`, or phase PASS marking was performed.
- No roll policy, roll calendar, canonical bars, real-bar session labeling,
  no-lookahead timestamp policy, alpha/factor/label/strategy scope, or
  alpha/profitability/tradability/production-readiness claim was introduced.

## Commit and Push Status

- Local executor commit was created on branch
  `auto/alpha_data_foundation_v1/data-p12-session-templates-and-trading-calendar`.
- Push was attempted with `GIT_TERMINAL_PROMPT=0 git push origin HEAD`.
- Push failed because network DNS could not resolve GitHub:

```text
fatal: unable to access 'https://github.com/yukepenn/alpha_system.git/': Could not resolve host: github.com
```

No force push, PR, merge, reviewer call, verdict, or PASS marking was
performed.
