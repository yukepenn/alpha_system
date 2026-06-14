# DK-P01 — Zero-Feed Calendar Substrate: New SESSION_CALENDAR_ROLL Flags (Additive, Parity-Gated)

---
campaign_id: DIFFERENTIATED_KILLSHOT_V1
phase_id: DK-P01
lane: YELLOW
status: draft
dependencies: [DK-P00]
executor: Codex GPT-5.5 high
reviewer: Claude Opus 4.8 xhigh
verifier: Claude Sonnet 4.6
---

## Purpose

Build the new zero-feed, known-ahead calendar flags that three Track A mechanisms (`opex_pinning`,
`month_end_flow`, `roll_week_flow`) need to express their conditioning factor — as **strictly
additive** members of the **existing** `SESSION_CALENDAR_ROLL` family (NOT a new `FeatureFamily`),
**double-implemented** value-identically under the fast-vs-reference parity gate, and admitted only
via an **APPROVED** `FeatureRequest`. This phase delivers substrate only: it builds and materializes
the flags. It computes **no** factor IC, no study, and no real-data metric — those are gated behind
DK-P02 (surrogate-FDR zero-pass) and DK-P03 (real-data evidence). The two mechanisms that need no
new substrate (`day_of_week_effect`, `open_close_auction_flow`) reuse existing `SessionFeatureName`
members and get **no** new build here.

## Context

This is the second phase of the differentiated-substrate kill-shot. It depends on **DK-P00**, which
committed the value-free **FDR active-subset restatement** (`research/differentiated_substrate_v1/
FDR_ACTIVE_SUBSET_RESTATEMENT.md`) and the REUSE-MAP/SCOPE lock. The FDR-before-metric gate is
therefore already in place; this phase must respect it by producing **no** real-data metric.

**Reused machinery (locked by the DK-P00 REUSE-MAP — extend, never rebuild):**

- Reference family: `src/alpha_system/features/families/session/family.py` — `SessionFeatureName`
  (`StrEnum`, class at line 53), the `_transform_id` map (line 645), `_INPUT_FIELDS_BY_FEATURE`
  (line 357), the `wrap`/definition builders, and the `_feature_point` compute branch (line 791,
  e.g. the `DAY_OF_WEEK` branch at line 810). New members are added to **each** of these five seams.
- Fast path: `src/alpha_system/features/fast/session_calendar_roll.py` — `_feature_expression`
  (polars branch, line 214). `PACK_FEATURES` is **auto-derived** as `tuple(... for feature_name in
  SessionFeatureName)` (line 31), so the parity test enumerates every enum member; a new member
  with no matching fast branch fails the parity test and raises `PackMaterializerError`.
- Calendar primitives (zero-feed): `src/alpha_system/data/foundation/rolls.py` — `third_friday`
  (line 728), `CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS = (3, 6, 9, 12)` (line 97), and
  `build_analytic_cme_equity_index_quarterly_roll_calendar` (line 787).
- Roll-window classifier: `src/alpha_system/labels/roll_guard.py` — `classify_roll_window`
  (line 236; `roll_window_days_before` / `roll_window_days_after` defaults), returning a
  `RollWindowVerdict` with `in_roll_window`.
- Committed calendar config: `configs/data/session_templates_and_calendar.json` (schema
  `alpha_system.session_calendar.v1`, timezone `America/Chicago`, covered window **2024–2026**,
  `non_claims: [not_exchange_official, not_holiday_complete, not_production_certified]`).
- Admission gate: `src/alpha_system/governance/feature_request.py` —
  `create_feature_request(...)` (line 141; `freq_`-prefixed deterministic content-hash id via
  `generate_feature_request_id`) and the `FeatureRequestApprovalStatus.APPROVED` value.
  `build_session_feature_definition` (family.py line 383) **fails closed** — "Missing, invalid,
  unapproved, duplicate-blocked, or registry-unchecked requests fail closed" — so each new flag
  needs an APPROVED `FeatureRequest`.
- Parity fixtures: `tests/fixtures/feature_compute_fast_path/session_calendar_roll.py`; parity test
  at `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py`.

**Relevant global hard invariants (this phase):**

- **FDR before metric:** no real-data IC/return/diagnostic value may be inspected before the DK-P00
  FDR active-subset restatement (already committed) **and** the DK-P02 surrogate-FDR `ZERO_PASS_MET`
  gate. This phase produces substrate only — **zero** real-data metrics.
