# FUTSUB Kill-Shot VariantLedger Reconciliation Audit (Pre-Invocation)

Date: 2026-06-12
Audit type: PRE-INVOCATION reconciliation (read-only)
Closes: `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` row 8;
`handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 6.

Run context: FUTSUB-P28 has NOT run. Run
`2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is stopped at
the pre-P28 boundary (STOP present). No Track A metric exists. Therefore no
per-study kill-shot VariantLedger entries can exist yet; this audit verifies,
for each intended invocation, that the intended ledger linkage is well-defined
and will be enforced fail-closed at invocation time, and it reconciles the
Track-B pooled entries registered 2026-06-12 (which DO exist, status PLANNED).

Status vocabulary: `matched` | `pending_creation_enforced` | `unmatched_gap`.

## Enforcement Basis (code citations)

The RIGOR-P02 fail-closed entry hook is
`validate_variant_and_family_budget` (`src/alpha_system/governance/variant_ledger.py:684`).
A study invocation REQUIRES a VariantLedger entry under these conditions:

- Creation point: promotion-gate transition `DIAGNOSTICS_ALLOWED ->
  DIAGNOSTICS_RUN` calls the hook with `persist=True, require_recorded=False`
  (`src/alpha_system/governance/promotion_gate.py:208-223`, hook call at
  `:213-218`), deriving `VariantLedgerRecord`s from the TrialLedger via
  `variant_ledger_records_from_trial_ledger`
  (`src/alpha_system/governance/variant_ledger.py:609-642`) and appending them
  (`variant_ledger.py:815-816`).
- Refusal point: transition `DIAGNOSTICS_RUN -> EVIDENCE_READY` calls the hook
  with `persist=False, require_recorded=True`
  (`src/alpha_system/governance/promotion_gate.py:225-243`, hook call at
  `:233-238`); missing records raise issue code
  `variant_ledger_missing_records` (`variant_ledger.py:731-745`). The CLI
  surface `alpha governance build-evidence` drives exactly this transition with
  an explicit `--variant-ledger-path`
  (`src/alpha_system/cli/governance.py:326-359`, argument at `:702-706`).
- Fail-closed path supply: the live ledger file location is supplied
  explicitly at runtime (`PromotionGateContext.variant_ledger_path`,
  `promotion_gate.py:117`; CLI `--variant-ledger-path`). There is no default
  path and no environment fallback. Missing/vague path raises
  `missing_variant_ledger_path` (`variant_ledger.py:413-426`); missing file
  raises `missing_variant_ledger` (`variant_ledger.py:1298-1308`); unwritable
  file raises `unwritable_variant_ledger` (`variant_ledger.py:1311-1346`).
- Budget refusal: study variant-budget overrun without a pre-declared
  amendment raises `variant_budget_overrun` (`variant_ledger.py:758-772`).
  Family roll-up applies only when the StudySpec declares `family_budget`
  (`variant_ledger.py:777`).
- Integration proof: `research/discovery_rigor_floor_v1/integration_audit/RIGOR-P07_gate_audit.md`
  rows "Variant/family budget entry hook" and "Promotion gate composition";
  bypass canaries
  `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py`.
- Reviewer intent: RIGOR-P02 review (run-local
  `runs/2026-06-11T223643Z_DISCOVERY_RIGOR_FLOOR_V1/phases/RIGOR-P02/review.md`,
  verdict PASS_WITH_WARNINGS) confirms the hook wiring and records warning 3:
  downstream consumers including "the future FUTSUB-P28 kill-shot runner" must
  supply `study_spec`/`family_id`/`variant_ledger_path` context.

## Reconciliation Table — Six Re-Locked Rerun Invocations

Committed StudySpecs: `research/futures_substrate_scaleout_v1/rerun/study_specs/sspec_*.json`.
Data-root search (`/home/yuke_zhang/alpha_data/alpha_system`, recursive) found
NO per-study VariantLedger JSONL referencing any of the six study ids; the only
variant ledger present is the Track-B pooled ledger (section below). Intended
variant linkage for each invocation: `VariantLedgerRecord`s derived
deterministically from the study's TrialLedger records, keyed
`(study_spec_id, variant_id)`, within the declared `variant_budget`.

