# CROSS_IDEA_FDR_BUDGET_V1 — Family-Wise Multiplicity Control for Setup Signals

Status: PROPOSED (design + staged build plan)
Date: 2026-06-15
Lane: Yellow (governance contract — a promotion gate; gets full review)
Scope: research_lane / governance. No PnL/value truth. Research-only diagnostics.

## 0. Why (reviewer-confirmed structural blocker)

An independent adversarial reviewer adjudicated the first shelved setup signal
(`prior_session_high_sweep_and_reclaim`, ES_2020_120m, net_excursion) **REWORK —
not promoted**, on a decisive, reproduced finding: the system has **no cross-idea
multiplicity control**. The per-idea `surrogate_fdr_gate` is a single-test
block-shuffle zero-pass gate (its "FDR" name is a misnomer); `family_budget`
de-dups *variants within one family* only. The signal was 1 of a co-mined batch
of **7 sibling pa_setup ideas** (5 net_excursion) against the same slice, with a
per-test surrogate p upper bound of `(0+1)/(64+1) = 0.01538`, which does not
clear a Bonferroni family threshold (`0.05/5 = 0.01`, `0.05/7 = 0.0071`) — and,
critically, **64 surrogates cannot even resolve a passing corrected p** (finest
resolvable p = 1/65 = 0.0154 > 0.01). Until family-wise error is controlled,
broad mining will manufacture false positives at the batch level exactly as a
single test does at the row level (cf. [[law-overlap-aware-ic-power-n-eff]], the
same false-signal failure mode one layer up).

This is THE broad-mining prerequisite: thousands of ideas across many families
will explode the family-wise error surface without a budget.

## 1. Invariant (the gate this adds)

A setup signal is **promotion-eligible** (may reach the independent reviewer
shelf as a *corrected* signal) ONLY if BOTH hold:
1. **Resolution adequacy:** its surrogate `run_count` is large enough to resolve
   the family-wise-corrected threshold — `run_count ≥ ceil(m / alpha_fw) − 1`,
   where `m` = family/batch size and `alpha_fw` = family-wise alpha (so the
   finest resolvable per-test p `1/(run_count+1) ≤ alpha_fw/m`). With m=7,
   alpha=0.05 ⇒ run_count ≥ 139. Recommend ≥1000 for a stable tail.
2. **Corrected significance:** its per-test surrogate p `(pass+1)/(run+1)` clears
   the family-wise / FDR-corrected threshold across its co-mined batch
   (Benjamini–Hochberg primary; Bonferroni as the conservative fallback).

The machine still **NEVER auto-promotes** — this is a deterministic *gate*, not a
promotion. Promotion still requires the independent reviewer rail (shadow→paper→
canary→ramp downstream). The FDR gate only decides whether a signal is even
*eligible* to be shelved as a corrected candidate vs. routed to requeue/graveyard.

## 2. Design — ENHANCE, do not rebuild (REUSE-MAP grounded)

### 2.1 Per-test p from the existing surrogate gate (reuse)
The per-idea gate (`research/conditional_probe.py:build_surrogate_zero_pass_gate`,
typed as `SurrogateFdrGate` in `research_lane/fast_readout.py`) already carries
`run_count` / `gate_pass_count`. Define the per-test surrogate p upper bound
`p = (gate_pass_count + 1)/(run_count + 1)`. No change to the per-idea gate.

### 2.2 New: `governance/family_fdr_correction.py` (no existing equivalent)
Pure functions (no I/O): given a list of `(idea_key, p_value, run_count)` for one
family/batch + `alpha_fw` + method ∈ {benjamini_hochberg, bonferroni}, return per
idea a `FamilyFdrVerdict` = {corrected_threshold, rejected_null (bool),
resolution_adequate (bool), reason}. Deterministic, unit-tested against textbook
BH/Bonferroni cases.

### 2.3 New: `governance/family_fdr_ledger.py` (mirror `variant_ledger.py`)
Append-only JSONL ledger mirroring `VariantLedger` (`governance/variant_ledger.py:284-410`):
record per (family_id, slice_id, batch_key) the set of co-mined idea verdicts +
their per-test p + the corrected verdict. `evaluate_family_fdr(...)` mirrors
`evaluate_family_budget(...)`. Reuses the exact load/append/summary pattern;
fail-closed validation like `validate_variant_and_family_budget`.

