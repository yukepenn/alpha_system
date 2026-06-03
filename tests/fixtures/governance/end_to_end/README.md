# ARGOV-P18 Synthetic End-to-End Fixture

`synthetic_lifecycle_fixture.json` contains tiny deterministic governance metadata
used by the ARGOV-P18 integration dry run. It is not market data, does not contain
factor values or labels, and is not evidence for any research result.

The test builds deterministic governance IDs from this metadata at runtime, writes
temporary JSON command inputs under pytest's temporary directory, and persists
objects only to a temporary SQLite registry.
