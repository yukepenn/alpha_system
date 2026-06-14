# DK-P01 Session Calendar Roll Flag Provenance

This directory records the APPROVED FeatureRequest declarations for the five
additive `SESSION_CALENDAR_ROLL` flags:

- `is_opex_day_flag`
- `is_quad_witch_day_flag`
- `is_month_end_session_flag`
- `is_quarter_end_session_flag`
- `in_roll_window_flag`

The flags are zero-feed and known ahead. They use canonical OHLCV timestamps,
the committed CME index futures session template in
`configs/data/session_templates_and_calendar.json`, analytic third-Friday
calendar arithmetic, committed full-holiday records for covered-window
month/quarter-end sessions, and the analytic CME equity-index quarterly roll
calendar through `roll_guard.classify_roll_window`.

Non-claims are explicit: `not_exchange_official`, `not_holiday_complete`,
`fail_absent_outside_coverage`, and `approximate_roll`. The roll-window flag
does not use `BARS_TO_ROLL` or `MINUTES_TO_ROLL`; those remain offline-only
future-countdown features. No external date, strike, open-interest, auction, or
paid data feed is required. No factor IC, return, diagnostic, alpha,
profitability, tradability, promotion, broker, paper, live, or deployment claim
is made here.
