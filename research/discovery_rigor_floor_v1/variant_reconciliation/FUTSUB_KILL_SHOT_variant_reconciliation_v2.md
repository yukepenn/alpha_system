# FUTSUB Kill-Shot VariantLedger Reconciliation Audit — V2 (Post-RELOCK_V2, Pre-Invocation)

- Date: `2026-06-13`
- Audit type: PRE-INVOCATION reconciliation (read-only, coordinator-dispatched)
- Supersedes: `research/discovery_rigor_floor_v1/variant_reconciliation/FUTSUB_KILL_SHOT_variant_reconciliation.md`
  (generated `2026-06-12T05:06Z` against the P022000 re-lock V1 anchors; its
  `P110000_RELOCK_V2` supersession addendum flagged that replacement Track-B
  records must be registered against the successor ids before any Track-A metric
  — this V2 audit reconciles exactly those replacements).
- Closes (re-run against V2): `research/discovery_rigor_floor_v1/KILL_SHOT_READINESS.md` row 8;
  `handoffs/DISCOVERY_RIGOR_FLOOR_V1/FUTSUB_KILL_SHOT_RESUME.md` step 6.

## Run Context

FUTSUB-P28 has NOT run. Run
`2026-06-07T235209Z_ALPHA_FUTURES_RESEARCH_SUBSTRATE_SCALEOUT_V1` is stopped at
the pre-P28 boundary (STOP present). No Track-A metric exists, so no per-study
kill-shot VariantLedger entries can exist yet; this audit verifies, for each
intended V2 invocation, that the ledger linkage is well-defined and will be
enforced fail-closed at invocation time, and it reconciles the two V2 Track-B
pooled entries (registered `2026-06-12T12:40:00Z`, status `PLANNED`) against the
live VariantLedger.

Corpus under audit (POST-RELOCK_V2): the six content-addressed successor
StudySpecs from P110000_RELOCK_V2 and the two V2 Track-B pooled hypotheses.

Status vocabulary: `matched` | `pending_creation_enforced` | `unmatched_gap`.

## Enforcement Basis (code citations, re-verified against current code)

The RIGOR-P02 fail-closed entry hook is `validate_variant_and_family_budget`
(`src/alpha_system/governance/variant_ledger.py:703`). A study invocation
REQUIRES a VariantLedger entry under these conditions:

- Creation point: promotion-gate transition `DIAGNOSTICS_ALLOWED ->
  DIAGNOSTICS_RUN` calls the hook with `persist=True, require_recorded=False`
  (`promotion_gate.py:208-223`, hook call `:213-218`).
- Refusal point: transition `DIAGNOSTICS_RUN -> EVIDENCE_READY` calls the hook
  with `persist=False, require_recorded=True` (`promotion_gate.py:225-243`, hook
  call `:233-238`); missing records raise `variant_ledger_missing_records`
  (`variant_ledger.py:731-745`). CLI `alpha governance build-evidence` drives
  this transition with explicit `--variant-ledger-path`.
- Fail-closed path supply: live ledger path supplied explicitly at runtime
  (`PromotionGateContext.variant_ledger_path`, `promotion_gate.py:118`). No
  default/env fallback. Missing path → `missing_variant_ledger_path`
  (`variant_ledger.py:413-426`); missing file → `missing_variant_ledger`
  (`:1298-1308`); unwritable → `unwritable_variant_ledger` (`:1311-1346`).
- Budget refusal: variant-budget overrun without pre-declared amendment →
  `variant_budget_overrun` (`:758-772`). Family roll-up applies only when the
  StudySpec declares `family_budget` (`:777`); none of the six V2 sspecs do.
- Family id: hook requires non-empty `family_id` via `_require_family_id`
  (`:963`), else `empty_required_field`.
- Integration proof: `integration_audit/RIGOR-P07_gate_audit.md` rows
  "Variant/family budget entry hook" + "Promotion gate composition"; bypass
  canaries `tests/unit/discovery_rigor_floor/test_rigor_p02_bypass_canaries.py`.

All citations re-read for this V2 audit; behavior/issue-codes identical to V1
(only the function-definition line moved `:684`→`:703`).

## Reconciliation — Six RELOCK_V2 Successor Rerun Invocations

Committed StudySpecs under `research/futures_substrate_scaleout_v1/rerun/study_specs/`
(git-tracked; each `variant_budget=4`, no `family_budget`, no `family_id`). A
recursive search of the data root found NO per-study VariantLedger referencing
any of the six V2 study ids (they appear only inside surrogate-FDR manifests),
which is correct pre-invocation. Intended linkage: `VariantLedgerRecord`s derived
from each study's TrialLedger at the creation transition.

