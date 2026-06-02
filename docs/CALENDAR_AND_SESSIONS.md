# Calendar And Sessions

ASV1-P07 adds a small, synthetic, local-first calendar and session layer above
the canonical 1-minute bar schema. It is intended for deterministic fixture
checks and downstream contract alignment. It does not ingest vendor calendars,
download holiday feeds, create local datasets, or make claims about market
results.

## Calendar Model

`alpha_system.data.calendar` loads JSON configs from
`configs/data/calendars/`. A config must declare:

- `calendar_id`
- `timezone`
- `regular_session.open`
- `regular_session.close`
- explicit synthetic `sessions` entries for boundary cases such as regular
  days, holidays, and half-days

Loaded sessions are represented with the existing
`alpha_system.data.contracts.TradingSession` fields:

```text
calendar_id
trading_date
session_id
open_ts
close_ts
is_holiday
is_half_day
session_type
timezone
quality_flags
```

No new domain contract is introduced in this phase.

## Timezone Handling

Session windows are built in the exchange timezone declared by the calendar.
Bar timestamps may be in UTC or another timezone as long as they are
timezone-aware. Session lookup converts the bar start into the exchange
timezone before choosing the trading date, then compares aware datetimes.

The implementation does not assume a single global exchange timezone.

## Holidays And Half-Days

A holiday calendar entry returns a typed `TradingSession` record for contract
inspection, but `trading_session_for_date` returns `None`. Bars on holidays are
therefore retained and flagged as `out_of_session`; they are not assigned to a
real session.

A half-day uses the configured early close. Expected bar counts are computed
from the actual `open_ts` to `close_ts` interval, so a half-day is not treated
as a full regular session.

## Session Assignment

`alpha_system.data.sessionize.sessionize_bars` is a pure in-memory transform.
It copies input rows, assigns the deterministic `session_id`, computes
zero-based `bar_index`, and attaches session metadata. `bar_index` starts at
the session open and resets for every session and trading date.

Bars outside the configured session window are not dropped and are not assigned
to a real session. They are retained with:

- `session_id` set to an empty string
- `bar_index` set to `-1`
- `quality_flags` containing `out_of_session`

## Quality Flags

`alpha_system.data.quality` surfaces three ASV1-P07 quality categories:

- `missing_bar`: expected grid entries absent from an observed
  instrument/session group
- `duplicate_bar`: duplicate `(instrument_id, session_id, bar_index)` or
  `(instrument_id, session_id, bar_start_ts)` keys
- `out_of_session`: bars before open, after close, on holidays, or outside a
  valid session interval

Quality checks return copied rows plus structured `QualityIssue` warnings.
Rows are not silently dropped, merged, filled, or backfilled.

## Availability Semantics

Canonical bars keep `event_ts`, `bar_end_ts`, and `available_ts` distinct.
Sessionized rows preserve the bar `available_ts` and add explicit availability
timestamps for session-derived metadata:

- `session_metadata_available_ts` is at least `bar_end_ts` plus configured
  latency and at least the bar's own `available_ts`
- `session_close_available_ts` is `session_close_ts` plus configured latency
- missing-bar summaries are available no earlier than session close plus
  configured latency

Downstream research code must use the relevant availability timestamp rather
than consuming session or quality metadata before that information is available.

## Artifact Policy

Calendar configs committed in this phase are tiny, deterministic, synthetic
examples. They are not licensed exchange dumps and are not raw market data.

Generated raw, canonical, factor, label, cache, report, SQLite, DB, Parquet,
Arrow, Feather, log, and model artifacts remain local-only unless a later phase
explicitly authorizes a tiny synthetic fixture exception. The `runs/` tree is
Workflow 2 runtime state and is never commit-eligible.
