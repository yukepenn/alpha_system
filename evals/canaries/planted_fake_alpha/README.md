# Canary: planted fake alpha

Injected fault: a tiny synthetic study labels each bar `t` using information
from future bar `t+1`.

Expected behavior: the evidence bundle itself validates, then the real
`DIAGNOSTICS_RUN -> EVIDENCE_READY` promotion-gate path rejects the study via
`locked_test_contamination_blocks_evidence_ready`. The canary asserts the
REJECTED outcome only; it records no score, alpha, profitability, or
tradability value.