- **Zero-feed, known-ahead:** the new flags are `live=True` / **CAUSAL** / POINT_IN_TIME (NOT
  `offline_only`), with `available_ts <= row.available_ts`. They are derived entirely from analytic
  exchange-calendar arithmetic and the committed calendar config — **no external date/strike/OI/
  auction feed**.
- **No countdown reuse:** the flags must **never** use the offline-only `live=False`
  `SessionFeatureName.BARS_TO_ROLL` / `MINUTES_TO_ROLL` countdown features (family.py lines 62–63,
  319–320, `_RollProximity`); `in_roll_window_flag` is a known-ahead boolean from
  `classify_roll_window`, not a countdown.
- **Single-factor path byte-unchanged:** no edit to `SINGLE_FACTOR_THRESHOLD_TEMPLATE` /
  `StudyConfig` / `src/alpha_system/strategies/templates.py` (a forbidden path) and no edit to the
  value engine (`core/value_store.py`, a forbidden path). New work is strictly additive.
- **No new dependency / no paid data:** `numpy`/`pandas`/`polars` stay unimportable at the venv
  level (the fast path obtains polars only via `require_dependency` inside the pack builder, never as
  a top-level runtime import); `fomc`/`cpi` stay DEFERRED (needs_paid_data); no new paid data.
- **Allowed outputs / research-only language:** non-claims must be stated explicitly
  (`not_exchange_official`, `not_holiday_complete`, approximate-roll, fail-absent-outside-coverage);
  no alpha/tradability/profitability claim; no promotion.

## Scope

Strictly additive substrate work, faithful to the DK-P01 entry in `campaigns/
DIFFERENTIATED_KILLSHOT_V1/campaign.yaml`:

1. **Add five new `SessionFeatureName` members** to the **existing** `SESSION_CALENDAR_ROLL`
   family (NOT a new family): `is_opex_day_flag`, `is_quad_witch_day_flag`,
   `is_month_end_session_flag`, `is_quarter_end_session_flag`, `in_roll_window_flag`. In
   `src/alpha_system/features/families/session/family.py`, wire each member through **all five
   reference seams**: the `SessionFeatureName` enum (line 53), `_transform_id` (line 645),
   `_INPUT_FIELDS_BY_FEATURE` (line 357), the definition `wrap`/builder path, and a `_feature_point`
   compute branch (line 791). Each flag is `live=True` / **CAUSAL** / POINT_IN_TIME, **not**
   `offline_only` (contrast the roll-countdown branch handling at family.py lines 529, 611, 620).

2. **Mirror each new member value-identically in the polars fast path**
   (`src/alpha_system/features/fast/session_calendar_roll.py`, `_feature_expression`, line 214). The
   auto-derived `PACK_FEATURES` (line 31) makes the parity test enumerate every enum member, so a
   missing fast branch fails the parity test / raises `PackMaterializerError`. The fast and reference
   branches must produce byte-identical values on the parity fixtures.

3. **Derive the flags zero-feed**, session-local timezone `America/Chicago`, DST-correct, matching
   the existing `day_of_week` (`weekday()` minus 1) and RTH open/close conventions:
   - `is_opex_day_flag` — analytic `third_friday(year, month)` of **every** month (monthly equity
     options expiration).
   - `is_quad_witch_day_flag` — `third_friday` of **only** Mar/Jun/Sep/Dec
     (`CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS`).
   - `is_month_end_session_flag` — the **last TRADING session** of the calendar month, computed as
     the final covered session **within the committed calendar's covered window**
     (`configs/data/session_templates_and_calendar.json`, 2024–2026). **Fail-absent outside
     coverage** (do not extrapolate); carry the `not_exchange_official` / `not_holiday_complete`
     non-claim.
   - `is_quarter_end_session_flag` — the last trading session of Mar/Jun/Sep/Dec, same
     covered-window / fail-absent / non-claim discipline.
   - `in_roll_window_flag` — `roll_guard.classify_roll_window(...).in_roll_window` over
     `build_analytic_cme_equity_index_quarterly_roll_calendar(...)`, using the **default** window
     (2 trading-adjacent days before + 1 after); carry the **approximate-roll** non-claim. **Never**
     use `BARS_TO_ROLL` / `MINUTES_TO_ROLL`.

