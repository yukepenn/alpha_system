# RIGOR-P05 Synthetic Surrogate-FDR Calibration

This report is value-free: it records run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, or diagnostic values.

## Threshold

- Declared threshold: zero shuffled runs may pass the promotion gate.
- Threshold verdict: `zero-pass-met`.
- Any shuffled pass is `LEAKAGE_BLOCKED` and requires diagnosis before the kill-shot resumes.
- Errored runs block calibration success and are not counted as non-passes.

## Synthetic Calibration Summary

- Run count: 2
- Error count: 0
- Gate pass count: 0
- Gate pass rate: 0.000000

## Per-Run Seeds And Outcomes

| StudySpec | Seed | Outcome | Surrogate ID | Reason |
|---|---:|---|---|---|
| sspec_1c1d4248e923531afaaf2bd8 | 5000 | BLOCKED | surrun_b09c096721fcf0be8d19edba | UNDERPOWERED |
| sspec_1c1d4248e923531afaaf2bd8 | 5001 | BLOCKED | surrun_6b1c51e8d138a968b82e18c0 | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded label-shuffled calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
