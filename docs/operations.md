# Operations

Document operational procedures, ownership, and recovery notes.

Red-lane operations require scoped authorization:

- `PROJECT_OP_AUTHORIZED`
- `PROJECT_OP_SCOPE`
- `PROJECT_OP_EXPIRES`

Run `python tools/frontier/op_gate.py --check` before any destructive, external, live, production, or broker-adjacent operation.
