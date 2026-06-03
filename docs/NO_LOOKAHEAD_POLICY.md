# No-Lookahead Policy

## Purpose

The platform must prevent lookahead leakage in data, factors, labels, signals,
strategies, ML workflows, and backtests. Timestamp semantics are part of the
architecture, not a later optimization.

## Timestamp Fields

- `event_ts`: when the market event occurred.
- `bar_start_ts`: start of the bar interval.
- `bar_end_ts`: end of the bar interval.
- `receive_ts`: when the input was received by the data process.
- `available_ts`: when the value is available to downstream research.
- `label_available_ts`: when a label can be known without future leakage.

These timestamps must remain distinct. Joining or comparing data without the
right timestamp is a correctness risk.

## Bar Availability

Completed bars are usable only after `bar_end_ts` plus configured latency. A
signal produced from bar `t` cannot execute inside bar `t` by default. The
default execution assumption is conservative next-bar execution.

## Labels

Labels may depend on future outcomes, but label values become research targets
only at `label_available_ts`. Labels are not live feature inputs. Any factor,
diagnostic, ML, or report workflow must keep label availability separate from
feature availability.

## Same-Bar Ambiguity

When stop and target prices are both possible inside the same bar and the
ordering is unknowable from 1-minute bars, the Reference engine must use a
conservative default. Optimistic same-bar handling is not the default.
Next-bar entry forbids using the signal origin bar for execution, but it does
not make the entry fill bar immune to risk-management exits; same-fill-bar
stop/target handling is conservative and must never prefer an optimistic target
when both stop and target are possible.

## Fail-Closed Rules

If `available_ts`, `label_available_ts`, data version, factor version, label
version, engine version, config hash, code hash, or run manifest metadata is
missing, the result is not complete for review. Later implementation should
fail closed for missing timestamp semantics rather than infer permissive
defaults.