4. **Author APPROVED `FeatureRequest`(s)** via `governance.feature_request.create_feature_request`
   (deterministic `freq_` content-hash id) — one per new flag (or one per coherent group),
   declaring `requested_inputs`, `formula_sketch`, `availability_assumptions`,
   `duplicate_or_equivalent_exposure_notes` (note overlap vs `day_of_week` / the roll-countdown
   features), `data_requirements`, and `approval_status=APPROVED`. `build_session_feature_definition`
   fails closed without an APPROVED request, so this admission is mandatory.

5. **Extend the parity fixtures** at `tests/fixtures/feature_compute_fast_path/
   session_calendar_roll.py` to cover the five new flags (including dates that exercise an OPEX
   Friday, a quad-witch Friday, a month-end session, a quarter-end session, and an in-roll-window
   day), and add/extend tests so the parity, no-lookahead/`available_ts`, and FeatureRequest-gate
   assertions cover the new members.

6. **Run no-lookahead / `available_ts` audits** for the new flags (each `available_ts <=
   row.available_ts`, CAUSAL window).

7. **Materialize** the five new flags on **ES/NQ/RTY** for the study window via
   `alpha feature materialize` (writes local-only Parquet + registry; serialized by the
   `materialization_registry` resource class). These outputs are **local-only and NEVER committed**.

The two mechanisms needing no new substrate reuse existing members and get **no** new build:
`day_of_week_effect` reuses `SessionFeatureName.DAY_OF_WEEK`; `open_close_auction_flow` reuses
`MINUTES_FROM_RTH_OPEN` / `MINUTES_TO_RTH_CLOSE` / `RTH_SEGMENT_FLAG`.

## Non-Goals

- Any factor IC / study / surrogate calibration / real-data metric (that is DK-P02 / DK-P03).
- Any external date feed; any strike, open-interest, or auction-imbalance data; any paid data
  (`fomc`/`cpi` stay DEFERRED).
- Creating a **new** `FeatureFamily` (the flags are additive members of the existing
  `SESSION_CALENDAR_ROLL` family).
- New `SessionFeatureName` members for `day_of_week_effect` or `open_close_auction_flow` (both reuse
  existing members).
- Reusing or re-enabling the offline-only `live=False` `BARS_TO_ROLL` / `MINUTES_TO_ROLL` countdown.
- Any edit to the single-factor template (`strategies/templates.py`) or the value engine
  (`core/value_store.py`) — both forbidden paths.
- Any horizon sweep, per-instrument split, grid, or geometry sweep.
- Committing any materialized Parquet/registry artifact, or any `runs/**`/data/DB artifact.
- Any promotion, FactorLibrary entry, or alpha/tradability/profitability claim.

## Expected Files (illustrative, not prescriptive)

- `src/alpha_system/features/families/session/family.py` — edit (add five enum members + their
  `_transform_id`, `_INPUT_FIELDS_BY_FEATURE`, builder/`wrap`, and `_feature_point` branches;
  existing members untouched).
- `src/alpha_system/features/fast/session_calendar_roll.py` — edit (add five value-identical polars
  `_feature_expression` branches).
- `src/alpha_system/governance/feature_request.py` — typically **no edit** (the function is reused);
  the APPROVED `FeatureRequest` payload(s) are authored as data/test fixtures or research artifacts,
  not by changing this module. Edit only if a missing helper is genuinely required and stays additive.
- `research/differentiated_substrate_v1/feature_requests/**` — new (the APPROVED `FeatureRequest`
  JSON declarations + a zero-feed provenance note: derivations, covered-window, non-claims).
- `tests/fixtures/feature_compute_fast_path/session_calendar_roll.py` — edit (extend fixtures).
- `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py` and close-by
  session/calendar/roll/no-lookahead/feature_request tests — new/edit (parity, no-lookahead,
  `available_ts`, FeatureRequest-gate coverage for the five new members).
- `configs/**` — edit only if a config entry is genuinely required for the new flags; do not modify
  the committed calendar data semantics.
- `docs/differentiated_killshot_v1/**` — optional, a short substrate note (no claims).

## Forbidden Changes

- Editing any path under `forbidden_paths`: `src/alpha_system/{execution,broker,live,portfolio,
  management,backtest,l2,agent_factory}/**`, `src/alpha_system/core/value_store.py`,
  `src/alpha_system/strategies/templates.py`, `research/futures_substrate_scaleout_v1/**`,
  `research/futures_core_alpha_pilot_v1/**`, all `data/**`, and any
  `*.sqlite`/`*.db`/`*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`.
