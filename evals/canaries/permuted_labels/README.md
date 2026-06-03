# Canary: permuted labels

Injected fault: permute labels away from their original examples so label
alignment is known-bad.

Expected behavior: the guard rejects or flags the injected permuted-label fault.
A passing canary validates guard behavior only and does not imply alpha validity.
