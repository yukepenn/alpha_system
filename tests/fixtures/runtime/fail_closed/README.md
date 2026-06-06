# Synthetic Runtime Fail-Closed Fixtures

This directory contains tiny, deterministic runtime fixtures for RT-P20
fail-closed tests. They are hand-written synthetic metadata and scalar values
only. They are not provider responses, market data, runtime values, alpha
evidence, or profitability/tradability evidence.

`invalid_shortcuts.json` groups deliberately invalid request, input, probe,
grid, cost, partition, decision-state, and artifact shapes used by the
fail-closed tests. Each item is meant to prove that the runtime blocks a
shortcut and emits a visible reason instead of silently producing a result.