### 2.4 Batch identity (reuse, no breaking YAML change)
Co-mined batch = ideas sharing `(alpha_spec_id, slice_id)` and tested together;
`family_id` already declared per idea (mechanism_card.duplicate_exposure + slice).
Do NOT add a `batch_id` YAML field. Optionally add slice-level
`family_fdr_requirement` (method) + `family_fdr_alpha` to the idea schema, parsed
in `testability_gate.TestabilitySlice.from_mapping` (which already tolerates a
`surrogate_fdr_requirement`).

### 2.5 Testability-gate declaration (extend)
Add `CHECK_FAMILY_FDR_DECLARED` to `research_lane/testability_gate.py` CHECK_ORDER:
if a slice declares `family_fdr_requirement`, the method + alpha must be known and
the batch's family_ids resolvable — a pre-test gate, fail-closed.

### 2.6 Enforcement point (Stage B — REALIZED as a provisional, accumulating ledger gate)

FDR correction is inherently **batch-level**: idea A's p cannot be corrected
without its co-mined siblings' p's. But `alpha idea run` processes ONE idea at a
time. Stage B realizes the correction via the **append-only ledger as an
accumulating, monotonically-refined provisional correction**, at the setup-lane
SIGNAL_PENDING_REVIEWER routing point in `research_lane/memory_router.py`
(`_route_signal_pending_reviewer` → `_evaluate_family_fdr_gate`):

1. Compute this idea's per-test surrogate p via
   `surrogate_p_upper_bound(gate_pass_count, run_count)` read from the **typed**
   `FastReadout.surrogate_fdr_gate` (reuse the FAST_READOUT_CONTRACT_V1 typed
   contract — no string-spelunking of the readout dict).
2. Record this idea into the `FamilyFdrLedger` keyed by batch identity
   `(alpha_spec_id, slice_id, family_id)` (`family_batch_key` /
   `create_family_fdr_ledger_record`). Idempotent append. The intra-batch
   `idea_key` is the idea's `mechanism_id` (co-mined siblings share
   alpha_spec/slice/family and differ by mechanism), falling back to
   `hypothesis_id` then `alpha_spec_id` for a singleton.
3. Load ALL sibling records for the same batch key (latest record per idea_key
   wins) and run `correct_family(entries, alpha_fw, method)` with the standing
   policy defaults (`DEFAULT_FDR_METHOD` = benjamini_hochberg, `DEFAULT_FDR_ALPHA`
   = 0.10 — the Stage-A policy source, not a second hardcoded copy).
