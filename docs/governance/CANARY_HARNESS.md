# Governance Canary Harness

`ARGOV-P14` adds an executable, deterministic, synthetic canary harness for
three catalogued negative controls:

- `future_shift`
- `permuted_labels`
- `optimistic_fill`

The harness lives in `alpha_system.governance.canaries.harness`. It uses the
`ARGOV-P13` negative-control catalog and `NegativeControlResult` contract as the
source of truth. It does not add new canary types, alter expected-failure
vocabulary, run real studies, ingest real data, compute factors, materialize
labels, run broker or paper systems, route orders, or make alpha, profitability,
tradability, capital-allocation, live-readiness, or production-readiness claims.

## Fail-Closed Contract

A governance canary injects a known-bad synthetic fault into a tiny fixture and
calls the corresponding guard. The result is recorded as:

- `PASS` when the guard detects or rejects the injected fault, so
  `observed_result == expected_failure`.
- `FAIL` when the guard misses the injected fault, so
  `observed_result != expected_failure`.

The harness does not silently drop missed faults. Missed faults remain valid
`NegativeControlResult` records only as `FAIL`.

## Executable Canaries

`future_shift` uses the label-leakage guard's availability-time check. Its
fixture shifts a requested feature's `information_time` to the label availability
timestamp, which the guard flags as lookahead.

`permuted_labels` is the catalogued label-integrity control used for the
ARGOV-P14 label-leakage canary. Its fixture requests a feature that overlaps the
`LabelSpec.forbidden_feature_overlap` declaration, which the guard flags as a
blocking label-as-feature finding.

`optimistic_fill` uses execution-assumption guards. Its fixture attempts
same-bar optimistic execution timing and target-first same-bar ordering. The
execution config guard rejects the non-conservative timing, and the same-bar
fill-bar check rejects a fill on the signal bar.

`random_target` remains catalogued but is not executable in ARGOV-P14.

## Fixtures

The default fixtures are tiny synthetic, non-market JSON files under:

- `evals/canaries/future_shift/synthetic_fixture.json`
- `evals/canaries/permuted_labels/synthetic_fixture.json`
- `evals/canaries/optimistic_fill/synthetic_fixture.json`

These fixtures contain metadata only. They are not raw data, canonical data,
factor values, label values, diagnostics output, research evidence, or market
evidence.

## Canary Runner

`tools/hooks/canary_runner.py` runs the governance canaries alongside the
existing Frontier safety canaries:

```bash
python tools/hooks/canary_runner.py
```

The runner exits non-zero if any governance canary fails to fail closed. Existing
hook canary scenarios are unchanged.
