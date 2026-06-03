# Canary: optimistic fill

Injected fault: use an unrealistically favorable fill assumption so
execution-cost handling is known-bad.

Expected behavior: the guard rejects or flags the injected optimistic-fill
fault. A passing canary validates guard behavior only and does not imply alpha
validity.

Executable ARGOV-P14 fixture:

- `synthetic_fixture.json` - tiny synthetic execution-assumption fixture that
  attempts same-bar optimistic timing and target-first ordering. It runs no
  backtest, broker, paper, live, or order-routing operation.
