# Close-Out Identity-Drift Repair Note (coordinator, 2026-06-11)

Context: the FUTSUB-P22 registry-integration audit (BLOCKED, blocking finding
1) verified all 48 `session_close`/`maintenance_flat` dry-run preview
`label_version_id`s were absent from the registry while 48 different
(pre-LCFP, FUTSUB-P18-era) ids were registered — close-out was the only
family still on its pre-LCFP registration after LCFP changed the
label-contract surfaces.

Resolution (per the P22 review's routed repair):

1. **Full-window re-materialization 2026-06-11** under the current governed
   identity: `alpha scaleout label-pack --config
   configs/labels/scaleout/session_close_maintenance_flat.json --execute
   --rollout full-window --engine reference` → **48 completed / 0 skipped /
   0 failed** (refreshed `coverage_summary.md`). Preview == registry is
   restored for the current contract.
2. **48 stale rows deprecated via the sanctioned `deprecate_label` API**
   (no deletion, lineage preserved): each pre-LCFP row deprecated with
   reason + replacement pointer to its same-(label, partition,
   dataset_version) current-identity row; exact 48 old/new pairs verified
   before mutation; registry backup `labels.sqlite.bak.20260611T144500Z`
   (local-only).

Together with the merged N_eff/overlap evidence-contract clarification
(PR #360), this resolves both P22 blocking findings. The P22 re-run's
resolver smoke should now pass the full keystone chain. Value-free; no
alpha/profitability claim.
