# Mechanism Card Template — DIFFERENTIATED_SUBSTRATE_V1

Status: VALUE-FREE design template. A mechanism card is a pre-registration of a
RESEARCH HYPOTHESIS to be tested, not a claim that an edge exists. No card may
contain IC/return/Sharpe values or any alpha/tradability/profitability claim.
Diagnostics and gates decide promotion; the card only declares intent, inputs,
lookahead controls, and orthogonality reasoning so the test is honest and bounded.

Each card under `cards/` is a JSON object with the fields below. This Markdown
file documents the schema and the allowed/expected values for each field.

## Field schema

- `mechanism_id` (string): stable kebab/snake id, unique within the campaign,
  e.g. `fomc_drift`. Used to key the card and to derive the eventual
  `StudySpec`/`AlphaSpec` family grouping. Must not collide with a dead-mechanism
  id (regime, liquidity_pa, bbo_tradability, vwap_session).

- `hypothesis` (object):
  - `statement` (string): the mechanism rationale — WHY an edge could plausibly
    exist, stated as a falsifiable behavioral conditioning claim, not a
    profitability assertion. Research-only language.
  - `economic_rationale` (string): the structural reason the conditioning
    variable could relate to forward behavior (e.g. positioning/hedging flow,
    scheduled information arrival, dealer gamma), again value-free.

- `expected_horizon` (string or list): candidate forward horizon(s) under test,
  e.g. `"5m"`, `"30m"`, or `["5m","30m"]`. Pre-registered so horizon count is
  counted against the FDR budget.

- `expected_session` (string): session/window scope, e.g. `"RTH"`, `"ETH"`,
  `"event_window"`, `"month_end_session"`. Reuses `SessionFeatureName` segmenting
  vocabulary where possible (`rth_segment_flag`, `eth_segment_flag`, `session_id`).

- `expected_sign` (string): `"up"`, `"down"`, `"reversion"`, `"continuation"`,
  or `"undirected"`. A directional prior is allowed as PRE-REGISTRATION only; the
  diagnostics decide, and an undirected/two-sided test is preferred when the prior
  is weak. The sign here does NOT pre-judge the outcome.

- `conditioning_variable` (object):
  - `name` (string): the event/calendar conditioner, e.g.
    `minutes_to_scheduled_event`, `is_opex_day`, `is_month_end_session`.
  - `knowability` (string): one of `pre_event_knowable` (schedule/calendar known
    ahead, point-in-time legal as a live feature) or `post_event_knowable`
    (surprise/actual-vs-consensus magnitude, knowable ONLY after release — must be
    treated as labels-only / offline diagnostic conditioning, never a live feature).

- `required_features` (object):
  - `existing` (list): reusable existing features by exact symbol, e.g.
    `["session_calendar_roll_day_of_week","session_calendar_roll_minutes_to_expiration"]`.
  - `new` (list of objects): each `{name, family, feature_request_required: true,
    reason}` describing a feature that needs a new `FeatureRequest` (`freq_`) via
    `require_feature_request_implementation_allowed`. `family` is either an
    existing `FeatureFamily` member to extend (`session_calendar_roll`,
    `cross_market`) or `"NEW:event_calendar"` if a new family member is proposed.

- `required_labels` (object):
  - `existing` (list): reusable outcome labels by exact symbol, e.g.
    `["fixed_horizon","midprice_forward","event:return_to_vwap"]`.
  - `new` (list of objects): each `{name, label_family, label_spec_required: true,
    reason}` for any outcome label that needs a new governance `LabelSpec`
    (`lspec_`).

- `lookahead_risk` (object):
  - `level` (string): `"low" | "medium" | "high"`.
  - `description` (string): the specific lookahead hazard.
  - `mitigation` (string): the point-in-time control. For schedule features the
    control is "scheduled event times are known-ahead and carried as point-in-time
    metadata with `metadata.available_ts <= row.available_ts` (the existing
    `_require_metadata_known_as_of` guard pattern)." For surprise/magnitude inputs
    the control is "post-event-knowable; usable only as an OFFLINE diagnostic
    conditioner or labels-only, never as a live feature."
  - `pre_event_knowable_features` (list): features safe to know before the event.
  - `post_event_knowable_features` (list): features knowable only after release.

- `expected_orthogonality_to_dead_mechanisms` (object):
  - `statement` (string): WHY this conditioning is expected to be orthogonal to
    the rejected price-action/BBO main effects (value-free reasoning).
  - `shared_inputs_with_dead` (list): any input also used by a dead mechanism
    (transparency; more shared inputs ⇒ lower claimed orthogonality).
  - `diagnostic_check` (string): the orthogonality diagnostic to run (e.g.
    residualize against the dead-mechanism factor before scoring). Diagnostic
    decides; this is the planned check, not a claimed result.

- `capacity_turnover_note` (string): qualitative, value-free note on event
  frequency / number of conditioning occurrences per year and the implied
  turnover regime (e.g. "~8 FOMC + ~12 CPI windows/yr ⇒ low occurrence count ⇒
  N_eff-limited; pool across instruments per Track-B"). No capacity dollar claim.

- `data_dependency` (object):
  - `class` (string): `"existing_substrate"`, `"derivable_from_exchange_calendar"`,
    or `"needs_paid_data"`.
  - `detail` (string): what exactly is needed.
  - `deferred_pending_user_approval` (bool): `true` whenever `needs_paid_data`.

- `value_free_status` (object):
  - `contains_values` (bool): MUST be `false`.
  - `claims` (string): MUST be a no-claims string, e.g.
    `"hypothesis pre-registration only; no alpha/tradability/profitability claim"`.

## Hard rules for every card

1. No IC/return/Sharpe/PnL values anywhere. `value_free_status.contains_values`
   must be `false`.
2. Scheduled event TIMES are pre-event-knowable; SURPRISE magnitudes are
   post-event-knowable and never become live features.
3. Any externally-sourced macro release feed is `needs_paid_data` and
   `deferred_pending_user_approval: true`.
4. Do NOT reuse or touch the `bbo_tradability` namespace.
5. Every new feature/label is gated by a new `FeatureRequest` / `LabelSpec`; the
   card only declares the need, it does not author the request.
6. Cards are counted against `FDR_BUDGET.md`. Authoring a card consumes
   pre-registered budget; it is not free exploration.
