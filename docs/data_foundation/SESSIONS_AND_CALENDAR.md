# Session Templates and Trading Calendar

DATA-P12 defines local-only session and calendar records for the data
foundation. The records validate timezone, session-window, holiday, early-close,
and DST-sensitive timestamp semantics before later phases consume sessions for
canonical bars, quality reports, or roll logic.

These records do not fetch data, label real bars, compute rolls, connect to
IBKR, or claim exchange-official calendar completeness.

## SessionTemplate

`SessionTemplate` is the reusable exchange-time template referenced by
`InstrumentMasterRecord.session_template_id`.

Required fields:

```text
template_id
timezone
rth_start
rth_end
eth_start
eth_end
maintenance_breaks
source
```

Validation is fail-closed:

- `timezone` must be an explicit valid IANA timezone such as
  `America/Chicago`; empty, local, system, default, and abbreviation-style
  values are rejected.
- `rth_start` must be before `rth_end`.
- `eth_start` and `eth_end` must describe a non-empty ETH window. Overnight ETH
  windows are allowed.
- The RTH window must fall inside the ETH window after overnight normalization.
- `maintenance_breaks` entries must include `start` and `end`, with
  `start < end`.
- `source` must carry synthetic or to-be-verified provenance and must not claim
  exchange-final authority, holiday completeness, or production certification.

The default synthetic config
`configs/data/session_templates_and_calendar.json` defines
`session_cme_index_futures_eth`, the template ID already referenced by the
DATA-P05 futures instrument master. The resolver verifies that a template ID
exists and that its timezone matches the instrument-master timezone.

## TradingCalendarRecord

`TradingCalendarRecord` is a concrete dated session record for one instrument
root and session type.

Required fields:

```text
calendar_id
instrument_root
date
session_type
open_ts
close_ts
breaks
is_holiday
is_early_close
source
```

Validation is fail-closed:

- `instrument_root` must exist in the DATA-P05 futures instrument master.
- Non-holiday sessions require timezone-aware `open_ts` and `close_ts`.
- Naive timestamps and missing offsets are rejected.
- Open sessions require `close_ts > open_ts`.
- Dated `breaks` entries must include aware `start` and `end`, with
  `start < end`, and must fall within the open session.
- Holiday records must use `session_type = HOLIDAY`, must not be early-close
  records, and must either omit both timestamps or provide an explicitly closed
  zero-duration timestamp pair.
- Early-close records must use `session_type = EARLY_CLOSE` and
  `is_early_close = true`.
- `source` follows the same synthetic/to-be-verified non-finality rule as
  `SessionTemplate`.

## DST and Early Closes

Calendar records store concrete aware timestamps. DST behavior is therefore
visible on the record: an offset-changing session has different UTC offsets on
`open_ts` and `close_ts`, exposed by `has_offset_transition`.

Early closes are explicit records with `is_early_close = true` and a shortened
`close_ts`. DATA-P12 tests compare the synthetic early-close duration against a
normal full synthetic session. The records do not infer early closes from a
holiday table and do not assert real exchange schedules.

## Fixtures

`tests/fixtures/data/synthetic_session_calendar.json` is tiny, deterministic,
and hand-authored. It contains:

- one session template linked to `session_cme_index_futures_eth`;
- one normal full ETH session;
- one DST-transition session with visible offset change;
- one early-close session;
- one holiday session with no tradable timestamps.

The fixture is not raw market data, is not a provider response, and is not
evidence about any venue schedule.

## Boundaries

DATA-P12 has no roll policy, roll calendar, canonical-bar, parser,
session-labeling, no-lookahead timestamp policy, provider-call, IBKR connection,
raw-write, broker, order, account, paper, live, real-time, deployment, alpha,
profitability, production-readiness, or tradability scope.

Holiday coverage remains a scaffold to be verified by later authorized work.
No calendar in this phase should be treated as complete, official, or
exchange-certified.
