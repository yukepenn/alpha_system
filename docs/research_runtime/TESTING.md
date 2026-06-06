# Research Runtime Testing

RT-P20 adds fail-closed tests for the Research Runtime. A guard that does not
block a prohibited shortcut is treated as a failing guard.

## Commands

Run the targeted RT-P20 suites:

```bash
python -m pytest tests/unit/runtime/fail_closed tests/no_lookahead/research_runtime -q
```

Run the fast repo smoke check:

```bash
python tools/verify.py --smoke
```

Check fixture size:

```bash
find tests/fixtures/runtime -type f -size +1M -print
```

The fixture size command should print nothing.

Run the YELLOW-lane canaries:

```bash
python tools/hooks/canary_runner.py
```

## Fail-Closed Suite

`tests/unit/runtime/fail_closed/` asserts that prohibited runtime shortcuts are
rejected, blocked, made inconclusive, or represented by terminal visible
records. The suite covers:

- Missing `AlphaSpec` or `StudySpec` references.
- Non-admissible `DatasetVersion` lifecycle states.
- Feature inputs missing `available_ts`.
- Label inputs missing `label_available_ts`.
- Label values exposed as live features.
- Same-bar optimistic signal-probe fills.
- Unbounded grids and `VariantBudget` overages.
- Locked-test use without contamination metadata and locked-test selection.
- Missing cost-stress / missing `double_cost` profile checks.
- Failed or inconclusive records that must carry visible rejection reasons.
- Prohibited MVP states that must not be reachable by runtime decision
  transitions.
- Raw/heavy/value-bearing artifact descriptors that must stay local-only.

## No-Lookahead Suite

`tests/no_lookahead/research_runtime/` exercises the runtime no-lookahead audit
over synthetic fixtures. RT-P20 adds fixture-backed checks for:

- `available_ts` on live feature inputs.
- `label_available_ts` on label inputs.
- Same-bar fill metadata.
- Locked-test contamination metadata.

These tests complement the existing no-lookahead tests and do not remove,
weaken, or mask earlier assertions.

## Interpretation

Passing these tests means the local runtime contracts refuse the specific
synthetic shortcut cases. It does not mean an alpha is valid, tradable,
profitable, production-ready, strategy-ready, or portfolio-ready. The runtime
remains a local deterministic research layer over accepted `DatasetVersion`
references and value-free metadata.
