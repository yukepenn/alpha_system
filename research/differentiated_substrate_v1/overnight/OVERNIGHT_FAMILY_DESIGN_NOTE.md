# Governed Overnight Family — Design Note (DIFFERENTIATED_SUBSTRATE_V1, priority 3)

Status: VALUE-FREE research-prep design note. No code, no data, no diagnostics,
no IC/return/Sharpe values, no alpha/tradability/profitability claims. Diagnostics
and gates decide promotion, never priors. This is a DESIGN NOTE, not a set of
mechanism cards: it scopes what a governed overnight (close-to-open /
close-to-close) family would require under existing rigor before any card or
`LabelSpec` is authored. It deliberately stops short of authoring cards.

## Why "governed" and why a separate note

Intraday differentiated substrate (event-calendar, flow/seasonality) reuses the
existing intraday forward-return labels and the session features. An OVERNIGHT
family is structurally different: the holding window crosses the ETH/RTH
boundary and (for close-to-close) a full maintenance break, so it carries
gap-risk and roll-splice hazards that the intraday cards do not. Those hazards
are why this family is held to a stricter standard and marked **RED-lane at
paper/live** (a gap-risk approval gate), even though the offline research
artifacts here are value-free Green.

## Lane classification

- Offline design + label/feature DEFINITION work (this note, any future cards,
  any future `LabelSpec`/`FeatureRequest` authoring, surrogate-FDR calibration):
  **Yellow** (material research; fresh Claude review), value-free.
- Any paper or live use of an overnight signal: **RED**. Holding through the
  close into the next session is gap-risk-bearing and broker-adjacent; it
  requires scoped authorization (`PROJECT_OP_AUTHORIZED` / `PROJECT_OP_SCOPE` /
  `PROJECT_OP_EXPIRES`) and an explicit gap-risk approval gate. No overnight
  position is taken automatically. This campaign expects to avoid Red scope; the
  Red marking is a forward constraint on the family, not a request to arm it now.

## Label definitions (explicit)

Two anchored overnight outcome windows are pre-registered. Both are LABELS-ONLY
forward windows (`WindowCausality.FUTURE`, `offline_only=True`,
`future_data_legal_only_for_labels`), consistent with the existing label
machinery.

### 1. close-to-open (overnight gap)

- Entry anchor: the last RTH bar of session D (use the existing
  `session_calendar_roll_minutes_to_rth_close` clock to identify the RTH close
  anchor; do NOT invent a new close timestamp).
- Outcome window: from the RTH close of session D to the RTH open of session
  D+1 (the overnight gap, spanning the ETH session and the maintenance break).
- This is the gap return over the held-overnight window. Sign undirected; the
  diagnostic decides.

### 2. close-to-close (overnight + next RTH)

- Entry anchor: the last RTH bar of session D.
- Outcome window: from the RTH close of session D to the RTH close of session
  D+1 (spans one full maintenance break, the overnight, and the next regular
  session).

Both definitions MUST be expressed against the actual session template
(`SessionWindowState` / `classify_session_timestamp` /
`CME_INDEX_FUTURES_SESSION_TEMPLATE_ID`) so that `EARLY_CLOSE` and `HOLIDAY`
sessions shift the anchors correctly and a holiday-adjacent overnight is never
mislabeled.

## What this family REUSES vs what needs a new `LabelSpec`

Reuse-first (REUSE-MAP rule). Repo-exact:

- `fixed_horizon` family (`src/alpha_system/labels/families/fixed_horizon/family.py`)
  already has `FixedHorizonLabelName.SESSION_CLOSE` and
  `FixedHorizonLabelName.MAINTENANCE_FLAT`, plus `MID_FWD_RET_*` mid-price
  variants. `SESSION_CLOSE` / `MAINTENANCE_FLAT` are the closest existing
  anchored-to-close / flat-at-maintenance outcomes and MUST be inspected first:
  if a close-to-open / close-to-close label can be expressed as a configuration
  of these existing labels (anchor = session close, horizon = next open/close),
  NO new `LabelSpec` is authored. Prefer reuse.
- `event` family (`src/alpha_system/labels/families/event/family.py`) is
  strategy-agnostic price-path OUTCOME labels (`breakout_success`,
  `return_to_vwap`, `sweep_outcome`, `liquidity_quality_future`); these are NOT
  overnight-anchored and are reused only if a path-outcome variant of the
  overnight window is wanted later.
- A NEW `LabelSpec` (`lspec_`) is required ONLY if the close-to-open /
  close-to-close window CANNOT be expressed as a configuration of the existing
  `SESSION_CLOSE` / `MAINTENANCE_FLAT` / `fixed_horizon` labels — for example if
  the gap return must be anchored to the RTH-open of D+1 specifically (a
  cross-session anchor the current labels may not express). The new `LabelSpec`
  would live in the `fixed_horizon` family (close-anchored forward return with a
  next-session-open / next-session-close horizon). This note declares the need;
  it does not author the `LabelSpec`.

Conditioning FEATURES reuse the session family
(`src/alpha_system/features/families/session/family.py`): `session_id`,
`minutes_from_rth_open`, `minutes_to_rth_close`, `rth_segment_flag`,
`eth_segment_flag`, `day_of_week`. The known-ahead seasonality conditioners from
the priority-2 flow cards (day-of-week, month-end, roll-window) are reusable
overnight conditioners. No new conditioning feature is strictly required for the
baseline close-to-open / close-to-close labels.

