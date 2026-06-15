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

### 2.6 Enforcement point
After all siblings' per-idea gates are evaluated, the family correction runs and
the per-idea promotion-eligibility (the SIGNAL_PENDING_REVIEWER route in
`research_lane/memory_router.py` + `verdict_report._derive_setup_verdict`) is gated
on the corrected verdict + resolution adequacy. A signal that passed its single
test but fails the family correction routes to **requeue** with reason
`family_fdr_not_cleared` (not graveyard — it may clear with more surrogates / OOS),
mirroring the reviewer's REWORK prescription.

## 3. Staged rollout (additive-first; the working loop never breaks)

- **Stage A (additive):** `family_fdr_correction.py` (pure math) + `family_fdr_ledger.py`
  (mirror variant_ledger) + a multiplicity canary under `evals/canaries/`
  (asserts: a batch of m co-mined per-test p's is corrected exactly per BH/Bonferroni;
  a too-small run_count is flagged resolution-inadequate; the historical 7-idea
  pa_setup batch yields the REWORK outcome the reviewer reached). Nothing wired
  into the live verdict path yet. CI green.
- **Stage B (wire in):** testability-gate declaration check; memory_router/verdict
  gate setup promotion-eligibility on the corrected verdict + resolution adequacy;
  route family-fails to requeue. Re-run the IVL dogfood e2e; behavior change is
  intentional and gated by the new tests.

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

## 5. Open question for the human (genuine fork, not a knowable default)

`alpha_fw` and the method (BH vs Bonferroni) are a research-policy choice, not a
mechanical one. Default proposed: **Benjamini–Hochberg at FDR alpha = 0.10** for
exploratory setup mining (more permissive, controls expected false-discovery
proportion — appropriate for a wide hypothesis sweep feeding a downstream
independent rail), with Bonferroni FWER 0.05 available as the conservative mode.
Recommend BH-0.10 as the substrate default; surface to the user before it becomes
the standing promotion policy.
