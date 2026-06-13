# Forbidden EXPLORATORY Promotion Canary

This canary asserts that the trusted promotion path refuses an artifact carrying
`stamp: EXPLORATORY`.

It passes only when `alpha_system.governance.promotion` raises the dedicated
`exploratory_artifact_refused` validation issue. If the guard is bypassed or
removed, the canary exits non-zero.

The fixture is value-free and does not exercise paper trading, live trading,
broker operations, order routing, deployment, or promotion.
