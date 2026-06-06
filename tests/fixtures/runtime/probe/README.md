# Signal Probe Synthetic Fixtures

These fixtures are tiny synthetic rows for unit tests and documentation only.
They are not market data, not alpha evidence, and not runtime output artifacts.

Rows carry `event_ts`, `available_ts`, and `label_available_ts` so the probe can
prove next-bar fill behavior and label availability discipline without reading
provider files or materializing feature/label stores.
