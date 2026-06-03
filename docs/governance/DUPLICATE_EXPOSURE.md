# Duplicate-Exposure Guard

`ARGOV-P05` adds a read-only guard for likely duplicate or equivalent feature
exposures requested by `FeatureRequest`.

The guard compares requested input and formula metadata against an injected view
of the existing factor registry. It returns structured findings and can populate
the request's `duplicate_or_equivalent_exposure_notes`. It does not compute
factor values, materialize data, register factors, record validation runs,
promote factors, or make trading decisions.

## Read-Only Registry Contract

The guard accepts a dependency-injected registry reader:

- an iterable of registry-entry mappings;
- a callable that returns registry-entry mappings;
- an object with `read_factor_versions()`;
- a registry path, opened with the existing registry connection helper in
  read-only mode.

The guard does not call `register_factor_spec`, validation recording, promotion
recording, or any mutating registry API. Tests use a read-only spy that fails if
any mutating method is called.

If the registry is empty, the guard returns no findings with `registry_status:
EMPTY`. If the registry is unavailable or the injected reader fails, the guard
does not crash; it returns no duplicate findings with `registry_status:
UNAVAILABLE` and guard notes that do not claim the request is clean.

## Findings

Each finding contains:

- `kind`: `DUPLICATE` or `EQUIVALENT`;
- `severity`: `BLOCKING` or `WARNING`;
- `matched_registry_reference`;
- `rationale`.

`DUPLICATE` findings are `BLOCKING` when the request matches an existing factor
identity or exposure family. `EQUIVALENT` findings are `WARNING` when metadata
suggests the requested formula is materially equivalent to an existing exposure,
for example by using an equivalent operation, input, and lookback window under a
different name.

The result is metadata for later governance gates. This phase does not implement
the `REGISTERED -> IMPLEMENTATION_ALLOWED` promotion gate.

## Limitations

The guard is conservative metadata matching. It can identify obvious duplicate
or equivalent exposure descriptions, but it does not prove mathematical identity
and does not evaluate data. Ambiguous warnings require later human or reviewer
attention before any implementation permission is considered.
