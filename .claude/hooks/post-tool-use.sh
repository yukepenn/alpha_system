#!/usr/bin/env sh
set -eu

if [ -x "tools/hooks/artifact_guard.py" ]; then
  python tools/hooks/artifact_guard.py --claude-post-tool-use
fi
