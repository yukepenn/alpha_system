# Canary: permuted labels

Injected fault: permute labels away from their original examples so label
alignment is known-bad.

Expected behavior: the guard rejects or flags the injected permuted-label fault.
A passing canary validates guard behavior only and does not imply alpha validity.

Executable ARGOV-P14 fixture:

- `synthetic_fixture.json` - tiny synthetic label-integrity fixture that requests
  a forbidden label reference as a feature. It contains no materialized labels,
  real data, factor values, or research evidence.