- Modifying `SINGLE_FACTOR_THRESHOLD_TEMPLATE` / `StudyConfig` / the single-factor study path (must
  stay byte-unchanged); modifying the value engine (`core/value_store.py`).
- Renaming, reordering, or changing the value semantics of any **existing** `SessionFeatureName`
  member, `_transform_id` entry, `_INPUT_FIELDS_BY_FEATURE` entry, or `_feature_point` branch.
- Marking any new flag `offline_only` / `live=False`, or deriving any flag from
  `BARS_TO_ROLL` / `MINUTES_TO_ROLL`.
- Weakening the FeatureRequest fail-closed admission gate, the parity gate, the no-lookahead/
  `available_ts` audit, the surrogate zero-pass invariant, or any canary; adding visible test-only
  branches.
- Importing `backtest` / `management` / `fast_path` / `value_store` from `research/` (no
  research→reference-sim bridge; no second PnL truth).
- Adding a runtime dependency (`numpy`/`pandas`/`polars` stay unimportable at the venv level); new
  paid data; secrets/credentials; raw/canonical/factor/label data, caches, model binaries, large
  artifacts.
- Committing any materialized Parquet/registry output or any `runs/**` artifact.
- `git add .` / `git add -A`, force push, auto-merge, deployment, PR creation, or any broker/live
  call.

## Interfaces / Contracts

- **Additive enum, full five-seam wiring.** Each new `SessionFeatureName` member appears in the enum
  (line 53), `_transform_id` (line 645), `_INPUT_FIELDS_BY_FEATURE` (line 357), the definition
  builder/`wrap`, and a `_feature_point` compute branch (line 791). Existing members are
  byte-unchanged.
- **Parity contract (auto-derived).** `PACK_FEATURES = tuple(... for feature_name in
  SessionFeatureName)` (fast path line 31) enumerates every member; the polars `_feature_expression`
  (line 214) must emit a branch for each new flag, value-identical to the reference `_feature_point`
  branch on the parity fixtures. A missing/mismatched fast branch fails the parity test / raises
  `PackMaterializerError`.
- **Zero-feed derivations.** opex = `third_friday(year, month)` every month; quad-witch =
  `third_friday` for `CME_EQUITY_INDEX_QUARTERLY_CYCLE_MONTHS` only; month/quarter-end = last covered
  trading session within the 2024–2026 calendar window (fail-absent outside coverage);
  in_roll_window = `classify_roll_window(ts, build_analytic_cme_equity_index_quarterly_roll_calendar
  (...), ...).in_roll_window` with default 2-before/1-after window. All `America/Chicago`,
  DST-correct, matching the existing `day_of_week`/open-close conventions.
- **Known-ahead contract.** `live=True` / CAUSAL / POINT_IN_TIME; `available_ts <=
  row.available_ts`; never the offline-only countdown features.
- **Admission contract.** `create_feature_request(..., approval_status=APPROVED)` yields a `freq_`
  content-hash id; `build_session_feature_definition` fails closed without an APPROVED request, so
  each new flag is gated by an APPROVED `FeatureRequest` declaring inputs / formula sketch /
  availability assumptions / duplicate-exposure notes.
- **Non-claims carried in declarations and the provenance note:** `not_exchange_official`,
  `not_holiday_complete`, fail-absent-outside-coverage, approximate-roll.

Illustrative (non-prescriptive) materialization invocation — local-only, never committed:

```bash
# Materialize the five new flags for the study window (writes local Parquet + registry only).
alpha feature materialize --family session_calendar_roll \
  --feature is_opex_day_flag,is_quad_witch_day_flag,is_month_end_session_flag,is_quarter_end_session_flag,in_roll_window_flag \
  --instrument ES,NQ,RTY --execute
```

## Artifact Policy

Run artifacts and materialized values are local-only and must never be committed:

- `runs/**` is **local-only runtime state** (run state, events, costs, STOP, run-local
  `handoff.md`/`review.md`/`verdict.json`, checks, repair attempts) — local audit and resume only.
  No `runs/` path appears under Allowed Paths.
- Materialized feature Parquet + the registry/`*.sqlite` written by `alpha feature materialize` are
  **never** staged or committed.
