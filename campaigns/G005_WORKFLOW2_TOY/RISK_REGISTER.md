# G005 Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Toy workflow is mistaken for production automation | Could imply provider or merge readiness that does not exist | Campaign and run artifacts explicitly state local-only behavior |
| STOP handling corrupts completed artifacts | Could make resume or audit unreliable | Driver skips already passed phases and checks STOP only before starting pending phases |
| Run artifacts are incomplete | Could fail Workflow 2 validation | Driver writes required root and per-phase files deterministically |
| Scope expands into real orchestration | Could violate project constraints | Driver keeps unsupported campaigns on the scaffold path and does not implement provider, GitHub, merge, deployment, or trading operations |
