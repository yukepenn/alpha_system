# Canary: random target

Injected fault: replace the study target with random noise so any
admissible-looking signal is known-bad.

Expected behavior: the guard rejects or flags the injected random-target fault.
A passing canary validates guard behavior only and does not imply alpha validity.
