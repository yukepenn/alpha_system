# Roll-Splice Guard Contract

`FUTSUB-P03` adds an approximate CME equity-index quarterly roll calendar and a
forward-label roll-splice guard. This is a leakage and contamination guard only.
It does not adjust prices, stitch series, select execution timing, route orders,
read providers, or materialize feature or label values.

## Approximate Calendar

The calendar is analytic and approximate:

- roots: `ES`, `NQ`, `RTY`;
- cycle months: March, June, September, December;
- expiration rule: third Friday of the cycle month;
- roll-date heuristic: 8 calendar days before that expiration;
- method: `calendar_days_before_expiration`;
- validation status: `unvalidated`;
- policy id: `roll_cme_index_futures_quarterly`.

The provider-continuous series in scope are `ES.v.0`, `NQ.v.0`, and `RTY.v.0`.
Their provider-internal volume-based splice point is not recoverable from the
continuous series alone. The analytic calendar is therefore not provider-exact
splice truth and must never be documented or consumed as reconciled provider
truth.

Persisted `RollCalendarRecord` rows are local-only under `$ALPHA_DATA_ROOT` or
`runs/**`. Committed files contain only code, parameters, docs, tests, and
value-free summaries.

## Guard Identifiers

- `roll_policy_id`: `roll_cme_index_futures_quarterly`
- `roll_guard_version`: `roll_guard_v1`
- default cross-roll policy: `drop`
- missing or ambiguous calendar policy: `drop`

Downstream label materialization must record both identifiers with any guarded
label pack so the applied guard is reproducible and auditable.

## Cross-Roll Policies

`alpha_system.labels.roll_guard.evaluate_roll_guard` evaluates one forward label
window `[entry_ts, label_horizon_ts]` against the roll calendar.

| Policy | Result |
| --- | --- |
| `drop` | Remove the window from materialized labels. |
| `truncate` | Shorten the effective label horizon to the roll-date boundary. If the entry is already on or after that boundary, return `invalid`. |
| `flag` | Keep the original horizon but return an explicit cross-roll flag. This is not a silent pass-through. |
| `invalid` | Mark the window invalid for downstream nulling or exclusion. |

If the calendar is missing or ambiguous for the requested root, the guard fails
closed by applying the safe default `drop` policy. A missing calendar never
produces a clean pass verdict.

## Roll-Window Split

`classify_roll_window`, `is_roll_window`, and `roll_window_label` expose the
deterministic roll-window split.

Default split parameters:

- `days_before_roll`: `2`
- `days_after_roll`: `1`

The labeller returns:

- `roll_window` when the timestamp date falls in the configured date window;
- `non_roll_window` when it is outside a known calendar window;
- `roll_window_unknown` when calendar coverage is missing or ambiguous.

The split is intended for diagnostics, coverage matrices, and regime-aware label
audits in later phases. It is date-level approximate metadata, not execution or
provider-splice truth.

## Locality And Scope

In scope:

- build unvalidated approximate `RollCalendarRecord`s through
  `src/alpha_system/data/foundation/rolls.py`;
- evaluate label windows through `src/alpha_system/labels/roll_guard.py`;
- expose stable policy and guard version identifiers;
- provide deterministic cross-roll verdicts and roll-window labels.

Out of scope:

- back-adjusted or ratio-adjusted continuous construction;
- full roll execution engine;
- IBKR or per-contract resolver wiring;
- provider calls or raw provider reads;
- feature or label materialization;
- profitability, capital, paper/live, broker, or production claims.