- A commit-eligible handoff goes under `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P01.md`.
- `git ls-files runs` must return empty.
- Never commit: `runs/**`, any `*.parquet`/`*.arrow`/`*.feather`/`*.dbn`/`*.zst`/`*.sqlite`/`*.db`,
  `data/raw/**`, `data/canonical/**`, `data/factors/**`, `data/labels/**`, `data/cache/**`,
  `secrets/**`, `**/*.key`.

### Allowed Paths (commit-eligible — explicit staging only)

These are the **only** paths this phase may stage and commit. Stage by explicit path; never
`git add .` / `git add -A`; never force push.

- `src/alpha_system/features/**`
- `src/alpha_system/governance/feature_request.py`
- `tests/**`
- `configs/**`
- `research/differentiated_substrate_v1/**`
- `docs/differentiated_killshot_v1/**`
- `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P01.md`
- `reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P01/**`

### Local-only run artifacts (NOT commit-eligible, never staged)

- `runs/**` and all materialized Parquet/registry outputs from `alpha feature materialize` — local
  audit/use only. **No `runs/` or materialized-value path appears under Allowed Paths above.**

## Allowed Test Paths

- `tests/**` (the extended `tests/fixtures/feature_compute_fast_path/session_calendar_roll.py`, the
  parity test `tests/unit/feature_compute_fast_path/test_session_calendar_roll_pack.py`, and close-by
  session/calendar/roll/parity/feature_request/no-lookahead tests for the five new members). Do not
  weaken or skip existing tests; do not add visible test-only special cases.

## Validation

Run from the repo root. All commands are local-only, safe, and make **no** provider, network, merge,
or external call.

```bash
# 1) Narrowest meaningful tests first — the new flags and their gates.
python -m pytest tests -k "session or calendar or roll or parity or feature_request or no_lookahead" -q

# 2) Repo smoke.
python tools/verify.py --smoke

# 3) Safety canaries must remain all-PASS (planted_fake_alpha + true-alpha pair,
#    forbidden_second_pnl_truth, forbidden_exploratory_promotion, governance_random_target,
#    forbidden_scope_drift).
python tools/hooks/canary_runner.py

# 4) No new dependency: numpy/pandas/polars must remain unimportable at the venv level.
python -c "import importlib,sys; [sys.exit('numpy/pandas/polars must NOT import') for m in ('numpy','pandas','polars') if importlib.util.find_spec(m)]"

# 5) No research->reference-sim bridge: research/ imports none of backtest/management/fast_path/value_store.
grep -rEn "import +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)|from +(alpha_system\.)?(backtest|management|fast_path|core\.value_store)" --include=*.py src/alpha_system/research && echo "FORBIDDEN IMPORT FOUND" && exit 1 || echo "no forbidden research->sim imports"

# 6) Single-factor template + value engine byte-unchanged (must print nothing).
git diff --name-only -- src/alpha_system/strategies/templates.py src/alpha_system/core/value_store.py

# 7) Run-artifact discipline: must print nothing.
git ls-files runs
```

Broaden to the authoritative suite (`python tools/verify.py --all`) if shared feature, parity, or
governance behavior appears affected; run it in a clean shell with `FRONTIER_*` env unset to avoid
the known driver-env false negative. Record any skipped check and its reason in the handoff.

## Done Criteria

- The five new flags (`is_opex_day_flag`, `is_quad_witch_day_flag`, `is_month_end_session_flag`,
  `is_quarter_end_session_flag`, `in_roll_window_flag`) exist in **both** the reference family
  (`features/families/session/family.py`, all five seams) and the polars fast path
  (`features/fast/session_calendar_roll.py`), **value-identical under the parity gate**.
- Each flag is `live=True` / **CAUSAL** / POINT_IN_TIME (not `offline_only`); none derives from
  `BARS_TO_ROLL` / `MINUTES_TO_ROLL`.
- APPROVED `FeatureRequest`(s) present (`freq_` ids) declaring inputs / formula sketch / availability
  assumptions / duplicate-exposure notes; `build_session_feature_definition` admission succeeds for
  the new flags and still fails closed without approval.
- No-lookahead / `available_ts` audits pass for the new flags; zero-feed derivations carry the
  `not_exchange_official` / `not_holiday_complete` / fail-absent / approximate-roll non-claims.