| V2 study_spec_id | family | variant_budget | existing entry | classification | issue codes |
|---|---|---:|---|---|---|
| `sspec_f6cbd88caa0445f0f56d81fd` | vwap | 4 | none (pre-invocation) | `pending_creation_enforced` | `live_ledger_path_undeclared`; `family_id_supplied_at_invocation` |
| `sspec_1604b063f3a3401208ee0239` | vwap | 4 | none | `pending_creation_enforced` | same |
| `sspec_dec89a327a9c50957adca780` | regime | 4 | none | `pending_creation_enforced` | same |
| `sspec_840e8342564226f2c3257903` | liq | 4 | none | `pending_creation_enforced` | same |
| `sspec_c237c6a8ce40c2585836fae0` | liq | 4 | none | `pending_creation_enforced` | same |
| `sspec_533f665ec4ac063dbb664a54` | bbo | 4 | none | `pending_creation_enforced` | same |

Issue codes are operating preconditions, NOT gaps — every failure direction is a
refusal, never a silent pass:
- `live_ledger_path_undeclared`: no committed artifact pins the live per-study
  ledger path; supplied at invocation; missing path/file fails closed
  (`variant_ledger.py:413-426`, `:1298-1308`).
- `family_id_supplied_at_invocation`: sspec JSONs carry no `family_id`; hook
  requires it (`:963`), absence → `empty_required_field`. No `family_budget` →
  family roll-up by-design inactive (`:777`).
- Boundary caveat `entry_hook_engages_at_promotion_boundary_not_diagnostic_call`:
  the FUTSUB-P28 spec and `runtime/**` have no call site into the hook;
  enforcement engages at the promotion-gate boundary (entry creation at
  `DIAGNOSTICS_ALLOWED->DIAGNOSTICS_RUN`; recorded-entry refusal at
  `DIAGNOSTICS_RUN->EVIDENCE_READY`, the FUTSUB-P29 verdict path). No diagnostic
  output becomes evidence without the recorded entry. The kill-shot operator
  must drive the gate transitions with explicit ledger context (RIGOR-P02 review
  warning 3).

## Track-B Pooled Entries — V2 (registered 2026-06-12T12:40:00Z)

Live files under `~/alpha_data/alpha_system/futsub_killshot_track_b/`:
`pooled_hypotheses.jsonl` (4: 2 historical V1 + 2 V2), `pooled_variant_ledger.jsonl`
(4), `pooled_registration_trials.jsonl` (4). Registration appends the embedded
`variant_ledger_record` by construction (`pooled_hypothesis.py:342`), so
hypothesis/ledger agreement is enforced and re-verified here by exact dict match.

| pooled_hypothesis_id | pool_kind | status | created_at | ledger exact match | trial present | classification |
|---|---|---|---|---|---|---|
| `poolhyp_d3b3d986369b525618a1caa0` | `cross_symbol` | `PLANNED` | `2026-06-12T12:40:00Z` | yes (1 row, all fields equal) | yes | `matched` |
| `poolhyp_0755f59753552574a8092624` | `cross_horizon` | `PLANNED` | `2026-06-12T12:40:00Z` | yes (1 row, all fields equal) | yes | `matched` |

Both carry `registered_before_metrics: true`, `alpha_spec_id =
aspec_5c56d1ad51dc2d8ae4a88edd`, and anchor the V2 successor
`sspec_f6cbd88caa0445f0f56d81fd`. Members: cross_symbol = f6cbd88#symbol=ES|NQ|RTY
@5m; cross_horizon = f6cbd88#horizon=5m|15m|30m on ES. Field-level dict equality
(variant_id, alpha_spec_id, study_spec_id, family_id, attempt_count=1, trial_ids,
status=PLANNED, created_at) passes for both.

Historical V1 records (`poolhyp_67427c04...`, `poolhyp_797417343...`, both
anchoring retired `sspec_652fcc...`) remain as immutable history and are NOT
post-RELOCK_V2 evidence contracts; out of scope here.

## Roll-Up

- Six V2 rerun invocations: 0 `matched` (expected pre-invocation),
  6 `pending_creation_enforced`, 0 `unmatched_gap`.
- Track-B V2 pooled entries: 2 `matched`, 0 mismatches, 2/2 trials consistent.
- `unmatched_gap` severity findings requiring action before STOP removal: NONE.
  Preconditions to honor at kill-shot time: declare/initialize the live
  per-study VariantLedger path, supply explicit `family_id` per study, drive the
  promotion-gate transitions with ledger context. All failure directions are
  refusals, not silent passes.

VERDICT: PASS. The POST-RELOCK_V2 corpus satisfies variant reconciliation — every
intended invocation is matched-or-fail-closed and there is zero `unmatched_gap`.
No V2 study id and no V2 pooled id can reach a metric without a recorded
VariantLedger entry.

## Value-Free Attestation

This audit contains only ids, ledger row counts, declared budgets, statuses,
timestamps, file paths, code citations, and issue codes. No market data,
diagnostic, metric, return, or PnL values appear. No alpha, profitability,
tradability, execution-quality, production-readiness, paper/live, broker, or
deployment claim is made.
