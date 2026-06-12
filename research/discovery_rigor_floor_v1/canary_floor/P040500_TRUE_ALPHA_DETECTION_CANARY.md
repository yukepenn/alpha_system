# P040500 Planted True-Signal Detection Canary

Campaign: `DISCOVERY_RIGOR_FLOOR_V1`
Phase: `P040500_TRUE_ALPHA_DETECTION_CANARY`
Evidence type: value-free synthetic canary threshold note

## Declared Fixtures

| Fixture | Declared SNR | Declared detectable floor | Diagnostic threshold | Expected outcome |
|---|---:|---:|---:|---|
| `synthetic_true_signal_detection_strong_v1` | 4.01 | 3.00 | abs(`directional.pearson_ic`) >= 0.95 | `DETECTED` |
| `synthetic_true_signal_detection_weak_v1` | 1.00 | 3.00 | abs(`directional.pearson_ic`) >= 0.95 | `NOT_DETECTED` |

Both fixtures are point-in-time clean. Each synthetic label is constructed as
`coefficient * feature_t + deterministic_noise`, and each label availability
timestamp is after the declared horizon end.

## Gated-Path Assertion

The detection canary writes synthetic factor and label JSONL only inside the
caller-provided temporary workspace, runs the existing research diagnostic
summary path, builds a strict `EvidenceBundle` with 4/4 required
negative-control PASS records, persists the temp `VariantLedger`, and validates
the real `DIAGNOSTICS_RUN -> EVIDENCE_READY` promotion transition.

Measured canary threshold: the strong fixture must clear
abs(`directional.pearson_ic`) >= 0.95, while the weak fixture must remain below
that same threshold. This measures a synthetic detection floor rather than a
tautological pass condition.

## Clean Twin

`evals/canaries/planted_fake_alpha_clean_twin/synthetic_fixture.json` mirrors
the P04 planted-fake-alpha fixture shape but removes lookahead: every label
references its own bar with `lookahead_k = 0` and declares no planted signal.
The clean twin must pass the same evidence-ready gate stack, proving the P04
contamination gate does not falsely block the clean shape.

## Limits

This canary validates synthetic detector sensitivity and gate wiring only. It is
not evidence of alpha validity, profitability, tradability, or production
readiness, and it does not use real market data.
