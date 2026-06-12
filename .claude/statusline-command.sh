#!/usr/bin/env bash
# alpha_system status line — no external deps (python, not jq).
# Format: Model-effort | 5h N% 1wk N% | ~$N.NN est | branch | WF2:<campaign> <state> <merged>/<total> [<active phase>] | TASK:<coordinator note>
# WF2 segment reads the newest runs/*/state.json; TASK reads runs/STATUSLINE_TASK.txt (local-only, coordinator-maintained).
input=$(cat)
printf '%s' "$input" | python3 -c '
import sys, json, subprocess, re, glob, os

try:
    d = json.load(sys.stdin)
except Exception:
    print("Claude")
    sys.exit(0)

model = (d.get("model") or {}).get("display_name") or "unknown"
model = re.sub(r"\s*\([^)]*\)", "", model)
model = "-".join(model.split())
effort = (d.get("effort") or {}).get("level")
cost = (d.get("cost") or {}).get("total_cost_usd")
rl = d.get("rate_limits") or {}
fh_used = (rl.get("five_hour") or {}).get("used_percentage")
wk_used = (rl.get("seven_day") or {}).get("used_percentage")
wd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or "."

seg = model + ("-" + str(effort) if effort else "")

parts = []
if fh_used is not None:
    parts.append("5h %.0f%%" % (100.0 - float(fh_used)))
if wk_used is not None:
    parts.append("1wk %.0f%%" % (100.0 - float(wk_used)))
if parts:
    seg += " | " + " ".join(parts)

try:
    if cost is not None and float(cost) > 0:
        seg += " | ~$%.2f est" % float(cost)
except (TypeError, ValueError):
    pass

try:
    b = subprocess.run(["git", "-C", wd, "--no-optional-locks", "symbolic-ref", "--short", "HEAD"],
                       capture_output=True, text=True, timeout=2).stdout.strip()
    if b:
        seg += " | " + b
except Exception:
    pass

# --- WF2 live status from newest runs/*/state.json ---
try:
    repo = wd
    states = glob.glob(os.path.join(repo, "runs", "*", "state.json"))
    if states:
        newest = max(states, key=os.path.getmtime)
        s = json.load(open(newest))
        phases = s.get("phases") or []
        total = len(phases)
        done = sum(1 for p in phases if p.get("status") in ("PASS", "PASS_WITH_WARNINGS") and p.get("merged"))
        if done == 0:
            done = sum(1 for p in phases if p.get("status") in ("PASS", "PASS_WITH_WARNINGS"))
        active = next((p for p in phases if p.get("status") not in
                       ("PASS", "PASS_WITH_WARNINGS", "PENDING", "SKIPPED")), None)
        pid0 = (phases[0].get("phase_id") or "") if phases else ""
        tag = pid0.split("-")[0] if "-" in pid0 else (s.get("campaign_id") or "?")[:10]
        wf2 = "WF2:%s %s %d/%d" % (tag, s.get("status", "?"), done, total)
        if active:
            wf2 += " [%s %s]" % (active.get("phase_id", "?"), active.get("status", "?"))
        seg += " | " + wf2
except Exception:
    pass

# --- coordinator task note (local-only file, never committed) ---
try:
    tf = os.path.join(wd, "runs", "STATUSLINE_TASK.txt")
    if os.path.isfile(tf):
        note = open(tf).read().strip()
        if note:
            seg += " | TASK:" + note[:80]
except Exception:
    pass

print(seg)
'
