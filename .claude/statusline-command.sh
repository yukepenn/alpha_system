#!/usr/bin/env bash
# alpha_system status line — no external deps (python, not jq).
# Format: ⛵ Model-effort | 5h N% 1wk N% | ~$N.NN est | branch | 🟢 WF2:<campaign> <state> <done>/<total> [<active phase>] | TASK:<coordinator note>
# Icons: ⛵ smooth sailing (no red anywhere) / ⚠️ attention; WF2: 🟢 running, ✅ completed, 🟡 stopped/paused, 🔴 blocked/failed.
# WF2 reads the newest runs/*/state.json; TASK reads runs/STATUSLINE_TASK.txt (local-only, coordinator-maintained).
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

cw = d.get("context_window") or {}
rem = cw.get("remaining_percentage")
if rem is not None:
    r = float(rem)
    ctx_icon = "\U0001F7E2" if r > 35 else ("\U0001F7E1" if r > 15 else "\U0001F534")
    seg += " | ctx %s%.0f%% left" % (ctx_icon, r)

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

healthy = True

# --- WF2 live status from newest runs/*/state.json ---
try:
    states = glob.glob(os.path.join(wd, "runs", "*", "state.json"))
    if states:
        newest = max(states, key=os.path.getmtime)
        s = json.load(open(newest))
        phases = s.get("phases") or []
        total = len(phases)
        run_status = str(s.get("status", "?"))
        pass_ct = sum(1 for p in phases if p.get("status") in ("PASS", "PASS_WITH_WARNINGS"))
        if run_status in ("COMPLETED", "COMPLETE"):
            done = pass_ct                       # terminal run: every passing phase is done (merged-flag may lag)
        else:
            merged_ct = sum(1 for p in phases if p.get("status") in ("PASS", "PASS_WITH_WARNINGS") and p.get("merged"))
            done = merged_ct or pass_ct          # live run: prefer truly-merged; fall back to passing
        active = next((p for p in phases if p.get("status") not in
                       ("PASS", "PASS_WITH_WARNINGS", "PENDING", "SKIPPED")), None)
        pid0 = (phases[0].get("phase_id") or "") if phases else ""
        tag = pid0.split("-")[0] if "-" in pid0 else (s.get("campaign_id") or "?")[:10]
        astat = str(active.get("status")) if active else ""
        if "BLOCKED" in run_status or "FAIL" in run_status or "BLOCKED" in astat or "FAIL" in astat:
            icon = "\U0001F534"; healthy = False          # red
        elif run_status == "RUNNING":
            icon = "\U0001F7E2"                           # green
        elif run_status in ("COMPLETED", "COMPLETE"):
            icon = "✅"                               # check
        else:
            icon = "\U0001F7E1"                           # yellow
        wf2 = "%s WF2:%s %s %d/%d" % (icon, tag, run_status, done, total)
        if active:
            wf2 += " [%s %s]" % (active.get("phase_id", "?"), astat)
        seg += " | " + wf2
except Exception:
    pass

# --- coordinator task note (local-only file; may start with its own status emoji) ---
try:
    tf = os.path.join(wd, "runs", "STATUSLINE_TASK.txt")
    if os.path.isfile(tf):
        note = open(tf).read().strip()
        if note:
            if "\U0001F534" in note or "⚠" in note:
                healthy = False
            seg += " | TASK:" + note[:90]
except Exception:
    pass

prefix = "⛵ " if healthy else "⚠️ "
print(prefix + seg)
'