| study_spec_id | alpha_spec_id | variant_budget | family_budget | existing ledger entry | intended linkage / enforcement citation | classification | issue codes |
|---|---|---:|---|---|---|---|---|
| `sspec_652fcc23a6f725b405612b8e` | `aspec_b40aee52d4399dd5b855a6ed` | 4 | not declared | none found | hook creation `promotion_gate.py:208-223` (persist=True); refusal `promotion_gate.py:225-243` + `variant_ledger.py:731-745` | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |
| `sspec_676a012a4a4cdf3d169cd981` | `aspec_43cd6c154bca2fcc419eee83` | 4 | not declared | none found | same citations | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |
| `sspec_1d87dfbe3d24810720f75014` | `aspec_eb962fc197eaf3955c5e4711` | 4 | not declared | none found | same citations | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |
| `sspec_c2114a3c6c90595350151af0` | `aspec_df2d040e45564c259ef3de6d` | 4 | not declared | none found | same citations | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |
| `sspec_950ad6bb7063928d9ff8ea4f` | `aspec_39ffc190cfbfa6ba0b1a2a25` | 4 | not declared | none found | same citations | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |
| `sspec_6088f0ed5b02b161bfb54943` | `aspec_1284e49b083df11eeb0481ea` | 4 | not declared | none found | same citations | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |

Issue code definitions (caveats, not gaps — enforcement exists for all six):

- `live_ledger_path_undeclared`: no committed artifact pins the live per-study
  VariantLedger JSONL path for the kill-shot reruns. The path is supplied
  explicitly at invocation and the hook fails closed on a missing path or
  missing file (`variant_ledger.py:413-426`, `:1298-1308`). Coordinator
  precondition: declare and initialize the kill-shot per-study ledger file
  before driving `DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN`; a missing file
  yields refusal (`missing_variant_ledger`), never silent pass.
- `family_id_supplied_at_invocation`: the committed sspec JSONs carry no
  family field; the hook requires an explicit non-empty `family_id`
  (`variant_ledger.py:963-968`) supplied in the invocation context. Absence
  yields refusal (`empty_required_field`), never silent pass. `family_budget`
  is absent from all six sspecs, so the family roll-up check is by-design
  inactive (`variant_ledger.py:777`).

Boundary caveat (recorded for the coordinator, classification unchanged):
the FUTSUB-P28 phase spec
(`specs/ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1/FUTSUB-P28.md`) contains
zero VariantLedger references, and the runtime diagnostics tool surface
(`src/alpha_system/runtime/**`) has no call site into
`validate_variant_and_family_budget` (callers are
`governance/promotion_gate.py` and governance canaries only). Enforcement
therefore engages at the promotion-gate boundary (entry creation at
`DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN`; recorded-entry refusal at
`DIAGNOSTICS_RUN -> EVIDENCE_READY`, the FUTSUB-P29 verdict path), not inside
the raw P28 diagnostic tool calls. No diagnostic output can become evidence or
a verdict without the recorded entry (`variant_ledger_missing_records`,
integration-audit row "Promotion gate composition"). Issue code:
`entry_hook_engages_at_promotion_boundary_not_diagnostic_call`. The kill-shot
operator must drive the gate transitions (or `alpha governance
build-evidence`) with the explicit ledger context, per RIGOR-P02 review
warning 3.

## Track-B Pooled Entries (registered 2026-06-12)

Live files under
`/home/yuke_zhang/alpha_data/alpha_system/futsub_killshot_track_b/`:
`pooled_hypotheses.jsonl` (2 records), `pooled_variant_ledger.jsonl`
(2 records), `pooled_registration_trials.jsonl` (2 records). Registration
surface: `alpha governance register-pooled-hypothesis`
(`src/alpha_system/cli/governance.py:396-421`), which appends the embedded
`variant_ledger_record` itself
(`src/alpha_system/governance/pooled_hypothesis.py:292-360`, append at
`:342`), so hypothesis/ledger agreement is enforced by construction and
re-verified here by exact field comparison.

| pooled_hypothesis_id | pool_kind | variant_id | trial_ids | status | created_at | ledger entry exact match | trial present and consistent | classification |
|---|---|---|---|---|---|---|---|---|
| `poolhyp_67427c04adfc2dc97fd42bc5` | `cross_symbol` | `pooled-track-b-cross-symbol-v1` | `trial_1b8ca7e8f2b837b9887e7121` | `PLANNED` | `2026-06-12T05:06:10Z` | yes (all 8 fields equal) | yes | `matched` |
| `poolhyp_797417343726708a0d2d9939` | `cross_horizon` | `pooled-track-b-cross-horizon-v1` | `trial_84ffee90a2153e7fe9fe12fa` | `PLANNED` | `2026-06-12T05:06:10Z` | yes (all 8 fields equal) | yes | `matched` |

