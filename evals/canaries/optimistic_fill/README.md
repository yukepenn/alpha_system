# Canary: optimistic fill

Injected fault: use an unrealistically favorable fill assumption so
execution-cost handling is known-bad.

Expected behavior: the guard rejects or flags the injected optimistic-fill
fault. A passing canary validates guard behavior only and does not imply alpha
validity.