- Flags materialized on **ES/NQ/RTY** for the study window locally (uncommitted Parquet/registry).
- `day_of_week_effect` and `open_close_auction_flow` reuse existing members — no new build.
- Single-factor path (`strategies/templates.py`) and value engine (`core/value_store.py`) untouched;
  `research/` imports no `backtest`/`management`/`fast_path`/`value_store`.
- `python tools/hooks/canary_runner.py` all-PASS; `numpy`/`pandas`/`polars` remain unimportable;
  no new paid data.
- `git ls-files runs` empty; explicit staging only; no edits under `forbidden_paths`.
- Commit-eligible handoff written; YELLOW review artifacts present.

## Handoff Requirements

Write the commit-eligible handoff at `handoffs/DIFFERENTIATED_KILLSHOT_V1/DK-P01.md`: scope
delivered, the exact validation commands run with results, any skipped check + reason, files changed
by path, and explicit confirmation that — (a) all five new flags are wired through both the
reference family (five seams) and the polars fast path and pass the parity gate; (b) each flag is
`live=True`/CAUSAL/POINT_IN_TIME and uses **no** `BARS_TO_ROLL`/`MINUTES_TO_ROLL` countdown;
(c) the zero-feed derivations and their non-claims (not_exchange_official, not_holiday_complete,
fail-absent-outside-coverage, approximate-roll) are recorded; (d) APPROVED `FeatureRequest`(s) gate
the new flags and the gate still fails closed without approval; (e) the flags were materialized on
ES/NQ/RTY locally and **no** Parquet/registry artifact was staged; (f) the single-factor template
and value engine are byte-unchanged and `research/` imports no reference-sim module; and (g) no
real-data metric was inspected. The run-local `runs/<run_id>/.../handoff.md` stays local-only and
must not be staged.

## Review Requirements

YELLOW lane requires a fresh Claude Opus review. Commit-eligible review notes + verdict belong under
`reviews/DIFFERENTIATED_KILLSHOT_V1/DK-P01/**`; run-local `review.md`/`verdict.json` stay under
`runs/<run_id>/...` and are not committed. The reviewer must adversarially confirm: the five flags
are **additive** members of the existing `SESSION_CALENDAR_ROLL` family (no new family; existing
members byte-unchanged); the fast and reference implementations are value-identical under the
**auto-derived** parity gate; the derivations are genuinely **zero-feed** (analytic third-Friday,
covered-window last-trading-session with fail-absent, `classify_roll_window` over the analytic
quarterly roll) with no external feed and **no** `BARS_TO_ROLL`/`MINUTES_TO_ROLL` reuse; each flag is
`live=True`/CAUSAL with `available_ts <= row.available_ts` (no lookahead); the FeatureRequest
admission is APPROVED and still fail-closed without approval; the non-claims are stated; **no**
real-data metric was inspected (FDR-before-metric preserved); the single-factor path and value
engine are byte-unchanged; `research/` has no reference-sim import; `numpy`/`pandas`/`polars` remain
unimportable; and artifact + staging discipline is honored (no Parquet/registry/`runs/` committed).

## Auto-Merge / Review Policy

This spec authorizes no PR creation, no auto-merge, and no deployment. Merge gating is the Ralph
driver's responsibility under the YELLOW lane policy (review required; block on critical /
test-tamper / boundary violation) and human authorization — not this spec.

## Repair-or-Rollback

- **In-scope repair only:** fix the new enum-member wiring, the polars mirror, the FeatureRequest
  declarations, the parity/no-lookahead fixtures/tests, or the zero-feed derivations within the
  Allowed Paths; do not expand scope to fix unrelated findings.
- **Rollback:** the change is additive and pure-Python; revert the five new enum members and their
  five reference seams, the five polars fast-path branches, the APPROVED `FeatureRequest`
  declarations, and the extended fixtures/tests to restore the prior state — no migration, no
  committed-data change (materialized Parquet/registry are local-only and discardable).
- **STOP / escalate (do not auto-proceed):** any pressure to modify the single-factor engine or
  value engine, change an existing `SessionFeatureName` member, mark a flag `offline_only` / derive
  it from the roll countdown, create a new family, weaken the FeatureRequest/parity/no-lookahead
  gates, inspect a real-data metric before DK-P02's surrogate zero-pass, add a dependency or paid
  data, import a reference-sim module from `research/`, or commit a Parquet/registry/`runs/` artifact
  — treat as out-of-scope and surface to the user.
