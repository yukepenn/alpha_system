# Diagnostics Fast Path

`SHIP_REFIT-P02` adds a pure-Python surrogate diagnostics fast path for
seeded label perturbations. It preserves the existing surrogate truth chain and
changes only how shuffled labels are represented during calibration.

## Design

- The reference JSONL writers remain available as the parity reference.
- The execution path builds an aligned factor/label diagnostic panel once per
  StudySpec and represents each seed as a permutation index from target label
  row to source label value.
- The same permutation builders drive the reference writers and the fast path:
  label shuffle, equal-length trade-date block shuffle, and equal-length
  trade-date block bootstrap.
- Per-seed study outputs, ledgers, surrogate records, detection threshold,
  zero-pass aggregation, constant-factor exclusion, and `spec_index -> seed`
  mapping remain unchanged.
- The fast path does not write per-seed shuffled-label JSONL copies under
  `seed_<n>/labels/`.

## Parity Gate

The local parity test is:

```bash
PYTHONPATH=src python -m pytest tests/unit/governance/test_surrogate_run.py -q
```

It compares materialized-reference and fast-path `diagnostic_summary.json`
hashes over ten deterministic seeds on the synthetic governance StudySpec
fixture, then verifies the fast path leaves no per-seed label-copy file.

## Calibration Guardrail

`tools/discovery_rigor_floor/run_real_surrogate_calibration.py` now defaults
`--runs-per-config` to the local cap and caps oversized CLI values at the same
bound. Explicit values within the bound pass through unchanged.