4. Find THIS idea's `FamilyFdrVerdict`:
   - if `eligible` (rejected_null AND resolution_adequate) → keep routing to
     SIGNAL_PENDING_REVIEWER (the reviewer shelf) AND attach the family-FDR
     verdict (`method`, `alpha_fw`, `corrected_threshold`, `family_size`,
     `p_value`, plus `rejected_null`/`resolution_adequate`/`eligible`/`reason`,
     `provisional: true`) to the shelved signal record so the independent reviewer
     sees the multiplicity context.
   - else → route to **requeue** (not graveyard — it may clear as the batch fills
     or with more surrogates, mirroring the reviewer's REWORK prescription) with a
     value-free `family_fdr_requeue_reason`: `family_fdr_not_cleared` when the
     corrected null is not rejected, or `surrogate_resolution_inadequate` when the
     surrogate `run_count` cannot resolve the corrected threshold (reuses the
     Stage-A REASON_* vocabulary). The honest verdict label stays INCONCLUSIVE.

The gate is **opt-in by ledger path**: `route_verdict_to_memory(...,
family_fdr_ledger_path=...)`. The `alpha idea run` CLI wires a persistent
local-only accumulator (`<research_memory>/family_fdr_ledger.jsonl`,
`ensure_family_fdr_ledger_path`) for real runs and skips it under `--no-persist`
(the accumulator is a persistent side effect, like the route ledgers). When no
ledger is supplied the gate is a no-op and the pre-Stage-B always-shelf behavior
is preserved (so unit tests of the pure routing seam are unaffected).

**Provisional / monotonic semantics (a known, honest limitation):** because
siblings arrive across separate runs, the correction is *provisional* and refines
as the batch fills (`family_size` grows, the corrected threshold tightens). The
gate applies **at routing time**. Earlier-shelved siblings are **NOT
retroactively de-shelved** by Stage B — there is no retro-mutation of the
append-only memory. A signal shelved when its batch looked small may, once the
batch fills, no longer be family-eligible; Stage B does not walk back the earlier
shelf record. A future **batch-close re-evaluation** (a deferred follow-up) could
tighten this by re-correcting a closed batch and emitting amended verdicts. This
is recorded as a deliberate limitation, not a defect.

**Scope boundary (generic where sound, bounded where not):** Stage B applies to
the **setup lane** (`context_not_equal_trigger`) only — it has a surrogate-p
(`(pass+1)/(run+1)`). The **main_effect (IC) lane is left UNCHANGED**: its
evidence is IC + n_eff, and a main_effect family-FDR needs an IC p-value
definition that does not exist yet. We do not fabricate one. **main_effect
family-FDR = follow-up (needs an IC p-value definition).** `verdict_report.
_derive_setup_verdict` (which decides the SIGNAL_PENDING_REVIEWER verdict *label*)
is unchanged; the family gate re-routes shelf↔requeue at the router, where the
batch context lives.

**Testability-gate declaration (lighter touch, shipped):** `TestabilitySlice`
now reads optional `family_fdr_requirement` (method) + `family_fdr_alpha`,
defaulting to the policy defaults when absent, so an idea CAN pin its family
policy. This is a pure declaration parse (two optional fields + `to_dict`); it
adds **no** `CHECK_*` and a missing declaration NEVER fails the gate — the
load-bearing enforcement is in `memory_router`, as designed.

## 3. Staged rollout (additive-first; the working loop never breaks)

- **Stage A (additive, MERGED #488):** `family_fdr_correction.py` (pure math) +
  `family_fdr_ledger.py` (mirror variant_ledger) + a multiplicity canary under
  `evals/canaries/` (asserts: a batch of m co-mined per-test p's is corrected
  exactly per BH/Bonferroni; a too-small run_count is flagged
  resolution-inadequate; the historical 7-idea pa_setup batch yields the REWORK
  outcome the reviewer reached). Nothing wired into the live verdict path yet. CI
  green.
- **Stage B (wire in — REALIZED):** the optional testability-gate declaration
  parse; `memory_router` gates the setup-lane SIGNAL_PENDING_REVIEWER route on the
  family-corrected verdict + resolution adequacy via the provisional accumulating
  ledger described in §2.6; family-fails route to requeue with the value-free
  reason; the family-FDR verdict is attached to shelved signals for the reviewer.
  The `alpha idea run` CLI wires the persistent local-only accumulator. main_effect
  routing is unchanged (follow-up). Behavior change is intentional and gated by the
  new tests (`tests/unit/research_lane/test_memory_router.py`); the IVL dogfood e2e
  still passes (its REJECT route never reaches the setup-signal gate).

## 4. Acceptance

- The historical prior_high_sweep signal, fed through the family correction with
  its real batch (m=7, p=0.01538, run_count=64), yields **not-eligible** with
  reasons `resolution_inadequate` + `family_fdr_not_cleared` — i.e. reproduces the
  independent reviewer's REWORK verdict deterministically. (The gate encodes the
  reviewer's arithmetic so the machine catches it next time without a human.)
- BH/Bonferroni math unit-tested against textbook vectors.
- A signal can only be SIGNAL_PENDING_REVIEWER if resolution-adequate AND
  family-corrected-significant.
- `python tools/verify.py --all` + canaries green. No PnL/value truth; machine
  never auto-promotes; research-only language.

## 5. Correction-method policy (was: open question for the human — now RESOLVED, see §5.1)

`alpha_fw` and the method (BH vs Bonferroni) are a research-policy choice, not a
mechanical one. Default proposed: **Benjamini–Hochberg at FDR alpha = 0.10** for
exploratory setup mining (more permissive, controls expected false-discovery
proportion — appropriate for a wide hypothesis sweep feeding a downstream
independent rail), with Bonferroni FWER 0.05 available as the conservative mode.
Recommend BH-0.10 as the substrate default; surface to the user before it becomes
the standing promotion policy.

### 5.1 Resolution (recorded 2026-06-15)

**RESOLVED: Benjamini–Hochberg at FDR alpha = 0.10 is adopted as the substrate
default** for exploratory setup mining, with Bonferroni FWER 0.05 retained as the
selectable conservative mode. Rationale: BH-0.10 controls the expected
false-discovery *proportion* across a wide hypothesis sweep, which is the correct
error notion for a broad exploratory lane that feeds a downstream **independent,
adversarial rail** (shadow → paper → canary → ramp) — the rail, not this gate, is
what protects real capital, so the gate's job is calibrated breadth, not FWER
conservatism. This is a research-policy default for *recording/flagging*
`SIGNAL_PENDING_REVIEWER`, **not** an auto-promotion authority: the machine never
promotes; a signal still requires resolution-adequacy AND family-corrected
significance, and the independent reviewer adjudicates. No alpha / profitability /
tradability claim attaches to the choice of correction method. The fork above is
closed; Bonferroni-0.05 stays available per-run for a deliberately conservative
sweep.
