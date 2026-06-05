# Historical / Superseded Docs

This directory preserves documents that are **no longer the source of truth** but
are kept for audit history. Nothing here should be treated as current guidance.

## Archived

| Archived file | Superseded by | Reason |
| --- | --- | --- |
| `architecture.md` | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) | Thin early stub (harness-spine sketch only). The uppercase `ARCHITECTURE.md` is the authoritative, complete architecture doc. The two also collided by case on case-insensitive filesystems. |
| `artifact_policy.md` | [`../ARTIFACT_POLICY.md`](../ARTIFACT_POLICY.md) + `frontier.yaml` | Thin early stub that itself deferred to `frontier.yaml`. The uppercase `ARTIFACT_POLICY.md` plus `frontier.yaml` are authoritative. Same case-collision concern. |

Archived during `PRE_FEATURE_REPO_CONSOLIDATION_V1`. Content is preserved
verbatim via `git mv` (full history retained); these files were duplicates, so
no information was lost.
