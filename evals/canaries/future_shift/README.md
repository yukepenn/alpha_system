# Canary: future shift

Injected fault: shift future information into the feature or label path so
lookahead is known-bad.

Expected behavior: the guard rejects or flags the injected future-shift fault.
A passing canary validates guard behavior only and does not imply alpha validity.

Executable ARGOV-P14 fixture:

- `synthetic_fixture.json` - tiny synthetic metadata fixture that places a
  feature `information_time` at the label availability timestamp. It contains no
  real data, factor values, or label values.
