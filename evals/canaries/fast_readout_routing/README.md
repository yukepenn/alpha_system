# Canary: fast_readout routing contract

Purpose: guard the fast-probe `readout` glue seam. The runner
(`src/alpha_system/governance/canaries/fast_readout_routing.py`, registered in
`tools/hooks/canary_runner.py`) asserts that the current producer shapes for
both lanes parse into the typed `FastReadout` contract
(`src/alpha_system/research_lane/fast_readout.py`), round-trip, and expose the
correct canonical `n_eff` per lane -- and that a deliberately DRIFTED field makes
`FastReadout.from_dict` RAISE `FastReadoutContractError`.

Covered shapes (Stage A of `FAST_READOUT_CONTRACT_V1`):

- `main_effect_recorded` -- `_run_main_effect` (study_kind=main_effect, RECORDED);
  canonical n_eff = `readout.factor_diagnostics_report.quality_summary.ic_power_n_eff`.
- `setup_zero_pass_met` -- `_run_context_not_equal_trigger` ZERO_PASS_MET;
  canonical n_eff = top-level `power.n_eff`; carries the continuous lift +
  surrogate gate.
- `setup_surrogate_blocked` -- `_build_surrogate_blocked_readout` (INCONCLUSIVE);
  carries the real surrogate gate; n_eff from top-level `power.n_eff`.
- `data_gap` -- `build_fast_probe_data_gap` (INCONCLUSIVE/DATA_GAP); n_eff = 0.

The JSON files in this directory are SHAPE FIXTURES: structural mirrors of the
verified producer key shapes. They contain no real market data, factor values,
labels, scores, or study values -- only the structural keys the contract pins.
The runner constructs equivalent fixtures programmatically and keeps them in sync
with the producer; these JSONs document the pinned shapes for human audit. A
passing canary validates contract/producer agreement only and does not imply any
alpha, profitability, or tradability claim.
