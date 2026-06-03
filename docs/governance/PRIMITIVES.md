# Governance Primitives

`ARGOV-P02` adds shared primitives for governance IDs, canonical serialization,
content hashing, and fail-closed validation. These primitives are governance-only
infrastructure. They do not define object schemas, persistence, registry behavior,
CLI behavior, gates, reports, market data ingestion, alpha search, broker behavior,
paper trading, live trading, order routing, deployment, or market claims.

## IDs

Governance IDs use the form:

```text
<prefix>_<24-lowercase-hex-token>
```

The valid prefixes are fixed by `docs/governance/NAMING.md`: `hyp`, `aspec`,
`freq`, `lspec`, `sspec`, `trial`, `evb`, `rej`, `prom`, `rver`, `nctrl`, and
`abook`.

`generate_governance_id(kind, components)` is deterministic. The same canonical
object kind and the same logical component mapping produce the same ID. The
deterministic path uses no wall-clock time, random entropy, or filesystem state.
`parse_governance_id(...)` and `validate_governance_id(...)` reject malformed IDs,
unknown prefixes, and wrong expected kinds or prefixes with `GovernanceIdError`.

## Serialization And Hashing

`canonical_serialize(...)` serializes strict JSON-compatible governance values
with sorted keys, compact separators, ASCII output, and finite JSON numbers only.
`deserialize(...)` rejects malformed JSON and duplicate object keys. Values that
cannot round-trip faithfully as JSON, such as sets or non-string mapping keys, are
rejected rather than converted.

`content_hash(...)` hashes the canonical serialized form with SHA-256. Reordering
mapping fields does not change the hash. Changing logical content does change the
hash.

## Validation

Validation fails closed by default. The helpers in
`alpha_system.governance.validation` raise `GovernanceValidationError` with
structured `ValidationIssue` entries for missing required fields, null required
fields, invalid declared types, non-mapping roots, and undeclared fields when an
allowed-field set is provided.

Valid mappings are returned unchanged. The primitives do not coerce strings to
numbers, accept `bool` as `int`, add implicit defaults, or drop unknown fields.