> Producer / second-truth boundary: any value-emitting fast-path code lives only
> in the sanctioned producer namespaces (`labels/fast/**`, `features/fast/**`)
> and stays reference-parity-gated. This note does NOT introduce a second
> value/accounting truth and does NOT touch the `bbo_tradability` namespace. Note
> that `features/fast/vwap_session_auction.py` (which contains overnight-range
> producer code) belongs to the DEAD `vwap_session` mechanism; the overnight
> family must not be built on top of it or be conflated with it.

## Gap-risk budget (pre-registered, value-free)

The overnight window is exposed to a discrete close-to-open gap. The gap-risk
budget is a pre-registered DESIGN CONSTRAINT, not a result:

- Gaps must be measured and reported as a first-class diagnostic of the held
  window, separated from the in-session path. The overnight return is dominated
  by the discrete gap, so it must never be reported as if it were a smooth
  intraday return.
- A maximum tolerated single-overnight adverse-gap threshold and a maximum
  cumulative overnight drawdown threshold are pre-registered on the eventual
  StudySpec/runbook (the THRESHOLDS are pre-registered; the realized VALUES are
  diagnostics, reported value-free here). Breaching either is a stop condition
  for any paper/live use, gated by the Red approval.
- Earnings-adjacent and scheduled-macro-overnight sessions (e.g. an overnight
  that spans a pre-FOMC or pre-CPI window) carry elevated gap risk and are
  flagged as a separate conditioning split, not silently pooled with ordinary
  overnights.

## ETH liquidity / spread gates (pre-registered)

The held window spans the ETH session, where liquidity is thinner and spreads
wider. Pre-registered gates (value-free design constraints):

- Overnight windows are segmented by the existing `eth_segment_flag` /
  `rth_segment_flag` so the ETH leg is explicitly identified.
- A pre-registered ETH liquidity/spread gate (minimum traded activity / maximum
  spread proxy over the ETH leg) must be declared on the StudySpec before any
  overnight study is treated as evidence. Bars failing the gate are flagged, not
  silently included. The spread proxy must come from existing point-in-time
  OHLCV/session substrate, NOT from the `bbo_tradability` namespace (out of
  scope) and NOT from paid L2/MBO depth data (deferred-pending-user-approval).
- Real fees/costs for the overnight hold (financing/carry treatment for a
  multi-session hold) are pre-registered as required inputs to any net
  diagnostic, per the Compass real-fees precondition; this note does not assert
  any net value.

## Stricter drawdown treatment

Overnight exposure is held through periods of no/low ability to manage the
position. The family is therefore held to a stricter drawdown treatment than the
intraday cards:

- Drawdown is computed including the full overnight gap, not just the in-session
  path (no gap is netted out or smoothed).
- A stricter pre-registered drawdown threshold than the intraday families is set
  on the StudySpec/runbook. The threshold is pre-registered; the realized
  drawdown is a diagnostic, reported value-free.
- The stricter-drawdown rule and the gap-risk budget together are part of the
  Red-lane gap-risk approval gate: paper/live use is blocked until both are
  satisfied under scoped authorization.

## Hard rule: NEVER silently cross maintenance / roll

This is the load-bearing governance rule for the family.

- Maintenance break: a close-to-close window spans the daily maintenance break by
  construction; this must be EXPLICIT in the label definition (anchored against
  the session template's `maintenance_breaks`), never an accidental side effect
  of a naive fixed-bar-count horizon. A close-to-open window must explicitly end
  at the next RTH open and not run past it.
- Roll splice: any overnight window whose horizon would span a quarterly
  contract roll MUST be passed through the existing roll guard
  (`src/alpha_system/labels/roll_guard.py`, `evaluate_roll_guard`) with the
  default `RollCrossPolicy.DROP` (or pre-registered `TRUNCATE` / `FLAG`), and the
  safe-default DROP when the roll calendar is missing or ambiguous
  (`SAFE_MISSING_CALENDAR_POLICY`). An overnight label that crosses a roll
  boundary without a roll-guard verdict is INVALID and must fail closed. This
  reuses the existing guard; it does NOT build a new one (REUSE-MAP rule).
- Roll-window overnights (close-to-open / close-to-close anchored inside the
  quarterly roll window from the `roll_week_flow` card) are the highest-risk
  overlap of overnight + roll and must be either dropped or explicitly
  roll-guarded, never silently spliced across contracts.

## FDR / multiple-testing placement

The overnight family is counted against the extended FDR budget in
`FDR_BUDGET_PRIORITY_2_3.md` (NOT the original `FDR_BUDGET.md`). It is pooled
across the index-futures family per Track-B, with no near-duplicate sibling
variants (close-to-open and close-to-close are the two pre-registered windows,
counted explicitly, not silently expanded). Surrogate-FDR zero-pass calibration
(`calibrate_surrogate_fdr`, `ZERO_PASS_MET` / `LEAKAGE_BLOCKED`) gates evidence
exactly as for the intraday families and is mandatory before any overnight study
is treated as evidence.

## Deferred / out-of-scope

- Paid overnight microstructure data (ETH L2/MBO depth, auction imbalance) is
  `deferred_pending_user_approval`. Long-deferred per the Compass for cost.
- No mechanism cards are authored in this note. Authoring overnight cards
  consumes pre-registered budget and is a later, separately-reviewed step.
- No `LabelSpec` / `FeatureRequest` is authored here; only the need is declared.