Field-level checks performed (deterministic dict equality, all pass):
`variant_id`, `alpha_spec_id`, `study_spec_id`, `family_id`, `attempt_count`,
`trial_ids`, `status` (`PLANNED`), `created_at` — each pooled hypothesis's
embedded `variant_ledger_record` equals exactly one `pooled_variant_ledger.jsonl`
row; each `trial_id` exists in `pooled_registration_trials.jsonl` with matching
`variant_id`, `study_spec_id`, `alpha_spec_id`, and status `PLANNED`.

Observation (not a gap): both pooled records carry
`alpha_spec_id = aspec_2982c385e0fae9ebcdc22a2d` and
`study_spec_id = sspec_652fcc23a6f725b405612b8e`; this alpha_spec_id differs
from the committed sspec_652fcc23a6f725b405612b8e alpha_spec_id
(`aspec_b40aee52d4399dd5b855a6ed`). The pooled hypothesis is its own
pre-registered governance object with its own alpha spec identity; the linkage
is internally consistent across all three Track-B files. Issue code (recorded
for traceability only): `pooled_alpha_spec_id_distinct_from_member_sspec`.

## P110000_RELOCK_V2 Supersession Addendum

The reconciliation above is the pre-invocation audit for the P022000 re-lock
anchors. P110000_RELOCK_V2 supersedes those StudySpecs with fresh locks against
current `REGISTERED` successors. For any post-P110000 Track-A or Track-B
operation, use the successor ids below.

| P022000 re-lock anchor | P110000_RELOCK_V2 successor |
| --- | --- |
| `sspec_652fcc23a6f725b405612b8e` | `sspec_f6cbd88caa0445f0f56d81fd` |
| `sspec_676a012a4a4cdf3d169cd981` | `sspec_1604b063f3a3401208ee0239` |
| `sspec_1d87dfbe3d24810720f75014` | `sspec_dec89a327a9c50957adca780` |
| `sspec_c2114a3c6c90595350151af0` | `sspec_840e8342564226f2c3257903` |
| `sspec_950ad6bb7063928d9ff8ea4f` | `sspec_c237c6a8ce40c2585836fae0` |
| `sspec_6088f0ed5b02b161bfb54943` | `sspec_533f665ec4ac063dbb664a54` |

The two Track-B pooled records registered at `2026-06-12T05:06:10Z` are now
historical P022000-anchor records. They must not be reused as post-P110000
evidence contracts. The coordinator must register replacement Track-B pooled
hypotheses against the P110000 successor ids before any Track-A metric is
computed; the Track-A marker remained absent at relock time.

## Roll-Up

- Six rerun candidate invocations: 0 `matched` (expected pre-invocation),
  6 `pending_creation_enforced`, 0 `unmatched_gap`.
- Track-B pooled entries: 2 `matched`, 0 mismatches; pooled trial ids 2/2
  present and consistent.
- Real findings requiring coordinator action before STOP removal: none at
  `unmatched_gap` severity. Preconditions to honor at kill-shot time:
  initialize and declare the live per-study VariantLedger path
  (`live_ledger_path_undeclared`), supply explicit `family_id` per study
  (`family_id_supplied_at_invocation`), and drive the promotion-gate
  transitions with ledger context so entry creation occurs at
  `DIAGNOSTICS_ALLOWED -> DIAGNOSTICS_RUN`
  (`entry_hook_engages_at_promotion_boundary_not_diagnostic_call`). All three
  failure directions are refusals, not silent passes.

## Value-Free Attestation

This audit contains only study ids, alpha spec ids, variant ids, trial ids,
pooled hypothesis ids, ledger row counts, declared budgets, statuses,
timestamps, file paths, code citations, and issue codes. No market data,
diagnostic values, metric values, return or PnL figures appear. No alpha,
profitability, tradability, execution-quality, production-readiness,
paper-trading, live-trading, broker, order-routing, or deployment claim is
made.
