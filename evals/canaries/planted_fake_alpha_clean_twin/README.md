# Canary fixture: planted fake-alpha clean twin

This is the clean twin of `evals/canaries/planted_fake_alpha/`: the bars and
label shape match the contaminated fixture, but each label references its own
bar, uses `lookahead_k = 0`, and declares no planted signal.

Expected behavior: the real `DIAGNOSTICS_RUN -> EVIDENCE_READY` gate stack
passes this fixture. It is synthetic canary metadata only and is not market
evidence.
