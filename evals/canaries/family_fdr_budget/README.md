# Canary: family_fdr_budget (cross-idea multiplicity)

Purpose: guard the cross-idea family-wise multiplicity correction math
(`src/alpha_system/governance/family_fdr_correction.py`). The runner
(`src/alpha_system/governance/canaries/family_fdr_budget.py`, registered in
`tools/hooks/canary_runner.py`) asserts:

1. **Textbook BH / Bonferroni.** On the classic Benjamini-Hochberg (1995)
   p-value vector (`benjamini_hochberg_1995_vector.json`), step-up BH at FDR
   alpha=0.05 rejects exactly the first four nulls (ranks 1..4); Bonferroni at
   FWER alpha=0.05 (threshold `0.05/15 = 0.003333`) rejects exactly the first
   three. Hardcoded expected rejection sets.

2. **The historical pa_setup REWORK reproduces deterministically**
   (`pa_setup_rework_batch.json`). The first shelved setup signal
   (`prior_session_high_sweep_and_reclaim`, ES_2020_120m, net_excursion) was 1
   of a co-mined batch of `m = 7` sibling pa_setup ideas (5 net_excursion) with
   a per-test surrogate p `(0 + 1) / (64 + 1) = 0.0153846` at `run_count = 64`.
   The independent reviewer adjudicated **REWORK** because 64 surrogates cannot
   even RESOLVE a passing corrected p: the finest resolvable p `1/65 = 0.01538`
   exceeds the Bonferroni family threshold `0.05/7 = 0.00714`. The canary asserts
   the gate now reaches the SAME conclusion deterministically:
   `resolution_adequate == False` AND `eligible == False`, with a reason citing
   resolution inadequacy. It checks BOTH the `m = 7` (all siblings; the
   reviewer's primary reading) and `m = 5` (net_excursion-only subset)
   interpretations -- not-eligible under both.

3. **Non-vacuity.** A clearly-significant, resolution-adequate idea
   (`p = 0.0001`, `run_count = 10000`, `m = 5`) is `eligible == True`.

The JSON files in this directory are SHAPE / VECTOR fixtures: the textbook
p-value vector and the historical batch numbers the runner asserts against. They
contain no real market data, factor values, labels, or scores -- only the
correction inputs and expected outcomes. The runner constructs the equivalent
inputs programmatically and keeps them in sync; these JSONs document the pinned
vectors for human audit. A passing canary validates the correction math only and
implies NO alpha, profitability, or tradability claim. The corrected verdict is
a deterministic RECORD; the machine never auto-promotes.
